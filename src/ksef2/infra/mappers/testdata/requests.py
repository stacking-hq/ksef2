"""Mappings from testdata domain models to generated API payloads."""

from enum import Enum
from functools import singledispatch
from typing import Literal, assert_never, overload

from pydantic import BaseModel

from ksef2.domain.models.testdata import (
    AuthContextIdentifier,
    AuthContextIdentifierTypeEnum,
    BlockContextRequest,
    CreatePersonRequest,
    CreateSubjectRequest,
    DeletePersonRequest,
    DeleteSubjectRequest,
    EnableAttachmentsRequest,
    GrantPermissionsRequest,
    Identifier,
    IdentifierTypeEnum,
    Permission,
    PermissionTypeEnum,
    RevokeAttachmentsRequest,
    RevokePermissionsRequest,
    SubjectTypeEnum,
    SubUnit,
    UnblockContextRequest,
)
from ksef2.infra.mappers.helpers import get_matching_enum
from ksef2.infra.schema.api.supp import testdata as supp


class ValidTestDataEnums(Enum):
    SubjectType = SubjectTypeEnum
    IdentifierType = IdentifierTypeEnum
    AuthContextIdentifierType = AuthContextIdentifierTypeEnum
    PermissionType = PermissionTypeEnum


VALID_TESTDATA_ENUMS = [v.value for v in ValidTestDataEnums.__members__.values()]

type SuppSubjectType = Literal["EnforcementAuthority", "VatGroup", "JST"]
type SuppIdentifierType = Literal["Nip", "Pesel", "Fingerprint", "System"]
type SuppAuthContextIdentifierType = Literal[
    "Nip", "InternalId", "NipVatUe", "PeppolId"
]
type SuppPermissionType = Literal[
    "InvoiceRead",
    "InvoiceWrite",
    "PefInvoiceWrite",
    "Introspection",
    "CredentialsRead",
    "CredentialsManage",
    "EnforcementOperations",
    "SubunitManage",
    "VatUeManage",
]


@overload
def to_spec(request: CreateSubjectRequest) -> supp.CreateSubjectRequest: ...


@overload
def to_spec(request: DeleteSubjectRequest) -> supp.DeleteSubjectRequest: ...


@overload
def to_spec(request: CreatePersonRequest) -> supp.CreatePersonRequest: ...


@overload
def to_spec(request: DeletePersonRequest) -> supp.DeletePersonRequest: ...


@overload
def to_spec(request: GrantPermissionsRequest) -> supp.GrantPermissionsRequest: ...


@overload
def to_spec(request: RevokePermissionsRequest) -> supp.RevokePermissionsRequest: ...


@overload
def to_spec(request: EnableAttachmentsRequest) -> supp.EnableAttachmentsRequest: ...


@overload
def to_spec(request: RevokeAttachmentsRequest) -> supp.RevokeAttachmentsRequest: ...


@overload
def to_spec(request: BlockContextRequest) -> supp.BlockContextRequest: ...


@overload
def to_spec(request: UnblockContextRequest) -> supp.UnblockContextRequest: ...


@overload
def to_spec(request: SubjectTypeEnum) -> SuppSubjectType: ...


@overload
def to_spec(request: IdentifierTypeEnum) -> SuppIdentifierType: ...


@overload
def to_spec(
    request: AuthContextIdentifierTypeEnum,
) -> SuppAuthContextIdentifierType: ...


@overload
def to_spec(request: PermissionTypeEnum) -> SuppPermissionType: ...


@overload
def to_spec(request: SubUnit) -> supp.SubUnit: ...


@overload
def to_spec(request: Identifier) -> supp.IdentifierInput: ...


@overload
def to_spec(request: AuthContextIdentifier) -> supp.AuthContextIdentifierInput: ...


@overload
def to_spec(request: Permission) -> supp.PermissionInput: ...


@overload
def to_spec(request: str) -> object: ...


def to_spec(request: BaseModel | Enum | str) -> object:
    """Convert a testdata domain object or literal into its schema counterpart.

    Args:
        request: Domain model, enum, or supported string literal to map.

    Returns:
        The matching generated API payload object or enum value.

    Raises:
        NotImplementedError: If no mapper exists for the provided value.
    """
    if isinstance(request, Enum):
        return _to_spec(request)
    if isinstance(request, str):
        enum_cls = get_matching_enum(request, VALID_TESTDATA_ENUMS)
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
def _(request: SubjectTypeEnum) -> SuppSubjectType:
    match request:
        case SubjectTypeEnum.ENFORCEMENT_AUTHORITY:
            return "EnforcementAuthority"
        case SubjectTypeEnum.VAT_GROUP:
            return "VatGroup"
        case SubjectTypeEnum.JST:
            return "JST"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: IdentifierTypeEnum) -> SuppIdentifierType:
    match request:
        case IdentifierTypeEnum.NIP:
            return "Nip"
        case IdentifierTypeEnum.PESEL:
            return "Pesel"
        case IdentifierTypeEnum.FINGERPRINT:
            return "Fingerprint"
        case IdentifierTypeEnum.SYSTEM:
            return "System"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: AuthContextIdentifierTypeEnum) -> SuppAuthContextIdentifierType:
    match request:
        case AuthContextIdentifierTypeEnum.NIP:
            return "Nip"
        case AuthContextIdentifierTypeEnum.INTERNAL_ID:
            return "InternalId"
        case AuthContextIdentifierTypeEnum.NIP_VAT_UE:
            return "NipVatUe"
        case AuthContextIdentifierTypeEnum.PEPPOL_ID:
            return "PeppolId"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: PermissionTypeEnum) -> SuppPermissionType:
    match request:
        case PermissionTypeEnum.INVOICE_READ:
            return "InvoiceRead"
        case PermissionTypeEnum.INVOICE_WRITE:
            return "InvoiceWrite"
        case PermissionTypeEnum.PEF_INVOICE_WRITE:
            return "PefInvoiceWrite"
        case PermissionTypeEnum.INTROSPECTION:
            return "Introspection"
        case PermissionTypeEnum.CREDENTIALS_READ:
            return "CredentialsRead"
        case PermissionTypeEnum.CREDENTIALS_MANAGE:
            return "CredentialsManage"
        case PermissionTypeEnum.ENFORCEMENT_OPERATIONS:
            return "EnforcementOperations"
        case PermissionTypeEnum.SUBUNIT_MANAGE:
            return "SubunitManage"
        case PermissionTypeEnum.VAT_UE_MANAGE:
            return "VatUeManage"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: SubUnit) -> supp.SubUnit:
    return supp.SubUnit(
        subjectNip=request.subject_nip,
        description=request.description,
    )


@_to_spec.register
def _(request: Identifier) -> supp.IdentifierInput:
    return supp.IdentifierInput(
        type=to_spec(IdentifierTypeEnum(request.type)),
        value=request.value,
    )


@_to_spec.register
def _(request: AuthContextIdentifier) -> supp.AuthContextIdentifierInput:
    return supp.AuthContextIdentifierInput(
        type=to_spec(AuthContextIdentifierTypeEnum(request.type)),
        value=request.value,
    )


@_to_spec.register
def _(request: Permission) -> supp.PermissionInput:
    return supp.PermissionInput(
        permissionType=to_spec(PermissionTypeEnum(request.type)),
        description=request.description,
    )


@_to_spec.register
def _(request: CreateSubjectRequest) -> supp.CreateSubjectRequest:
    return supp.CreateSubjectRequest(
        subjectNip=request.subject_nip,
        subjectType=to_spec(SubjectTypeEnum(request.subject_type)),
        description=request.description,
        subunits=[to_spec(unit) for unit in request.subunits]
        if request.subunits
        else None,
        createdDate=request.created_date,
    )


@_to_spec.register
def _(request: DeleteSubjectRequest) -> supp.DeleteSubjectRequest:
    return supp.DeleteSubjectRequest(subjectNip=request.subject_nip)


@_to_spec.register
def _(request: CreatePersonRequest) -> supp.CreatePersonRequest:
    return supp.CreatePersonRequest(
        nip=request.nip,
        pesel=request.pesel,
        description=request.description,
        isBailiff=request.is_bailiff,
        isDeceased=request.is_deceased,
        createdDate=request.created_date,
    )


@_to_spec.register
def _(request: DeletePersonRequest) -> supp.DeletePersonRequest:
    return supp.DeletePersonRequest(nip=request.nip)


@_to_spec.register
def _(request: GrantPermissionsRequest) -> supp.GrantPermissionsRequest:
    return supp.GrantPermissionsRequest(
        contextIdentifier=to_spec(request.in_context_of),
        authorizedIdentifier=to_spec(request.grant_to),
        permissions=[to_spec(permission) for permission in request.permissions],
    )


@_to_spec.register
def _(request: RevokePermissionsRequest) -> supp.RevokePermissionsRequest:
    return supp.RevokePermissionsRequest(
        contextIdentifier=to_spec(request.in_context_of),
        authorizedIdentifier=to_spec(request.revoke_from),
    )


@_to_spec.register
def _(request: EnableAttachmentsRequest) -> supp.EnableAttachmentsRequest:
    return supp.EnableAttachmentsRequest(nip=request.nip)


@_to_spec.register
def _(request: RevokeAttachmentsRequest) -> supp.RevokeAttachmentsRequest:
    return supp.RevokeAttachmentsRequest(
        nip=request.nip,
        expectedEndDate=request.expected_end_date,
    )


@_to_spec.register
def _(request: BlockContextRequest) -> supp.BlockContextRequest:
    return supp.BlockContextRequest(contextIdentifier=to_spec(request.context))


@_to_spec.register
def _(request: UnblockContextRequest) -> supp.UnblockContextRequest:
    return supp.UnblockContextRequest(contextIdentifier=to_spec(request.context))
