"""Mappings from generated token schema models to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel
from pydantic.alias_generators import to_snake

from ksef2._domain.models.tokens import (
    GenerateTokenResponse,
    QueryTokensResponse,
    TokenAuthorIdentifier,
    TokenAuthorIdentifierType,
    TokenContextIdentifier,
    TokenContextIdentifierType,
    TokenInfo,
    TokenFailure,
    TokenPermission,
    TokenStatus,
    TokenStatusEnum,
    TokenStatusResponse,
)
from ksef2._infra.schema.api import spec


@overload
def from_spec(
    response: spec.GenerateTokenResponse | spec.GenerateTokenResponseRev2,
) -> GenerateTokenResponse: ...


@overload
def from_spec(
    response: spec.TokenStatusResponse | spec.TokenStatusResponseRev2,
) -> TokenStatusResponse: ...


@overload
def from_spec(
    response: spec.QueryTokensResponse | spec.QueryTokensResponseRev2,
) -> QueryTokensResponse: ...


@overload
def from_spec(
    response: spec.QueryTokensResponseItem | spec.QueryTokensResponseItemRev2,
) -> TokenInfo: ...


@overload
def from_spec(response: spec.AuthenticationTokenStatus) -> TokenStatus: ...


@overload
def from_spec(response: spec.TokenPermissionType) -> TokenPermission: ...


@overload
def from_spec(
    response: spec.TokenAuthorIdentifierTypeIdentifier,
) -> TokenAuthorIdentifier: ...


@overload
def from_spec(
    response: spec.TokenAuthorIdentifierType,
) -> TokenAuthorIdentifierType: ...


@overload
def from_spec(
    response: spec.TokenContextIdentifierTypeIdentifier,
) -> TokenContextIdentifier: ...


@overload
def from_spec(
    response: spec.TokenContextIdentifierType,
) -> TokenContextIdentifierType: ...


def from_spec(response: BaseModel | Enum) -> object:
    """Convert a generated token schema object into its domain counterpart.

    Args:
        response: Generated API model or enum value to map.

    Returns:
        The matching domain model or literal value.

    Raises:
        NotImplementedError: If no mapper exists for the provided type.
    """
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(response: spec.AuthenticationTokenStatus) -> TokenStatus:
    match response:
        case spec.AuthenticationTokenStatus.Pending:
            return "pending"
        case spec.AuthenticationTokenStatus.Active:
            return "active"
        case spec.AuthenticationTokenStatus.Revoking:
            return "revoking"
        case spec.AuthenticationTokenStatus.Revoked:
            return "revoked"
        case spec.AuthenticationTokenStatus.Failed:
            return "failed"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.TokenPermissionType) -> TokenPermission:
    match response:
        case spec.TokenPermissionType.InvoiceRead:
            return "invoice_read"
        case spec.TokenPermissionType.InvoiceWrite:
            return "invoice_write"
        case spec.TokenPermissionType.Introspection:
            return "introspection"
        case spec.TokenPermissionType.CredentialsRead:
            return "credentials_read"
        case spec.TokenPermissionType.CredentialsManage:
            return "credentials_manage"
        case spec.TokenPermissionType.SubunitManage:
            return "subunit_manage"
        case spec.TokenPermissionType.EnforcementOperations:
            return "enforcement_operations"
        case spec.TokenPermissionType.CollectiveIdentifierManage:
            return "collective_identifier_manage"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.TokenAuthorIdentifierType) -> TokenAuthorIdentifierType:
    match response:
        case spec.TokenAuthorIdentifierType.Nip:
            return "nip"
        case spec.TokenAuthorIdentifierType.Pesel:
            return "pesel"
        case spec.TokenAuthorIdentifierType.Fingerprint:
            return "fingerprint"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.TokenContextIdentifierType) -> TokenContextIdentifierType:
    match response:
        case spec.TokenContextIdentifierType.Nip:
            return "nip"
        case spec.TokenContextIdentifierType.InternalId:
            return "internal_id"
        case spec.TokenContextIdentifierType.NipVatUe:
            return "nip_vat_ue"
        case spec.TokenContextIdentifierType.PeppolId:
            return "peppol_id"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.TokenAuthorIdentifierTypeIdentifier) -> TokenAuthorIdentifier:
    return TokenAuthorIdentifier(
        type=from_spec(response.type),
        value=response.value,
    )


@_from_spec.register
def _(response: spec.TokenContextIdentifierTypeIdentifier) -> TokenContextIdentifier:
    return TokenContextIdentifier(
        type=from_spec(response.type),
        value=response.value,
    )


@_from_spec.register
def _(
    response: spec.GenerateTokenResponse | spec.GenerateTokenResponseRev2,
) -> GenerateTokenResponse:
    return GenerateTokenResponse(
        reference_number=response.referenceNumber,
        token=response.token,
    )


@_from_spec.register
def _(response: spec.TokenStatusResponse) -> TokenStatusResponse:
    return TokenStatusResponse(
        reference_number=response.referenceNumber,
        status=from_spec(response.status),
    )


@_from_spec.register
def _(response: spec.QueryTokensResponseItem) -> TokenInfo:
    return TokenInfo(
        reference_number=response.referenceNumber,
        author_identifier=from_spec(response.authorIdentifier),
        context_identifier=from_spec(response.contextIdentifier),
        description=response.description,
        requested_permissions=[from_spec(p) for p in response.requestedPermissions],
        date_created=response.dateCreated,
        last_use_date=response.lastUseDate,
        status=from_spec(response.status),
        status_details=response.statusDetails,
    )


@_from_spec.register
def _(response: spec.QueryTokensResponse) -> QueryTokensResponse:
    return QueryTokensResponse(
        continuation_token=response.continuationToken,
        tokens=[from_spec(t) for t in response.tokens],
    )


def _rev2_status(status: spec.TokenStatusRev2) -> TokenStatus:
    if status.code is spec.TokenStatusRev2Code.FutureValue:
        return "other"
    return TokenStatusEnum(to_snake(status.code.value)).value


def _rev2_failure(failure: spec.TokenFailureRev2 | None) -> TokenFailure | None:
    if failure is None:
        return None
    return TokenFailure(
        code=failure.code, description=failure.description, details=failure.details
    )


@_from_spec.register
def _(response: spec.TokenStatusResponseRev2) -> TokenStatusResponse:
    status = _rev2_status(response.status)
    return TokenStatusResponse(
        reference_number=response.referenceNumber,
        status=status,
        valid_from=response.validFrom,
        valid_to=response.validTo,
        failure=_rev2_failure(response.failure),
        raw_status=response.status.rawCode if status == "other" else None,
    )


@_from_spec.register
def _(response: spec.QueryTokensResponseItemRev2) -> TokenInfo:
    author = response.authorIdentifier
    context = response.contextIdentifier
    unknown_author = (
        author.type.code is spec.TokenAuthorIdentifierTypeCodeRev2.FutureValue
    )
    unknown_context = (
        context.type.code is spec.TokenContextIdentifierTypeCodeRev2.FutureValue
    )
    status = _rev2_status(response.status)
    failure = _rev2_failure(response.failure)
    return TokenInfo(
        reference_number=response.referenceNumber,
        author_identifier=TokenAuthorIdentifier(
            type="other"
            if unknown_author
            else from_spec(spec.TokenAuthorIdentifierType(author.type.code.value)),
            value=author.value,
            raw_type=author.type.rawCode if unknown_author else None,
        ),
        context_identifier=TokenContextIdentifier(
            type="other"
            if unknown_context
            else from_spec(spec.TokenContextIdentifierType(context.type.code.value)),
            value=context.value,
            raw_type=context.type.rawCode if unknown_context else None,
        ),
        description=response.description,
        requested_permissions=[
            from_spec(spec.TokenPermissionType(permission.code.value))
            for permission in response.requestedPermissions
            if permission.code is not spec.TokenPermissionCodeRev2.FutureValue
        ],
        unknown_permissions=[
            permission.rawCode
            for permission in response.requestedPermissions
            if permission.code is spec.TokenPermissionCodeRev2.FutureValue
        ],
        date_created=response.dateCreated,
        last_use_date=response.lastUseDate,
        status=status,
        status_details=failure.details if failure else None,
        valid_from=response.validFrom,
        valid_to=response.validTo,
        failure=failure,
        raw_status=response.status.rawCode if status == "other" else None,
    )


@_from_spec.register
def _(response: spec.QueryTokensResponseRev2) -> QueryTokensResponse:
    return QueryTokensResponse(
        continuation_token=response.continuationToken,
        tokens=[from_spec(token) for token in response.tokens],
    )
