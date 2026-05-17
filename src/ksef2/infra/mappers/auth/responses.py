"""Mappings from generated auth schema models to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2.domain.models.auth import (
    AuthenticationMethod,
    AuthenticationMethodCategory,
    AuthenticationSession,
    AuthenticationSessionsResponse,
    AuthInitResponse,
    AuthOperationStatus,
    AuthTokens,
    ChallengeResponse,
    RefreshedToken,
    TokenCredentials,
)
from ksef2.infra.schema.api import spec


@overload
def from_spec(response: spec.AuthenticationChallengeResponse) -> ChallengeResponse: ...


@overload
def from_spec(response: spec.TokenInfo) -> TokenCredentials: ...


@overload
def from_spec(response: spec.AuthenticationInitResponse) -> AuthInitResponse: ...


@overload
def from_spec(
    response: spec.AuthenticationMethod,
) -> AuthenticationMethod: ...


@overload
def from_spec(
    response: spec.AuthenticationMethodCategory,
) -> AuthenticationMethodCategory: ...


@overload
def from_spec(
    response: spec.AuthenticationOperationStatusResponse,
) -> AuthOperationStatus: ...


@overload
def from_spec(
    response: spec.AuthenticationListResponse,
) -> AuthenticationSessionsResponse: ...


@overload
def from_spec(response: spec.AuthenticationTokensResponse) -> AuthTokens: ...


@overload
def from_spec(response: spec.AuthenticationTokenRefreshResponse) -> RefreshedToken: ...


@overload
def from_spec(response: spec.AuthenticationListItem) -> AuthenticationSession: ...


def from_spec(response: BaseModel | Enum) -> object:
    """Convert a generated auth schema object into its domain counterpart.

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


_AUTHENTICATION_METHOD_BY_CODE: dict[str, AuthenticationMethod] = {
    "token.ksef": "token",
    "national-node.trusted-profile": "trusted_profile",
    "other.internal-certificate": "internal_certificate",
    "xades.qualified-signature": "qualified_signature",
    "xades.qualified-seal": "qualified_seal",
    "xades.personal-signature": "personal_signature",
    "xades.peppol-signature": "peppol_signature",
    "xades.ksef-certificate": "ksef_certificate",
}


def _method_from_code(code: str) -> AuthenticationMethod:
    return _AUTHENTICATION_METHOD_BY_CODE.get(code, "other")


@_from_spec.register
def _(response: spec.AuthenticationChallengeResponse) -> ChallengeResponse:
    return ChallengeResponse(
        challenge=response.challenge,
        timestamp=response.timestamp,
        timestamp_ms=response.timestampMs,
    )


@_from_spec.register
def _(response: spec.TokenInfo) -> TokenCredentials:
    return TokenCredentials(
        token=response.token,
        valid_until=response.validUntil,
    )


@_from_spec.register
def _(response: spec.AuthenticationInitResponse) -> AuthInitResponse:
    return AuthInitResponse(
        reference_number=response.referenceNumber,
        authentication_token=from_spec(response.authenticationToken),
    )


@_from_spec.register
def _(response: spec.AuthenticationMethod) -> AuthenticationMethod:
    match response:
        case spec.AuthenticationMethod.Token:
            return "token"
        case spec.AuthenticationMethod.TrustedProfile:
            return "trusted_profile"
        case spec.AuthenticationMethod.InternalCertificate:
            return "internal_certificate"
        case spec.AuthenticationMethod.QualifiedSignature:
            return "qualified_signature"
        case spec.AuthenticationMethod.QualifiedSeal:
            return "qualified_seal"
        case spec.AuthenticationMethod.PersonalSignature:
            return "personal_signature"
        case spec.AuthenticationMethod.PeppolSignature:
            return "peppol_signature"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.AuthenticationMethodCategory) -> AuthenticationMethodCategory:
    match response:
        case spec.AuthenticationMethodCategory.XadesSignature:
            return "xades_signature"
        case spec.AuthenticationMethodCategory.NationalNode:
            return "national_node"
        case spec.AuthenticationMethodCategory.Token:
            return "token"
        case spec.AuthenticationMethodCategory.Other:
            return "other"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_from_spec.register
def _(response: spec.AuthenticationOperationStatusResponse) -> AuthOperationStatus:
    return AuthOperationStatus(
        start_date=response.startDate,
        authentication_method=_method_from_code(response.authenticationMethodInfo.code),
        authentication_method_category=from_spec(
            response.authenticationMethodInfo.category
        ),
        authentication_method_code=response.authenticationMethodInfo.code,
        authentication_method_display_name=response.authenticationMethodInfo.displayName,
        status_code=response.status.code,
        status_description=response.status.description,
        status_details=response.status.details,
        is_token_redeemed=response.isTokenRedeemed,
        last_token_refresh_date=response.lastTokenRefreshDate,
        refresh_token_valid_until=response.refreshTokenValidUntil,
    )


@_from_spec.register
def _(response: spec.AuthenticationListItem) -> AuthenticationSession:
    return AuthenticationSession(
        start_date=response.startDate,
        authentication_method=_method_from_code(response.authenticationMethodInfo.code),
        authentication_method_category=from_spec(
            response.authenticationMethodInfo.category
        ),
        authentication_method_code=response.authenticationMethodInfo.code,
        authentication_method_display_name=response.authenticationMethodInfo.displayName,
        status_code=response.status.code,
        status_description=response.status.description,
        status_details=response.status.details,
        is_token_redeemed=response.isTokenRedeemed,
        last_token_refresh_date=response.lastTokenRefreshDate,
        refresh_token_valid_until=response.refreshTokenValidUntil,
        reference_number=response.referenceNumber,
        is_current=response.isCurrent,
    )


@_from_spec.register
def _(response: spec.AuthenticationListResponse) -> AuthenticationSessionsResponse:
    return AuthenticationSessionsResponse(
        continuation_token=response.continuationToken,
        items=[from_spec(item) for item in response.items],
    )


@_from_spec.register
def _(response: spec.AuthenticationTokensResponse) -> AuthTokens:
    return AuthTokens(
        access_token=from_spec(response.accessToken),
        refresh_token=from_spec(response.refreshToken),
    )


@_from_spec.register
def _(response: spec.AuthenticationTokenRefreshResponse) -> RefreshedToken:
    return RefreshedToken(
        access_token=from_spec(response.accessToken),
    )
