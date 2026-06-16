"""Helpers for loading certificates and creating XAdES authentication payloads."""

from __future__ import annotations

import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509 import Certificate
from cryptography.x509.oid import NameOID, ObjectIdentifier
from lxml import etree
from signxml.algorithms import (
    DigestAlgorithm,
    SignatureConstructionMethod,
    SignatureMethod,
)
from signxml.xades.xades import XAdESSigner

from ksef2.core.xml import parse_xml_bytes

# OID 2.5.4.97 = organizationIdentifier (used in company-seal certificates)
_OID_ORGANIZATION_IDENTIFIER = ObjectIdentifier("2.5.4.97")
# OID 2.5.4.5 = serialNumber (used for PESEL in personal certificates)
_OID_SERIAL_NUMBER = ObjectIdentifier("2.5.4.5")

_AUTH_TOKEN_NS = "http://ksef.mf.gov.pl/auth/token/2.0"

XAdESPrivateKey = RSAPrivateKey | EllipticCurvePrivateKey


def load_certificate_from_pem(source: bytes | str | Path) -> Certificate:
    """Load an X.509 certificate from PEM data or a PEM file path.

    Args:
        source: PEM-encoded bytes, or a path (``str`` / ``Path``) to a ``.pem`` / ``.crt`` file.

    Returns:
        A :class:`~cryptography.x509.Certificate` ready to pass to
        :meth:`~ksef2.clients.auth.AuthClient.with_xades`.

    Example — certificate obtained from MCU (DEMO / PRODUCTION)::

        from ksef2.core.xades import load_certificate_from_pem, load_private_key_from_pem
        from ksef2 import Client, Environment

        cert = load_certificate_from_pem("cert.pem")
        key  = load_private_key_from_pem("key.pem")

        auth = Client(Environment.DEMO).authentication.with_xades(
            nip="1234567890", cert=cert, private_key=key
        )
    """
    data = Path(source).read_bytes() if not isinstance(source, bytes) else source
    return x509.load_pem_x509_certificate(data)


def load_private_key_from_pem(
    source: bytes | str | Path,
    *,
    password: bytes | None = None,
) -> XAdESPrivateKey:
    """Load an RSA or EC private key from PEM data or a PEM file path.

    Args:
        source: PEM-encoded bytes, or a path (``str`` / ``Path``) to a ``.pem`` / ``.key`` file.
        password: Decryption password if the key is encrypted, otherwise ``None``.

    Returns:
        An :class:`~cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey` or
        :class:`~cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePrivateKey`.

    Raises:
        TypeError: If the decoded key is not an RSA or EC private key.
    """
    data = Path(source).read_bytes() if not isinstance(source, bytes) else source
    key = serialization.load_pem_private_key(data, password=password)
    if not isinstance(key, (RSAPrivateKey, EllipticCurvePrivateKey)):
        raise TypeError(f"Expected RSA or EC private key, got {type(key).__name__}")
    return key


def load_certificate_and_key_from_p12(
    source: bytes | str | Path,
    *,
    password: bytes | None = None,
) -> tuple[Certificate, XAdESPrivateKey]:
    """Load a certificate and RSA or EC private key from a PKCS#12 (.p12 / .pfx) file.

    Args:
        source: Raw PKCS#12 bytes, or a path (``str`` / ``Path``) to the ``.p12`` / ``.pfx`` file.
        password: Decryption password for the archive, or ``None`` if unencrypted.

    Returns:
        A ``(cert, private_key)`` tuple ready to pass to
        :meth:`~ksef2.clients.auth.AuthClient.with_xades`.

    Note:
        If you have separate ``.pem`` and ``.key`` files downloaded directly from MCU, prefer
        :func:`load_certificate_from_pem` + :func:`load_private_key_from_pem` — no conversion needed.

    Raises:
        ValueError: If the archive does not contain a certificate.
        TypeError: If the decoded key is not an RSA or EC private key.
    """
    data = Path(source).read_bytes() if not isinstance(source, bytes) else source
    private_key, cert, _ = pkcs12.load_key_and_certificates(data, password)
    if cert is None:
        raise ValueError("No certificate found in PKCS#12 archive")
    if not isinstance(private_key, (RSAPrivateKey, EllipticCurvePrivateKey)):
        raise TypeError(
            f"Expected RSA or EC private key, got {type(private_key).__name__}"
        )
    return cert, private_key


def generate_test_certificate(nip: str) -> tuple[Certificate, RSAPrivateKey]:
    """Generate a self-signed RSA-2048 certificate for XAdES auth on the TEST environment.

    The DN uses the company-seal format matching the Java/C# reference implementations:
    ``2.5.4.97=VATPL-{NIP}, CN=KSeF SDK Test, C=PL``
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "KSeF SDK Test"),
            x509.NameAttribute(_OID_ORGANIZATION_IDENTIFIER, f"VATPL-{nip}"),
            x509.NameAttribute(NameOID.COMMON_NAME, "KSeF SDK Test"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
        ]
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(hours=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    return cert, private_key


def generate_personal_test_certificate(
    pesel: str,
    nip: str | None = None,
) -> tuple[Certificate, RSAPrivateKey]:
    """Generate a self-signed RSA-2048 certificate for a person (XAdES auth).

    The DN uses the personal certificate format:
    ``2.5.4.5=TINPL-{PESEL}, CN=KSeF SDK Test, C=PL``

    Optionally includes NIP for company representatives:
    ``2.5.4.97=VATPL-{NIP}``
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    attributes = [
        x509.NameAttribute(_OID_SERIAL_NUMBER, f"TINPL-{pesel}"),
        x509.NameAttribute(NameOID.COMMON_NAME, "KSeF SDK Test"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
    ]

    if nip:
        attributes.insert(
            0, x509.NameAttribute(_OID_ORGANIZATION_IDENTIFIER, f"VATPL-{nip}")
        )

    subject = issuer = x509.Name(attributes)

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(hours=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    return cert, private_key


def build_auth_token_request_xml(
    challenge: str,
    nip: str,
    subject_identifier_type: str = "certificateSubject",
) -> bytes:
    """Build the XML payload that is signed for XAdES authentication.

    Args:
        challenge: Challenge value returned by KSeF.
        nip: Taxpayer NIP used in the authentication context.
        subject_identifier_type: Subject identifier type written to the XML.

    Returns:
        UTF-8 XML bytes matching the KSeF auth-token schema.
    """
    nsmap: dict[str | None, str] = {None: _AUTH_TOKEN_NS}
    root = etree.Element(f"{{{_AUTH_TOKEN_NS}}}AuthTokenRequest", nsmap=nsmap)  # pyright: ignore[reportArgumentType]

    etree.SubElement(root, f"{{{_AUTH_TOKEN_NS}}}Challenge").text = challenge

    ctx = etree.SubElement(root, f"{{{_AUTH_TOKEN_NS}}}ContextIdentifier")
    etree.SubElement(ctx, f"{{{_AUTH_TOKEN_NS}}}Nip").text = nip

    etree.SubElement(
        root, f"{{{_AUTH_TOKEN_NS}}}SubjectIdentifierType"
    ).text = subject_identifier_type

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def sign_xades(
    xml_bytes: bytes,
    cert: Certificate,
    private_key: XAdESPrivateKey,
) -> bytes:
    """Sign XML with an enveloped XAdES-B signature.

    Args:
        xml_bytes: XML document to sign.
        cert: Certificate that should be embedded in the signature.
        private_key: RSA or EC private key used for signing.

    Returns:
        UTF-8 XML bytes containing the enveloped XAdES signature.
    """
    if isinstance(private_key, EllipticCurvePrivateKey):
        sig_alg = SignatureMethod.ECDSA_SHA256
    else:
        sig_alg = SignatureMethod.RSA_SHA256
    signer = XAdESSigner(
        method=SignatureConstructionMethod.enveloped,
        signature_algorithm=sig_alg,
        digest_algorithm=DigestAlgorithm.SHA256,
    )
    root = parse_xml_bytes(xml_bytes)

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )

    signed_root = signer.sign(data=root, key=key_pem, cert=cert_pem)  # pyright: ignore[reportCallIssue]
    return etree.tostring(signed_root, xml_declaration=True, encoding="UTF-8")


class LocalSigner:
    """A :class:`~ksef2.domain.interfaces.Signer` that signs XML locally."""

    def __init__(self, cert: Certificate, private_key: XAdESPrivateKey) -> None:
        self._cert = cert
        self._private_key = private_key

    def sign(self, xml_bytes: bytes) -> bytes:
        """Sign XML bytes with the certificate and key held by this signer."""
        return sign_xades(xml_bytes, self._cert, self._private_key)
