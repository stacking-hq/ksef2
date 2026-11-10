"""Records for persisting XAdES signing certificates and their private keys."""

import hashlib
from typing import (
    Annotated,
    NoReturn,
    Self,
    SupportsIndex,
    override,
)

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.x509 import Certificate
from pydantic import AwareDatetime, ConfigDict, Field, model_validator

from ksef2._errors import KSeFArgumentError
from ksef2._config import Environment
from ksef2._domain.models.base import KSeFBaseModel, validation_errors
from ksef2._domain.models.certificates import (
    CertificateSerialNumber,
    CertificateTypeValue,
)
from ksef2._domain.models.xades import XAdESCredentials

type SigningCertificateFingerprint = Annotated[str, Field(pattern="^[0-9a-f]{64}$")]


def _certificate_fingerprint(certificate: Certificate) -> str:
    """Return the SHA-256 of *certificate* in its DER encoding."""
    return hashlib.sha256(certificate.public_bytes(Encoding.DER)).hexdigest()


def _public_key_fingerprint(certificate: Certificate) -> str:
    """Return the SHA-256 of the SubjectPublicKeyInfo DER of *certificate*'s key."""
    return hashlib.sha256(
        certificate.public_key().public_bytes(
            Encoding.DER, PublicFormat.SubjectPublicKeyInfo
        )
    ).hexdigest()


def _needs_credentials_error() -> Exception:
    """Return the error for a value that is not a credentials holder.

    Returns:
        The exception for the caller to raise.
    """
    return KSeFArgumentError(
        "SigningCertificate needs an XAdESCredentials holder.",
        hint="Load the pair with XAdESCredentials.from_pem(), from_der() "
        "or from_pkcs12().",
    )


class SigningCertificateRef(KSeFBaseModel):
    """Identity of one stored signing certificate: environment and certificate fingerprint.

    The two parts are what a store keys its records by. The NIP is not part of the
    identity; the store instance supplies any application or tenant namespace, so the
    same certificate stored by two applications stays two independent records.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    environment: Environment
    """KSeF environment the certificate is used in."""
    fingerprint_sha256: SigningCertificateFingerprint
    """SHA-256 of the certificate's DER encoding, as 64 lowercase hex characters."""

    @classmethod
    def for_certificate(
        cls, certificate: Certificate, *, environment: Environment
    ) -> Self:
        """Return the reference of ``certificate`` in ``environment``.

        Args:
            certificate: Loaded X.509 signing certificate to fingerprint.
            environment: KSeF environment the certificate will be used in.

        Returns:
            The reference naming that certificate and environment.
        """
        return cls(
            environment=environment,
            fingerprint_sha256=_certificate_fingerprint(certificate),
        )


class SigningCertificateInfo(KSeFBaseModel):
    """Metadata of one stored signing certificate; holds no key material.

    Safe to log and to serialize. It records whatever validity the certificate itself
    carries, including an expired one, and says nothing about whether KSeF still
    considers the certificate active or unrevoked.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    reference: SigningCertificateRef
    """Environment and fingerprint this record is stored under."""
    x509_serial_number: int = Field(ge=0)
    """Serial number from the X.509 certificate. It is not the KSeF serial number."""
    public_key_sha256: SigningCertificateFingerprint
    """SHA-256 of the public key's SubjectPublicKeyInfo DER encoding, as 64 lowercase hex characters."""
    certificate_type: CertificateTypeValue | None = None
    """KSeF certificate purpose, ``authentication`` or ``offline``; ``None`` for external or generated TEST certificates."""
    ksef_serial_number: CertificateSerialNumber | None = None
    """Serial number KSeF assigned when issuing the certificate; ``None`` when unknown."""
    valid_from: AwareDatetime
    """Start of the certificate's validity period, in UTC."""
    valid_to: AwareDatetime
    """End of the certificate's validity period, in UTC."""

    @model_validator(mode="after")
    def _valid_to_after_valid_from(self) -> Self:
        if self.valid_to < self.valid_from:
            raise ValueError("valid_to is before valid_from")
        return self


def derive_signing_certificate_info(
    certificate: Certificate,
    *,
    environment: Environment,
    certificate_type: CertificateTypeValue | None = None,
    ksef_serial_number: str | None = None,
) -> SigningCertificateInfo:
    """Return the metadata a store records for ``certificate``, without its private key.

    Every field comes from the certificate itself or from the two optional
    annotations a store keeps alongside it, so a record read back from a backend
    cannot disagree with the certificate it was stored next to. An expired
    certificate, or one that is not valid yet, is described as it stands.

    This is an internal helper for store adapters inside the SDK. It is not part of
    ``ksef2.certificate_stores`` or ``ksef2.models``.

    Args:
        certificate: Loaded X.509 signing certificate to describe.
        environment: KSeF environment the certificate is used in.
        certificate_type: KSeF certificate purpose, ``None`` when unknown.
        ksef_serial_number: Serial number KSeF assigned when issuing the certificate,
            ``None`` when unknown.

    Returns:
        The metadata for that certificate and environment.

    Raises:
        KSeFValidationError: If ``certificate_type`` or ``ksef_serial_number`` is invalid.
    """
    with validation_errors("signing_certificate"):
        return SigningCertificateInfo.model_validate(
            {
                "reference": SigningCertificateRef.for_certificate(
                    certificate, environment=environment
                ),
                "x509_serial_number": certificate.serial_number,
                "public_key_sha256": _public_key_fingerprint(certificate),
                "certificate_type": certificate_type,
                "ksef_serial_number": ksef_serial_number,
                "valid_from": certificate.not_valid_before_utc,
                "valid_to": certificate.not_valid_after_utc,
            }
        )


class SigningCertificate:
    """A validated signing certificate and private key together with its store metadata.

    Build one from an :class:`XAdESCredentials` holder and the environment the pair
    signs in. Construction fingerprints the certificate once and derives the metadata
    from it, so the record a store saves cannot disagree with its own certificate.
    A certificate that has expired, or is not valid yet, is accepted: whether to keep
    using it is the application's decision.

    The instance is a secret while it is in memory. It hides the credentials in
    ``repr()``, refuses to be pickled or copied, and has no ``model_dump`` or JSON
    serialization API. Persist it only through a signing certificate store's
    ``save()``, which returns the metadata that is safe to serialize.

    Args:
        credentials: Loaded certificate and matching private key.
        environment: KSeF environment the pair signs in.
        certificate_type: KSeF certificate purpose, ``None`` when unknown.
        ksef_serial_number: Serial number KSeF assigned when issuing the certificate,
            ``None`` when unknown.

    Raises:
        KSeFArgumentError: If ``credentials`` is not an ``XAdESCredentials`` holder.
        KSeFValidationError: If ``certificate_type`` or ``ksef_serial_number`` is invalid.
    """

    __slots__ = ("_info", "_credentials")

    def __init__(
        self,
        credentials: XAdESCredentials,
        *,
        environment: Environment,
        certificate_type: CertificateTypeValue | None = None,
        ksef_serial_number: str | None = None,
    ) -> None:
        # The guard is for callers that run without runtime type checking; the
        # annotation above is what type checkers see.
        if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            credentials, XAdESCredentials
        ):
            raise _needs_credentials_error()  # pyright: ignore[reportUnreachable]
        self._credentials = credentials
        self._info = derive_signing_certificate_info(
            credentials.certificate,
            environment=environment,
            certificate_type=certificate_type,
            ksef_serial_number=ksef_serial_number,
        )

    @property
    def info(self) -> SigningCertificateInfo:
        """Return the metadata derived from the certificate.

        Returns:
            The record's metadata, free of key material.
        """
        return self._info

    @property
    def credentials(self) -> XAdESCredentials:
        """Return the loaded certificate and private key. Keep this secret.

        Returns:
            The credentials holder accepted at construction.
        """
        return self._credentials

    @property
    def reference(self) -> SigningCertificateRef:
        """Return the reference this record is stored under.

        Returns:
            Shortcut for ``info.reference``.
        """
        return self._info.reference

    @override
    def __repr__(self) -> str:
        return (
            f"SigningCertificate(reference={self._info.reference!r}, "
            f"valid_to={self._info.valid_to.isoformat()})"
        )

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError(
            "SigningCertificate holds a private key and cannot be pickled or copied; "
            "persist it with a signing certificate store's save()."
        )
