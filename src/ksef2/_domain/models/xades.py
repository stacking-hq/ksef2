"""Loaded certificate and private key for XAdES authentication."""

from typing import Literal, Self, override

from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    pkcs12,
)
from cryptography.x509 import Certificate

import ksef2._errors as exceptions

_DataEncoding = Literal["pem", "der"]

# The parsing failures ``cryptography`` raises for unreadable material, a wrong
# password, or a key type its loader refuses. A broad ``Exception`` is not caught:
# anything else is a programming error and must surface unchanged.
_READ_FAILURES = (ValueError, TypeError, UnsupportedAlgorithm)

_CERTIFICATE_HINT = (
    "Pass certificate bytes in the encoding named in the message, for example the "
    "contents of the .pem or .crt file you downloaded from the certificate authority."
)
_PRIVATE_KEY_HINT = (
    "Pass private-key bytes in the encoding named in the message, with the password "
    "that encrypts them; an unencrypted key must be passed without a password."
)
_PKCS12_HINT = (
    "Pass the whole .p12 or .pfx file as bytes, with the password it was created with "
    "when it has one."
)


def _certificate(data: bytes, *, encoding: _DataEncoding) -> Certificate:
    """Return the X.509 certificate held in *data*, or raise a safe argument error."""
    loader = (
        x509.load_der_x509_certificate
        if encoding == "der"
        else x509.load_pem_x509_certificate
    )
    try:
        return loader(data)
    except _READ_FAILURES as exc:
        raise exceptions.KSeFArgumentError(
            f"The XAdES certificate could not be read as {encoding.upper()} data.",
            hint=_CERTIFICATE_HINT,
            certificate_encoding=encoding,
        ) from exc


def _private_key(
    data: bytes, *, encoding: _DataEncoding, password: bytes | None
) -> PrivateKeyTypes:
    """Return the private key held in *data*, or raise a safe argument error."""
    loader = (
        serialization.load_der_private_key
        if encoding == "der"
        else serialization.load_pem_private_key
    )
    try:
        return loader(data, password=password)
    except _READ_FAILURES as exc:
        raise exceptions.KSeFArgumentError(
            f"The XAdES private key could not be read as {encoding.upper()} data "
            "with the supplied password.",
            hint=_PRIVATE_KEY_HINT,
            private_key_encoding=encoding,
        ) from exc


def _usable_pair(
    certificate: Certificate, private_key: PrivateKeyTypes
) -> tuple[Certificate, RSAPrivateKey | EllipticCurvePrivateKey]:
    """Return *certificate* and *private_key* once the key can sign and matches it.

    The public parts are compared as SubjectPublicKeyInfo DER, so a key that merely
    has the same parameters as the certificate is still rejected.
    """
    if not isinstance(private_key, (RSAPrivateKey, EllipticCurvePrivateKey)):
        raise exceptions.KSeFArgumentError(
            f"The XAdES private key must be RSA or EC, got {type(private_key).__name__}.",
            hint="Use an RSA or EC private key; KSeF does not accept other key types "
            "for XAdES authentication.",
            key_type=type(private_key).__name__,
        )
    signed_with = private_key.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo
    )
    issued_with = certificate.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo
    )
    if signed_with != issued_with:
        raise exceptions.KSeFArgumentError(
            "The XAdES certificate does not belong to the supplied private key.",
            hint="Pass the certificate issued for that key; check both files came "
            "from the same request.",
        )
    return certificate, private_key


class XAdESCredentials:
    """Loaded certificate and private key for ``with_xades()``.

    Use :meth:`from_pem`, :meth:`from_der` or :meth:`from_pkcs12` to load bytes,
    or construct the holder from loaded cryptography objects. Construction checks
    that the key is RSA or EC and belongs to the certificate, once. Authentication
    reuses those objects without serializing or parsing the private key again.

    The holder retains no password or input bytes. Its repr hides both objects.
    It has no model schema or JSON serialization API. Treat it as a secret while
    it holds the decrypted private key in memory.

    Args:
        certificate: Loaded X.509 signing certificate.
        private_key: Loaded RSA or EC private key belonging to the certificate.

    Raises:
        KSeFArgumentError: If the key is not RSA or EC or does not match.
    """

    __slots__ = ("_certificate", "_private_key")

    def __init__(self, certificate: Certificate, private_key: PrivateKeyTypes) -> None:
        self._certificate, self._private_key = _usable_pair(certificate, private_key)

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}(<redacted>)"

    @property
    def certificate(self) -> Certificate:
        """Return the loaded signing certificate.

        Returns:
            The certificate accepted at construction.
        """
        return self._certificate

    @property
    def private_key(self) -> RSAPrivateKey | EllipticCurvePrivateKey:
        """Return the loaded signing key. Keep this secret and out of logs.

        Returns:
            The private key accepted at construction.
        """
        return self._private_key

    @classmethod
    def from_pem(
        cls,
        cert_pem: bytes,
        key_pem: bytes,
        key_password: bytes | None = None,
    ) -> Self:
        """Build credentials from a PEM certificate and a PEM private key.

        Args:
            cert_pem: Certificate bytes in PEM encoding.
            key_pem: Private-key bytes in PEM encoding, encrypted or not.
            key_password: Password that decrypts ``key_pem``, or ``None`` when the key
                is unencrypted. Supplying one for an unencrypted key, or withholding
                it from an encrypted key, is rejected instead of ignored.

        Returns:
            Credentials holding the loaded certificate and private key.

        Raises:
            KSeFArgumentError: If either input cannot be read, the key is not RSA or
                EC, or the key does not belong to the certificate.

        Example:
            ```python
            credentials = XAdESCredentials.from_pem(
                Path("company.pem").read_bytes(),
                Path("company.key").read_bytes(),
                key_password=b"secret",
            )
            ```
        """
        return cls(
            _certificate(cert_pem, encoding="pem"),
            _private_key(key_pem, encoding="pem", password=key_password),
        )

    @classmethod
    def from_der(
        cls,
        cert_der: bytes,
        key_der: bytes,
        key_password: bytes | None = None,
    ) -> Self:
        """Build credentials from a DER certificate and a DER private key.

        Args:
            cert_der: Certificate bytes in DER encoding.
            key_der: Private-key bytes in DER encoding, encrypted or not.
            key_password: Password that decrypts ``key_der``, or ``None`` when the key
                is unencrypted. Supplying one for an unencrypted key, or withholding
                it from an encrypted key, is rejected instead of ignored.

        Returns:
            Credentials holding the loaded certificate and private key.

        Raises:
            KSeFArgumentError: If either input cannot be read, the key is not RSA or
                EC, or the key does not belong to the certificate.

        Example:
            ```python
            credentials = XAdESCredentials.from_der(
                Path("company.cer").read_bytes(),
                Path("company.der").read_bytes(),
            )
            ```
        """
        return cls(
            _certificate(cert_der, encoding="der"),
            _private_key(key_der, encoding="der", password=key_password),
        )

    @classmethod
    def from_pkcs12(cls, p12_bytes: bytes, password: bytes | None = None) -> Self:
        """Build credentials from a PKCS#12 archive holding a certificate and a key.

        Args:
            p12_bytes: The whole ``.p12`` or ``.pfx`` file.
            password: Password of the archive, or ``None`` when it has none. The
                password decrypts the archive only: it is not kept afterwards.

        Returns:
            Credentials holding the loaded certificate and private key.

        Raises:
            KSeFArgumentError: If the archive cannot be read, holds no certificate or
                no private key, or the key is not RSA or EC.

        Example:
            ```python
            credentials = XAdESCredentials.from_pkcs12(
                Path("company.p12").read_bytes(),
                password=b"secret",
            )
            ```
        """
        try:
            private_key, certificate, _extra_certificates = (
                pkcs12.load_key_and_certificates(p12_bytes, password)
            )
        except _READ_FAILURES as exc:
            raise exceptions.KSeFArgumentError(
                "The XAdES PKCS#12 archive could not be read with the supplied password.",
                hint=_PKCS12_HINT,
            ) from exc
        if private_key is None:
            raise exceptions.KSeFArgumentError(
                "The XAdES PKCS#12 archive holds no private key.",
                hint=_PKCS12_HINT,
            )
        if certificate is None:
            raise exceptions.KSeFArgumentError(
                "The XAdES PKCS#12 archive holds no certificate.",
                hint=_PKCS12_HINT,
            )
        return cls(certificate, private_key)
