from ksef2.domain.models import tokens as domain_tokens
from ksef2.infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture


# --- factories for spec models ---


@register_fixture(name="token_generate_req")
class GenerateTokenRequestFactory(ModelFactory[spec.GenerateTokenRequest]):
    @classmethod
    def permissions(cls) -> list[spec.TokenPermissionType]:
        return [spec.TokenPermissionType.InvoiceRead]


@register_fixture(name="token_generate_resp")
class GenerateTokenResponseFactory(ModelFactory[spec.GenerateTokenResponse]):
    reference_number: str = "ref-12345678-1234-1234-1234-123456789012"
    token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"


@register_fixture(name="token_status_resp")
class TokenStatusResponseFactory(ModelFactory[spec.TokenStatusResponse]):
    reference_number: str = "ref-12345678-1234-1234-1234-123456789012"
    status: spec.AuthenticationTokenStatus = spec.AuthenticationTokenStatus.Active


class TokenAuthorIdentifierFactory(
    ModelFactory[spec.TokenAuthorIdentifierTypeIdentifier]
):
    type: spec.TokenAuthorIdentifierType = spec.TokenAuthorIdentifierType.Nip
    value: str = "1234567890"


class TokenContextIdentifierFactory(
    ModelFactory[spec.TokenContextIdentifierTypeIdentifier]
):
    type: spec.TokenContextIdentifierType = spec.TokenContextIdentifierType.Nip
    value: str = "1234567890"


class QueryTokensResponseItemFactory(ModelFactory[spec.QueryTokensResponseItem]):
    reference_number: str = "ref-12345678-1234-1234-1234-123456789012"
    author_identifier: spec.TokenAuthorIdentifierTypeIdentifier = (
        TokenAuthorIdentifierFactory.build()
    )
    context_identifier: spec.TokenContextIdentifierTypeIdentifier = (
        TokenContextIdentifierFactory.build()
    )
    description: str = "Test token"
    requested_permissions: list[spec.TokenPermissionType] = [
        spec.TokenPermissionType.InvoiceRead
    ]
    status: spec.AuthenticationTokenStatus = spec.AuthenticationTokenStatus.Active


@register_fixture(name="token_list_resp")
class QueryTokensResponseFactory(ModelFactory[spec.QueryTokensResponse]):
    @classmethod
    def tokens(cls) -> list[spec.QueryTokensResponseItem]:
        return [QueryTokensResponseItemFactory.build()]


# --- factories for domain models ---


@register_fixture(name="domain_token_generate_req")
class DomainGenerateTokenRequestFactory(
    ModelFactory[domain_tokens.GenerateTokenRequest]
):
    permissions: list[str] = ["invoice_read"]
    description: str = "Test token"


@register_fixture(name="domain_token_generate_resp")
class DomainGenerateTokenResponseFactory(
    ModelFactory[domain_tokens.GenerateTokenResponse]
):
    reference_number: str = "ref-12345678-1234-1234-1234-123456789012"
    token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"


@register_fixture(name="domain_token_status_resp")
class DomainTokenStatusResponseFactory(ModelFactory[domain_tokens.TokenStatusResponse]):
    reference_number: str = "ref-12345678-1234-1234-1234-123456789012"
    status: str = "active"


@register_fixture(name="domain_token_info")
class DomainTokenInfoFactory(ModelFactory[domain_tokens.TokenInfo]):
    reference_number: str = "ref-12345678-1234-1234-1234-123456789012"
    author_identifier: domain_tokens.TokenAuthorIdentifier = (
        domain_tokens.TokenAuthorIdentifier(
            type=domain_tokens.TokenAuthorIdentifierTypeEnum.NIP.value,
            value="1234567890",
        )
    )
    context_identifier: domain_tokens.TokenContextIdentifier = (
        domain_tokens.TokenContextIdentifier(
            type=domain_tokens.TokenContextIdentifierTypeEnum.NIP.value,
            value="1234567890",
        )
    )
    description: str = "Test token"
    requested_permissions: list[str] = ["invoice_read"]
    status: str = "active"
    status_details: list[str] | None = None


@register_fixture(name="domain_token_list_resp")
class DomainQueryTokensResponseFactory(ModelFactory[domain_tokens.QueryTokensResponse]):
    continuation_token: str | None = None
    tokens: list[domain_tokens.TokenInfo] = [DomainTokenInfoFactory.build()]
