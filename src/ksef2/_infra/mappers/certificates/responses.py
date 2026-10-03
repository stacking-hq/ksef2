"""Mappings from generated certificate schema models to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from ksef2._domain.models.certificates import (
    CertificateEnrollmentData,
    CertificateEnrollmentResponse,
    CertificateEnrollmentStatusResponse,
    CertificateInfo,
    CertificateLimitsResponse,
    CertificatesInfoList,
    CertificateTypeValue,
    CertificateStatusValue,
    SubjectIdentifier,
    RetrievedCertificatesList,
    Certificate,
)
from ksef2._infra.schema.api import spec

from pydantic import BaseModel

# --- overloads ---


@overload
def from_spec(
    response: spec.CertificateLimitsResponse,
) -> CertificateLimitsResponse: ...


@overload
def from_spec(
    response: spec.CertificateEnrollmentDataResponse,
) -> CertificateEnrollmentData: ...


@overload
def from_spec(
    response: spec.EnrollCertificateResponse,
) -> CertificateEnrollmentResponse: ...


@overload
def from_spec(
    response: spec.CertificateEnrollmentStatusResponse,
) -> CertificateEnrollmentStatusResponse: ...


@overload
def from_spec(
    response: spec.CertificateSubjectIdentifier,
) -> SubjectIdentifier: ...


@overload
def from_spec(
    response: spec.CertificateSubjectIdentifierType,
) -> str: ...


@overload
def from_spec(response: spec.CertificateListItemStatus) -> CertificateStatusValue: ...


@overload
def from_spec(response: spec.KsefCertificateType) -> CertificateTypeValue: ...


@overload
def from_spec(response: spec.CertificateListItem) -> CertificateInfo: ...


@overload
def from_spec(response: spec.QueryCertificatesResponse) -> CertificatesInfoList: ...


@overload
def from_spec(response: spec.RetrieveCertificatesListItem) -> Certificate: ...


@overload
def from_spec(
    response: spec.RetrieveCertificatesResponse,
) -> RetrievedCertificatesList: ...


def from_spec(response: BaseModel | Enum) -> object:
    """Convert a generated certificate schema object into its domain counterpart.

    Args:
        response: Generated API model or enum value to map.

    Returns:
        The matching domain model or literal value.

    Raises:
        NotImplementedError: If no mapper exists for the provided type.
    """
    return _from_spec(response)


# --- dispatch ---


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @from_spec.register"
    )


@_from_spec.register
def _(
    response: spec.CertificateLimitsResponse,
) -> CertificateLimitsResponse:
    return CertificateLimitsResponse(
        can_request=response.canRequest,
        enrollment_limit=response.enrollment.limit,
        enrollment_remaining=response.enrollment.remaining,
        certificate_limit=response.certificate.limit,
        certificate_remaining=response.certificate.remaining,
    )


@_from_spec.register
def _(
    response: spec.CertificateEnrollmentDataResponse,
) -> CertificateEnrollmentData:
    return CertificateEnrollmentData(
        common_name=response.commonName,
        name=response.givenName,
        surname=response.surname,
        iso_country_code=response.countryName,
        serial_number=response.serialNumber,
        unique_identifier=response.uniqueIdentifier,
        organization_name=response.organizationName,
        organization_identifier=response.organizationIdentifier,
    )


@_from_spec.register
def _(
    response: spec.EnrollCertificateResponse,
) -> CertificateEnrollmentResponse:
    return CertificateEnrollmentResponse(
        reference_number=response.referenceNumber,
        timestamp=response.timestamp,
    )


@_from_spec.register
def _(
    response: spec.CertificateEnrollmentStatusResponse,
) -> CertificateEnrollmentStatusResponse:
    return CertificateEnrollmentStatusResponse(
        request_date=response.requestDate,
        status_code=response.status.code,
        status_description=response.status.description,
        status_details=response.status.details,
        certificate_serial_number=response.certificateSerialNumber,
    )


@_from_spec.register
def _(c: spec.CertificateListItem) -> CertificateInfo:
    return CertificateInfo(
        serial_number=c.certificateSerialNumber,
        name=c.name,
        common_name=c.commonName,
        type=from_spec(c.type),
        status=from_spec(c.status),
        subject_identifier=from_spec(c.subjectIdentifier),
        valid_from=c.validFrom,
        valid_to=c.validTo,
        request_date=c.requestDate,
        last_use_date=c.lastUseDate,
    )


@_from_spec.register
def _(
    response: spec.CertificateSubjectIdentifier,
) -> SubjectIdentifier:
    subject_type = "_"
    match response.type:
        case spec.CertificateSubjectIdentifierType.Nip:
            subject_type = "nip"
        case spec.CertificateSubjectIdentifierType.Pesel:
            subject_type = "pesel"
        case spec.CertificateSubjectIdentifierType.Fingerprint:
            subject_type = "fingerprint"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)

    return SubjectIdentifier(
        type=subject_type,
        value=response.value,
    )


@_from_spec.register
def _(
    response: spec.CertificateSubjectIdentifierType,
) -> str:
    match response:
        case spec.CertificateSubjectIdentifierType.Nip:
            return "nip"
        case spec.CertificateSubjectIdentifierType.Pesel:
            return "pesel"
        case spec.CertificateSubjectIdentifierType.Fingerprint:
            return "fingerprint"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.CertificateListItemStatus) -> CertificateStatusValue:
    match response:
        case spec.CertificateListItemStatus.Active:
            return "active"
        case spec.CertificateListItemStatus.Revoked:
            return "revoked"
        case spec.CertificateListItemStatus.Expired:
            return "expired"
        case spec.CertificateListItemStatus.Blocked:
            return "blocked"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.KsefCertificateType) -> CertificateTypeValue:
    match response:
        case spec.KsefCertificateType.Authentication:
            return "authentication"
        case spec.KsefCertificateType.Offline:
            return "offline"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(
    response: spec.QueryCertificatesResponse,
) -> CertificatesInfoList:
    return CertificatesInfoList(
        certificates=[from_spec(c) for c in response.certificates],
        has_more=response.hasMore,
    )


@_from_spec.register
def _(response: spec.RetrieveCertificatesListItem) -> Certificate:
    return Certificate(
        name=response.certificateName,
        certificate_type=from_spec(response.certificateType),
        base64_encoded_certificate=response.certificate,
        serial_number=response.certificateSerialNumber,
    )


@_from_spec.register
def _(
    response: spec.RetrieveCertificatesResponse,
) -> RetrievedCertificatesList:
    return RetrievedCertificatesList(
        certificates=[from_spec(c) for c in response.certificates],
    )
