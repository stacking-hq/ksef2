"""Mappings from certificate domain models to generated API schema models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2.domain.models.certificates import (
    EnrollCertificateRequest,
    RevokeCertificateRequest,
    RetrieveCertificatesRequest,
    QueryCertificatesRequest,
    CertificateTypeValue,
    CertificateTypeEnum,
    CertificateStatusValue,
    CertificateStatusEnum,
    RevocationReasonEnum,
    IdentifierTypeEnum,
)
from ksef2.infra.mappers.helpers import get_matching_enum
from ksef2.infra.schema.api import spec
from ksef2.infra.mappers import helpers


class ValidCertificatesEnums(Enum):
    CertificateType = CertificateTypeEnum
    CertificateStatus = CertificateStatusEnum
    RevocationReason = RevocationReasonEnum
    IdentifierType = IdentifierTypeEnum


VALID_CERT_ENUMS = [v.value for v in ValidCertificatesEnums.__members__.values()]


@overload
def to_spec(request: EnrollCertificateRequest) -> spec.EnrollCertificateRequest: ...


@overload
def to_spec(
    request: RevokeCertificateRequest,
) -> spec.RevokeCertificateRequest | None: ...


@overload
def to_spec(
    request: RetrieveCertificatesRequest,
) -> spec.RetrieveCertificatesRequest: ...


@overload
def to_spec(request: QueryCertificatesRequest) -> spec.QueryCertificatesRequest: ...


@overload
def to_spec(request: CertificateTypeValue) -> spec.KsefCertificateType: ...


@overload
def to_spec(
    request: CertificateStatusValue,
) -> spec.CertificateListItemStatus: ...


def to_spec(request: BaseModel | Enum | str) -> object:
    """Convert a certificate domain object or literal into its schema counterpart.

    Args:
        request: Domain model, enum, or supported string literal to map.

    Returns:
        The matching generated API schema object or enum value.

    Raises:
        NotImplementedError: If no mapper exists for the provided value.
    """
    if isinstance(request, str):
        enum_cls = get_matching_enum(request, VALID_CERT_ENUMS)
        if enum_cls is None:
            raise NotImplementedError(f"No mapper for string value: {request!r}")
        return _to_spec(enum_cls(request))
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel | Enum | str) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: CertificateTypeEnum) -> spec.KsefCertificateType:
    match request:
        case CertificateTypeEnum.AUTHENTICATION:
            return spec.KsefCertificateType.Authentication
        case CertificateTypeEnum.OFFLINE:
            return spec.KsefCertificateType.Offline
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: CertificateStatusEnum) -> spec.CertificateListItemStatus:
    match request:
        case CertificateStatusEnum.ACTIVE:
            return spec.CertificateListItemStatus.Active
        case CertificateStatusEnum.BLOCKED:
            return spec.CertificateListItemStatus.Blocked
        case CertificateStatusEnum.REVOKED:
            return spec.CertificateListItemStatus.Revoked
        case CertificateStatusEnum.EXPIRED:
            return spec.CertificateListItemStatus.Expired
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(
    request: EnrollCertificateRequest,
) -> spec.EnrollCertificateRequest:
    return spec.EnrollCertificateRequest(
        certificateName=request.certificate_name,
        certificateType=to_spec(request.certificate_type),
        csr=request.csr,
        validFrom=helpers.to_aware_datetime(request.valid_from)
        if request.valid_from
        else None,
    )


@_to_spec.register
def _(
    request: RevokeCertificateRequest,
) -> spec.RevokeCertificateRequest | None:
    reason = "_"
    match request.revocation_reason:
        case "unspecified":
            reason = spec.CertificateRevocationReason.Unspecified
        case "superseded":
            reason = spec.CertificateRevocationReason.Superseded
        case "key_compromise":
            reason = spec.CertificateRevocationReason.KeyCompromise
        case None:
            return None
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)

    return spec.RevokeCertificateRequest(revocationReason=reason)


@_to_spec.register
def _(
    request: RetrieveCertificatesRequest,
) -> spec.RetrieveCertificatesRequest:
    return spec.RetrieveCertificatesRequest(
        certificateSerialNumbers=[
            spec.CertificateSerialNumber.model_validate(serial_number)
            for serial_number in request.certificate_serial_numbers
        ],
    )


@_to_spec.register
def _(
    request: QueryCertificatesRequest,
) -> spec.QueryCertificatesRequest:
    return spec.QueryCertificatesRequest(
        certificateSerialNumber=request.certificate_serial_number,
        name=request.name,
        type=to_spec(request.certificate_type) if request.certificate_type else None,
        status=to_spec(request.status) if request.status else None,
        expiresAfter=helpers.to_aware_datetime(request.expires_after)
        if request.expires_after
        else None,
    )
