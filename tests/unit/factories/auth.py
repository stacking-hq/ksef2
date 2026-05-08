from datetime import datetime, timedelta, timezone

from ksef2.domain.models import auth as domain_auth
from ksef2.infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from tests.unit.helpers import VALID_BASE64, VALID_PUBLIC_KEY_ID


def _future_time(hours: int = 1) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


class AuthenticationMethodInfoFactory(ModelFactory[spec.AuthenticationMethodInfo]):
    category: spec.AuthenticationMethodCategory = (
        spec.AuthenticationMethodCategory.Token
    )
    code: str = "token.ksef"
    displayName: str = "Token KSeF"


class TokenInfoFactory(ModelFactory[spec.TokenInfo]):
    token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
    validUntil: datetime = _future_time()


class AuthenticationListItemFactory(ModelFactory[spec.AuthenticationListItem]):
    authenticationMethod: spec.AuthenticationMethod = spec.AuthenticationMethod.Token
    authenticationMethodInfo: spec.AuthenticationMethodInfo = (
        AuthenticationMethodInfoFactory.build()
    )
    referenceNumber: str = "20250514-AU-2DFC46C000-3AC6D5877F-D4"


@register_fixture(name="auth_challenge_resp")
class AuthenticationChallengeResponseFactory(
    ModelFactory[spec.AuthenticationChallengeResponse]
): ...


@register_fixture(name="auth_init_resp")
class AuthenticationInitResponseFactory(ModelFactory[spec.AuthenticationInitResponse]):
    authenticationToken: spec.TokenInfo = TokenInfoFactory.build()


@register_fixture(name="auth_status_resp")
class AuthenticationOperationStatusResponseFactory(
    ModelFactory[spec.AuthenticationOperationStatusResponse]
):
    authenticationMethod: spec.AuthenticationMethod = spec.AuthenticationMethod.Token
    authenticationMethodInfo: spec.AuthenticationMethodInfo = (
        AuthenticationMethodInfoFactory.build()
    )


@register_fixture(name="auth_tokens_resp")
class AuthenticationTokensResponseFactory(
    ModelFactory[spec.AuthenticationTokensResponse]
):
    accessToken: spec.TokenInfo = TokenInfoFactory.build(token="access-token")
    refreshToken: spec.TokenInfo = TokenInfoFactory.build(token="refresh-token")


@register_fixture(name="auth_refresh_resp")
class AuthenticationTokenRefreshResponseFactory(
    ModelFactory[spec.AuthenticationTokenRefreshResponse]
):
    accessToken: spec.TokenInfo = TokenInfoFactory.build(token="access-token")


@register_fixture(name="auth_list_resp")
class AuthenticationListResponseFactory(ModelFactory[spec.AuthenticationListResponse]):
    @classmethod
    def items(cls) -> list[spec.AuthenticationListItem]:
        return [AuthenticationListItemFactory.build()]


@register_fixture(name="auth_init_req")
class InitTokenAuthenticationRequestFactory(
    ModelFactory[spec.InitTokenAuthenticationRequest]
):
    challenge = "A" * 36
    encryptedToken = VALID_BASE64
    publicKeyId = VALID_PUBLIC_KEY_ID
    contextIdentifier = spec.AuthenticationContextIdentifier(
        type=spec.AuthenticationContextIdentifierType.Nip,
        value="1234567890",
    )
    authorizationPolicy = None


@register_fixture(name="domain_auth_init_req")
class DomainInitTokenAuthenticationRequestFactory(
    ModelFactory[domain_auth.InitTokenAuthenticationRequest]
):
    challenge: str = "A" * 36
    context_type: str = "nip"
    context_value: str = "1234567890"
    encrypted_token: str = VALID_BASE64
    public_key_id: str = VALID_PUBLIC_KEY_ID


@register_fixture(name="domain_auth_challenge_resp")
class DomainChallengeResponseFactory(ModelFactory[domain_auth.ChallengeResponse]): ...


@register_fixture(name="domain_auth_init_resp")
class DomainAuthInitResponseFactory(ModelFactory[domain_auth.AuthInitResponse]):
    authentication_token: domain_auth.TokenCredentials = domain_auth.TokenCredentials(
        token="auth-token",
        valid_until=_future_time(),
    )


@register_fixture(name="domain_auth_status_resp")
class DomainAuthOperationStatusFactory(ModelFactory[domain_auth.AuthOperationStatus]):
    authentication_method: str = "token"
    authentication_method_category: str = "token"
    authentication_method_code: str = "token"
    authentication_method_display_name: str = "Token"


@register_fixture(name="domain_auth_session")
class DomainAuthenticationSessionFactory(
    ModelFactory[domain_auth.AuthenticationSession]
):
    reference_number: str = "20250514-AU-2DFC46C000-3AC6D5877F-D4"
    authentication_method: str = "token"
    authentication_method_category: str = "token"
    authentication_method_code: str = "token"
    authentication_method_display_name: str = "Token"


@register_fixture(name="domain_auth_sessions_resp")
class DomainAuthenticationSessionsResponseFactory(
    ModelFactory[domain_auth.AuthenticationSessionsResponse]
):
    items: list[domain_auth.AuthenticationSession] = [
        DomainAuthenticationSessionFactory.build()
    ]


@register_fixture(name="domain_auth_tokens")
class DomainAuthTokensFactory(ModelFactory[domain_auth.AuthTokens]):
    access_token: domain_auth.TokenCredentials = domain_auth.TokenCredentials(
        token="fake-access-token",
        valid_until=_future_time(),
    )
    refresh_token: domain_auth.TokenCredentials = domain_auth.TokenCredentials(
        token="fake-refresh-token",
        valid_until=_future_time(24),
    )


@register_fixture(name="domain_auth_refresh")
class DomainRefreshedTokenFactory(ModelFactory[domain_auth.RefreshedToken]):
    access_token: domain_auth.TokenCredentials = domain_auth.TokenCredentials(
        token="access-token",
        valid_until=_future_time(),
    )
