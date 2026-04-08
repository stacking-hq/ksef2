"""Mappings from domain token models to generated API schema models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2.domain.models.tokens import (
    GenerateTokenRequest,
    TokenPermission,
    TokenPermissionEnum,
    TokenStatus,
    TokenStatusEnum,
    TokenAuthorIdentifierTypeEnum,
    TokenContextIdentifierTypeEnum,
)
from ksef2.infra.mappers.helpers import get_matching_enum
from ksef2.infra.schema.api import spec


class ValidTokensEnums(Enum):
    TokenPermission = TokenPermissionEnum
    TokenStatus = TokenStatusEnum


VALID_TOKEN_ENUMS = [v.value for v in ValidTokensEnums.__members__.values()]


@overload
def to_spec(request: GenerateTokenRequest) -> spec.GenerateTokenRequest: ...


@overload
def to_spec(request: TokenPermission) -> spec.TokenPermissionType: ...


@overload
def to_spec(request: TokenStatus) -> spec.AuthenticationTokenStatus: ...


@overload
def to_spec(request: str) -> object: ...


def to_spec(request: BaseModel | Enum | str) -> object:
    """Convert a domain token object or literal into its schema counterpart.

    Args:
        request: Domain model, enum, or supported string literal to map.

    Returns:
        The matching generated API schema object or enum value.

    Raises:
        NotImplementedError: If no mapper exists for the provided value.
    """
    if isinstance(request, str):
        enum_cls = get_matching_enum(request, VALID_TOKEN_ENUMS)
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
def _(request: TokenPermissionEnum) -> spec.TokenPermissionType:
    match request:
        case TokenPermissionEnum.INVOICE_READ:
            return spec.TokenPermissionType.InvoiceRead
        case TokenPermissionEnum.INVOICE_WRITE:
            return spec.TokenPermissionType.InvoiceWrite
        case TokenPermissionEnum.INTROSPECTION:
            return spec.TokenPermissionType.Introspection
        case TokenPermissionEnum.CREDENTIALS_READ:
            return spec.TokenPermissionType.CredentialsRead
        case TokenPermissionEnum.CREDENTIALS_MANAGE:
            return spec.TokenPermissionType.CredentialsManage
        case TokenPermissionEnum.SUBUNIT_MANAGE:
            return spec.TokenPermissionType.SubunitManage
        case TokenPermissionEnum.ENFORCEMENT_OPERATIONS:
            return spec.TokenPermissionType.EnforcementOperations
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: TokenStatusEnum) -> spec.AuthenticationTokenStatus:
    match request:
        case TokenStatusEnum.PENDING:
            return spec.AuthenticationTokenStatus.Pending
        case TokenStatusEnum.ACTIVE:
            return spec.AuthenticationTokenStatus.Active
        case TokenStatusEnum.REVOKING:
            return spec.AuthenticationTokenStatus.Revoking
        case TokenStatusEnum.REVOKED:
            return spec.AuthenticationTokenStatus.Revoked
        case TokenStatusEnum.FAILED:
            return spec.AuthenticationTokenStatus.Failed
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: TokenAuthorIdentifierTypeEnum) -> spec.TokenAuthorIdentifierType:
    match request:
        case TokenAuthorIdentifierTypeEnum.NIP:
            return spec.TokenAuthorIdentifierType.Nip
        case TokenAuthorIdentifierTypeEnum.PESEL:
            return spec.TokenAuthorIdentifierType.Pesel
        case TokenAuthorIdentifierTypeEnum.FINGERPRINT:
            return spec.TokenAuthorIdentifierType.Fingerprint
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: TokenContextIdentifierTypeEnum) -> spec.TokenContextIdentifierType:
    match request:
        case TokenContextIdentifierTypeEnum.NIP:
            return spec.TokenContextIdentifierType.Nip
        case TokenContextIdentifierTypeEnum.INTERNAL_ID:
            return spec.TokenContextIdentifierType.InternalId
        case TokenContextIdentifierTypeEnum.NIP_VAT_UE:
            return spec.TokenContextIdentifierType.NipVatUe
        case TokenContextIdentifierTypeEnum.PEPPOL_ID:
            return spec.TokenContextIdentifierType.PeppolId
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: GenerateTokenRequest) -> spec.GenerateTokenRequest:
    return spec.GenerateTokenRequest(
        permissions=[to_spec(p) for p in request.permissions],
        description=request.description,
    )
