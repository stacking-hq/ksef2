"""Domain models for KSeF certificate management."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter

from ksef2._domain.models.base import KSeFBaseModel

type IdentifierType = Literal["nip", "pesel", "fingerprint"]
type RevocationReason = Literal["unspecified", "superseded", "key_compromise"]
type CertificateTypeValue = Literal["authentication", "offline"]
type CertificateStatusValue = Literal["active", "blocked", "revoked", "expired"]
type CertificateSerialNumber = Annotated[
    str, Field(max_length=16, min_length=16, pattern="^[0-9A-F]{16}$")
]

_CERTIFICATE_SERIAL_NUMBER_ADAPTER = TypeAdapter(CertificateSerialNumber)


def validate_certificate_serial_number(value: str) -> CertificateSerialNumber:
    """Validate and return a KSeF certificate serial number.

    Args:
        value: Candidate serial number.

    Returns:
        The validated serial number.

    Raises:
        pydantic.ValidationError: If ``value`` is not a valid certificate serial number.
    """
    return _CERTIFICATE_SERIAL_NUMBER_ADAPTER.validate_python(value)


class CertificateTypeEnum(StrEnum):
    """Runtime enum for certificate types."""

    AUTHENTICATION = "authentication"
    OFFLINE = "offline"


class CertificateStatusEnum(StrEnum):
    """Runtime enum for certificate lifecycle statuses."""

    ACTIVE = "active"
    BLOCKED = "blocked"
    REVOKED = "revoked"
    EXPIRED = "expired"


class IdentifierTypeEnum(StrEnum):
    """Runtime enum for certificate subject identifier types."""

    NIP = "nip"
    PESEL = "pesel"
    FINGERPRINT = "fingerprint"


class RevocationReasonEnum(StrEnum):
    """Runtime enum for certificate revocation reasons."""

    UNSPECIFIED = "unspecified"
    SUPERSEDED = "superseded"
    KEY_COMPROMISE = "key_compromise"


class SubjectIdentifier(KSeFBaseModel):
    """Identifier of the subject the certificate was issued for."""

    type: IdentifierType
    """Kind of identifier in ``value`` (``nip``, ``pesel`` or ``fingerprint``)."""
    value: str
    """Identifier of the certificate subject."""


class Certificate(KSeFBaseModel):
    """Issued certificate payload returned by retrieval endpoints."""

    base64_encoded_certificate: str
    """DER-encoded X.509 certificate, Base64-encoded."""
    name: str
    """Name given to the certificate at enrollment."""
    serial_number: CertificateSerialNumber
    """Certificate serial number, in uppercase hexadecimal."""
    certificate_type: CertificateTypeValue
    """Certificate type, ``authentication`` or ``offline``."""


class RetrievedCertificatesList(KSeFBaseModel):
    """Certificates returned by the retrieval endpoint."""

    certificates: list[Certificate]
    """Retrieved certificates."""


class CertificateQuota(KSeFBaseModel):
    """Limit and remaining count for one certificate quota."""

    limit: int
    """Maximum number allowed."""
    remaining: int
    """Number still available."""


class CertificateInfo(KSeFBaseModel):
    """Metadata for one certificate visible in certificate queries."""

    # certificate
    serial_number: CertificateSerialNumber
    """Certificate serial number, in uppercase hexadecimal."""
    name: str
    """Name given to the certificate at enrollment."""
    common_name: str
    """Common name (CN) of the certificate subject."""
    type: CertificateTypeValue
    """Certificate type, ``authentication`` or ``offline``."""
    status: CertificateStatusValue
    """Lifecycle status of the certificate, such as ``active`` or ``revoked``."""

    # issued for
    subject_identifier: SubjectIdentifier
    """Identifier of the subject the certificate was issued for."""

    # date
    valid_from: datetime
    """Start of the certificate validity period."""
    valid_to: datetime
    """End of the certificate validity period."""
    last_use_date: datetime | None = None
    """When the certificate was last used; ``None`` if never used."""
    request_date: datetime
    """When the certificate was requested."""


class CertificatesInfoList(KSeFBaseModel):
    """One page of certificate query results."""

    certificates: list[CertificateInfo]
    """Certificates on this page."""
    has_more: bool
    """Whether more results are available after this page."""


class CertificateEnrollmentData(KSeFBaseModel):
    """Subject data that should be embedded in a certificate enrollment CSR."""

    common_name: str
    """Common name (CN) of the subject."""
    name: str | None = None
    """Given name of the subject, for certificates issued to a natural person."""
    surname: str | None = None
    """Surname of the subject, for certificates issued to a natural person."""
    iso_country_code: str
    """Two-letter ISO 3166 country code of the subject."""
    serial_number: str | None = None
    """Serial number attribute of the subject, such as a PESEL or NIP identifier."""
    unique_identifier: str | None = None
    """Unique identifier attribute of the subject."""
    organization_name: str | None = None
    """Organization name of the subject, for certificates issued to an entity."""
    organization_identifier: str | None = None
    """Organization identifier of the subject, such as ``VATPL-<NIP>``."""

    @property
    def country_name(self) -> str:
        """Alias for ``iso_country_code`` used by certificate tooling.

        Returns:
            The two-letter ISO country code.
        """
        return self.iso_country_code


class CertificateEnrollmentResponse(KSeFBaseModel):
    """Reference returned after submitting a certificate enrollment request."""

    reference_number: str
    """KSeF reference number of the operation or resource."""
    timestamp: datetime
    """When KSeF accepted the enrollment request."""


class CertificateEnrollmentStatusResponse(KSeFBaseModel):
    """Current status of a certificate enrollment request."""

    request_date: datetime
    """When the enrollment was requested."""
    status_code: int
    """Numeric status code; ``200`` means the certificate was issued."""
    status_description: str
    """Human-readable description of the status."""
    status_details: list[str] | None = None
    """Additional status details, if any."""
    certificate_serial_number: CertificateSerialNumber | None = None
    """Serial number of the issued certificate; ``None`` until issued."""


class CertificateLimitsResponse(KSeFBaseModel):
    """Effective enrollment and certificate quotas for the current subject."""

    can_request: bool
    """Whether the subject may currently submit an enrollment request."""
    enrollment_limit: int
    """Maximum number of enrollment requests allowed."""
    enrollment_remaining: int
    """Number of enrollment requests still available."""
    certificate_limit: int
    """Maximum number of active certificates allowed."""
    certificate_remaining: int
    """Number of additional certificates that may still be issued."""

    @property
    def enrollment(self) -> CertificateQuota:
        """Return the enrollment quota as a structured value.

        Returns:
            The enrollment limit and remaining count.
        """
        return CertificateQuota(
            limit=self.enrollment_limit,
            remaining=self.enrollment_remaining,
        )

    @property
    def certificate(self) -> CertificateQuota:
        """Return the issued-certificate quota as a structured value.

        Returns:
            The certificate limit and remaining count.
        """
        return CertificateQuota(
            limit=self.certificate_limit,
            remaining=self.certificate_remaining,
        )


# --- Request models ---


class EnrollCertificateRequest(KSeFBaseModel):
    """Payload used to request a new certificate enrollment."""

    certificate_name: str
    """Name to give the certificate."""
    certificate_type: CertificateTypeValue
    """Certificate type to request, ``authentication`` or ``offline``."""
    csr: str
    """PKCS#10 certificate signing request, DER-encoded and Base64-encoded."""
    valid_from: datetime | str | None = None
    """Requested start of validity as a datetime or ISO 8601 string; ``None`` for immediately."""


class RetrieveCertificatesRequest(KSeFBaseModel):
    """Payload used to download issued certificates by serial number."""

    certificate_serial_numbers: list[CertificateSerialNumber]
    """Serial numbers of the certificates to download."""


class RevokeCertificateRequest(KSeFBaseModel):
    """Payload used to revoke a certificate when a reason is provided."""

    revocation_reason: RevocationReason | None = None
    """Reason for the revocation; ``None`` to omit it."""


class QueryCertificatesRequest(KSeFBaseModel):
    """Optional filters for certificate search."""

    certificate_serial_number: CertificateSerialNumber | None = None
    """Match this certificate serial number."""
    name: str | None = None
    """Match this certificate name."""
    certificate_type: CertificateTypeValue | None = None
    """Match this certificate type."""
    status: CertificateStatusValue | None = None
    """Match this lifecycle status."""
    expires_after: datetime | str | None = None
    """Match certificates that expire after this datetime or ISO 8601 string."""


QueryCertificatesResponse = CertificatesInfoList
