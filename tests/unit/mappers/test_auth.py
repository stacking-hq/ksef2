from polyfactory import BaseFactory

from ksef2.domain.models import auth as domain_auth
from ksef2.infra.mappers.auth import from_spec, to_spec
from ksef2.infra.schema.api import spec
from ksef2.infra.schema.api.supp.auth import (
    InitTokenAuthenticationRequest as SuppInitTokenAuthenticationRequest,
)
from tests.unit.factories.auth import (
    AuthenticationListItemFactory,
    DomainInitTokenAuthenticationRequestFactory,
    TokenInfoFactory,
)


class TestAuthResponseMapper:
    def test_map_authentication_method_token(self) -> None:
        assert from_spec(spec.AuthenticationMethod.Token) == "token"

    def test_map_authentication_method_qualified_signature(self) -> None:
        assert (
            from_spec(spec.AuthenticationMethod.QualifiedSignature)
            == "qualified_signature"
        )

    def test_map_authentication_method_category_token(self) -> None:
        assert from_spec(spec.AuthenticationMethodCategory.Token) == "token"

    def test_map_authentication_method_category_xades_signature(self) -> None:
        assert (
            from_spec(spec.AuthenticationMethodCategory.XadesSignature)
            == "xades_signature"
        )

    def test_map_challenge_response(
        self, auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse]
    ) -> None:
        mapped_input = auth_challenge_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.ChallengeResponse)
        assert output.challenge == mapped_input.challenge
        assert output.timestamp == mapped_input.timestamp
        assert output.timestamp_ms == mapped_input.timestampMs

    def test_map_token_info(self) -> None:
        mapped_input = TokenInfoFactory.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.TokenCredentials)
        assert output.token == mapped_input.token
        assert output.valid_until == mapped_input.validUntil

    def test_map_auth_init_response(
        self, auth_init_resp: BaseFactory[spec.AuthenticationInitResponse]
    ) -> None:
        mapped_input = auth_init_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.AuthInitResponse)
        assert output.reference_number == mapped_input.referenceNumber
        assert (
            output.authentication_token.token == mapped_input.authenticationToken.token
        )
        assert (
            output.authentication_token.valid_until
            == mapped_input.authenticationToken.validUntil
        )

    def test_map_auth_status_response(
        self,
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
    ) -> None:
        mapped_input = auth_status_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.AuthOperationStatus)
        assert output.start_date == mapped_input.startDate
        assert output.authentication_method == "token"
        assert output.authentication_method_category == from_spec(
            mapped_input.authenticationMethodInfo.category
        )
        assert (
            output.authentication_method_code
            == mapped_input.authenticationMethodInfo.code
        )
        assert (
            output.authentication_method_display_name
            == mapped_input.authenticationMethodInfo.displayName
        )
        assert output.status_code == mapped_input.status.code
        assert output.status_description == mapped_input.status.description
        assert output.status_details == mapped_input.status.details
        assert output.is_token_redeemed == mapped_input.isTokenRedeemed
        assert output.last_token_refresh_date == mapped_input.lastTokenRefreshDate
        assert output.refresh_token_valid_until == mapped_input.refreshTokenValidUntil

    def test_map_authentication_session(self) -> None:
        mapped_input = AuthenticationListItemFactory.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.AuthenticationSession)
        assert output.reference_number == mapped_input.referenceNumber
        assert output.is_current == mapped_input.isCurrent
        assert output.authentication_method == "token"
        assert output.authentication_method_category == from_spec(
            mapped_input.authenticationMethodInfo.category
        )

    def test_map_authentication_session_from_transport_code(self) -> None:
        mapped_input = AuthenticationListItemFactory.build(
            authenticationMethod=spec.AuthenticationMethod.QualifiedSeal,
            authenticationMethodInfo=spec.AuthenticationMethodInfo(
                category=spec.AuthenticationMethodCategory.XadesSignature,
                code="xades.qualified-seal",
                displayName="Pieczęć kwalifikowana",
            ),
        )

        output = from_spec(mapped_input)

        assert output.authentication_method == "qualified_seal"
        assert output.authentication_method_code == "xades.qualified-seal"

    def test_map_authentication_session_ksef_certificate(self) -> None:
        mapped_input = AuthenticationListItemFactory.build(
            authenticationMethod=spec.AuthenticationMethod.InternalCertificate,
            authenticationMethodInfo=spec.AuthenticationMethodInfo(
                category=spec.AuthenticationMethodCategory.XadesSignature,
                code="xades.ksef-certificate",
                displayName="Certyfikat KSeF",
            ),
        )

        output = from_spec(mapped_input)

        assert output.authentication_method == "ksef_certificate"
        assert output.authentication_method_category == "xades_signature"
        assert output.authentication_method_code == "xades.ksef-certificate"

    def test_map_authentication_sessions_response(
        self, auth_list_resp: BaseFactory[spec.AuthenticationListResponse]
    ) -> None:
        mapped_input = auth_list_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.AuthenticationSessionsResponse)
        assert output.continuation_token == mapped_input.continuationToken
        assert len(output.items) == len(mapped_input.items)

    def test_map_auth_tokens(
        self, auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse]
    ) -> None:
        mapped_input = auth_tokens_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.AuthTokens)
        assert output.access_token.token == mapped_input.accessToken.token
        assert output.refresh_token.token == mapped_input.refreshToken.token

    def test_map_refreshed_token(
        self,
        auth_refresh_resp: BaseFactory[spec.AuthenticationTokenRefreshResponse],
    ) -> None:
        mapped_input = auth_refresh_resp.build()
        output = from_spec(mapped_input)

        assert isinstance(output, domain_auth.RefreshedToken)
        assert output.access_token.token == mapped_input.accessToken.token


class TestAuthRequestMapper:
    def test_to_spec_context_identifier_type_nip(self) -> None:
        assert to_spec("nip") == spec.AuthenticationContextIdentifierType.Nip

    def test_to_spec_context_identifier_type_peppol(self) -> None:
        assert to_spec("peppol_id") == spec.AuthenticationContextIdentifierType.PeppolId

    def test_to_spec_init_token_authentication_request(self) -> None:
        request = DomainInitTokenAuthenticationRequestFactory.build()
        output = to_spec(request)

        assert isinstance(output, SuppInitTokenAuthenticationRequest)
        assert output.challenge == request.challenge
        assert output.contextIdentifier.type == to_spec(request.context_type)
        assert output.contextIdentifier.value == request.context_value
        assert output.encryptedToken == request.encrypted_token
        assert output.publicKeyId == request.public_key_id
        assert output.authorizationPolicy is None

    def test_to_spec_unknown_string_raises(self) -> None:
        import pytest

        with pytest.raises(NotImplementedError, match="No mapper for string value"):
            _ = to_spec("not_supported")  # pyright: ignore[reportArgumentType]
