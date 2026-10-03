"""Mappings from generated token schema models to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2._domain.models.tokens import (
    GenerateTokenResponse,
    QueryTokensResponse,
    TokenAuthorIdentifier,
    TokenAuthorIdentifierType,
    TokenContextIdentifier,
    TokenContextIdentifierType,
    TokenInfo,
    TokenPermission,
    TokenStatus,
    TokenStatusResponse,
)
from ksef2._infra.schema.api import spec


@overload
def from_spec(response: spec.GenerateTokenResponse) -> GenerateTokenResponse: ...


@overload
def from_spec(response: spec.TokenStatusResponse) -> TokenStatusResponse: ...


@overload
def from_spec(response: spec.QueryTokensResponse) -> QueryTokensResponse: ...


@overload
def from_spec(response: spec.QueryTokensResponseItem) -> TokenInfo: ...


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
def _(response: spec.GenerateTokenResponse) -> GenerateTokenResponse:
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
