"""Domain models for KSeF certificate management."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter

from ksef2.domain.models.base import KSeFBaseModel

type IdentifierType = Literal["nip", "pesel", "fingerprint"]
type RevocationReason = Literal["unspecified", "superseded", "key_compromise"]
type CertificateTypeValue = Literal["authentication", "offline"]
type CertificateStatusValue = Literal["active", "blocked", "revoked", "expired"]
type CertificateSerialNumber = Annotated[
    str, Field(max_length=16, min_length=16, pattern="^[0-9A-F]{16}$")
]

_CERTIFICATE_SERIAL_NUMBER_ADAPTER = TypeAdapter(CertificateSerialNumber)


def validate_certificate_serial_number(value: str) -> CertificateSerialNumber:
    """Validate and return a KSeF certificate serial number."""
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
    value: str


class Certificate(KSeFBaseModel):
    """Issued certificate payload returned by retrieval endpoints."""

    base64_encoded_certificate: str
    name: str
    serial_number: CertificateSerialNumber
    certificate_type: CertificateTypeValue


class RetrievedCertificatesList(KSeFBaseModel):
    """Certificates returned by the retrieval endpoint."""

    certificates: list[Certificate]


class CertificateQuota(KSeFBaseModel):
    """Limit and remaining count for one certificate quota."""

    limit: int
    remaining: int


class CertificateInfo(KSeFBaseModel):
    """Metadata for one certificate visible in certificate queries."""

    # certificate
    serial_number: CertificateSerialNumber
    name: str
    common_name: str
    type: CertificateTypeValue
    status: CertificateStatusValue

    # issued for
    subject_identifier: SubjectIdentifier

    # date
    valid_from: datetime
    valid_to: datetime
    last_use_date: datetime | None = None
    request_date: datetime


class CertificatesInfoList(KSeFBaseModel):
    """One page of certificate query results."""

    certificates: list[CertificateInfo]
    has_more: bool


class CertificateEnrollmentData(KSeFBaseModel):
    """Subject data that should be embedded in a certificate enrollment CSR."""

    common_name: str
    name: str | None = None
    surname: str | None = None
    iso_country_code: str
    serial_number: str | None = None
    unique_identifier: str | None = None
    organization_name: str | None = None
    organization_identifier: str | None = None

    @property
    def country_name(self) -> str:
        """Alias for ``iso_country_code`` used by certificate tooling."""
        return self.iso_country_code


class CertificateEnrollmentResponse(KSeFBaseModel):
    """Reference returned after submitting a certificate enrollment request."""

    reference_number: str
    timestamp: datetime


class CertificateEnrollmentStatusResponse(KSeFBaseModel):
    """Current status of a certificate enrollment request."""

    request_date: datetime
    status_code: int
    status_description: str
    status_details: list[str] | None = None
    certificate_serial_number: CertificateSerialNumber | None = None


class CertificateLimitsResponse(KSeFBaseModel):
    """Effective enrollment and certificate quotas for the current subject."""

    can_request: bool
    enrollment_limit: int
    enrollment_remaining: int
    certificate_limit: int
    certificate_remaining: int

    @property
    def enrollment(self) -> CertificateQuota:
        """Return the enrollment quota as a structured value."""
        return CertificateQuota(
            limit=self.enrollment_limit,
            remaining=self.enrollment_remaining,
        )

    @property
    def certificate(self) -> CertificateQuota:
        """Return the issued-certificate quota as a structured value."""
        return CertificateQuota(
            limit=self.certificate_limit,
            remaining=self.certificate_remaining,
        )


# --- Request models ---


class EnrollCertificateRequest(KSeFBaseModel):
    """Payload used to request a new certificate enrollment."""

    certificate_name: str
    certificate_type: CertificateTypeValue
    csr: str
    valid_from: datetime | str | None = None


class RetrieveCertificatesRequest(KSeFBaseModel):
    """Payload used to download issued certificates by serial number."""

    certificate_serial_numbers: list[CertificateSerialNumber]


class RevokeCertificateRequest(KSeFBaseModel):
    """Payload used to revoke a certificate when a reason is provided."""

    revocation_reason: RevocationReason | None = None


class QueryCertificatesRequest(KSeFBaseModel):
    """Optional filters for certificate search."""

    certificate_serial_number: CertificateSerialNumber | None = None
    name: str | None = None
    certificate_type: CertificateTypeValue | None = None
    status: CertificateStatusValue | None = None
    expires_after: datetime | str | None = None


QueryCertificatesResponse = CertificatesInfoList
