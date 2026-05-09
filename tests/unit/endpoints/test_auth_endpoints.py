from typing import cast

import pytest

from pydantic import BaseModel

from ksef2.core import exceptions, headers
from ksef2.core.routes import AuthRoutes
from ksef2.endpoints.auth import AuthEndpoints
from tests.unit.fakes import transport
from tests.unit.factories.auth import (
    AuthenticationChallengeResponseFactory,
    AuthenticationInitResponseFactory,
    AuthenticationOperationStatusResponseFactory,
    AuthenticationTokensResponseFactory,
    AuthenticationTokenRefreshResponseFactory,
    AuthenticationListResponseFactory,
    InitTokenAuthenticationRequestFactory,
)

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


class TestAuthEndpoints:
    @pytest.fixture
    def auth_eps(self, fake_transport: transport.FakeTransport) -> AuthEndpoints:
        return AuthEndpoints(fake_transport)

    @pytest.fixture
    def handled_auth_eps(
        self, fake_transport: transport.FakeTransport
    ) -> AuthEndpoints:
        return AuthEndpoints(KSeFExceptionMiddleware(fake_transport))

    def test_challenge(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_challenge_resp: AuthenticationChallengeResponseFactory,
    ):
        expected = auth_challenge_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = auth_eps.challenge()

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == AuthRoutes.CHALLENGE
        assert call.json is None
        assert call.content is None
        assert call.headers is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_challenge_response_validation(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_challenge_resp: AuthenticationChallengeResponseFactory,
    ):
        response_data = auth_challenge_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = auth_eps.challenge()

        assert fake_transport.responses == []

    def test_challenge_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_challenge_resp: AuthenticationChallengeResponseFactory,
    ):
        response = auth_challenge_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_auth_eps.challenge())

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == AuthRoutes.CHALLENGE
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_token_auth(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_init_req: InitTokenAuthenticationRequestFactory,
        auth_init_resp: AuthenticationInitResponseFactory,
    ):
        request = auth_init_req.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = auth_init_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = auth_eps.token_auth(request)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == AuthRoutes.TOKEN_AUTH
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_token_auth_response_validation(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_init_req: InitTokenAuthenticationRequestFactory,
        auth_init_resp: AuthenticationInitResponseFactory,
    ):
        request = auth_init_req.build()
        response_data = auth_init_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = auth_eps.token_auth(request)

        assert fake_transport.responses == []

    def test_token_auth_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_init_req: InitTokenAuthenticationRequestFactory,
        auth_init_resp: AuthenticationInitResponseFactory,
    ):
        request = auth_init_req.build()
        response = auth_init_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_auth_eps.token_auth(request))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == AuthRoutes.TOKEN_AUTH
            assert call.headers is None
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_xades_auth(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_init_resp: AuthenticationInitResponseFactory,
    ):
        expected = auth_init_resp.build()
        expected_dump = expected.model_dump(mode="json")
        signed_xml = b"<SignedXML>...</SignedXML>"

        fake_transport.enqueue(expected_dump)
        response = auth_eps.xades_auth(signed_xml)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == AuthRoutes.XADES_SIGNATURE
        assert call.content == signed_xml
        assert call.headers is not None
        assert call.headers.get("Content-Type") == "application/xml"
        assert call.params is not None
        assert call.params.get("verifyCertificateChain") == "false"
        assert call.json is None
        assert fake_transport.responses == []

    def test_xades_auth_verify_chain_true(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_init_resp: AuthenticationInitResponseFactory,
    ):
        expected = auth_init_resp.build()
        expected_dump = expected.model_dump(mode="json")
        signed_xml = b"<SignedXML>...</SignedXML>"

        fake_transport.enqueue(expected_dump)
        response = auth_eps.xades_auth(signed_xml, verify_chain=True)

        assert response == expected
        call = fake_transport.calls[0]
        assert call.params is not None
        assert call.params.get("verifyCertificateChain") == "true"
        assert fake_transport.responses == []

    def test_xades_auth_response_validation(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_init_resp: AuthenticationInitResponseFactory,
    ):
        signed_xml = b"<SignedXML>...</SignedXML>"
        response_data = auth_init_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = auth_eps.xades_auth(signed_xml)

        assert fake_transport.responses == []

    def test_xades_auth_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_init_resp: AuthenticationInitResponseFactory,
    ):
        signed_xml = b"<SignedXML>...</SignedXML>"
        response = auth_init_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_auth_eps.xades_auth(signed_xml))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == AuthRoutes.XADES_SIGNATURE
            assert call.content == signed_xml
            assert call.params is not None

            assert fake_transport.responses == []

    def test_auth_status(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_status_resp: AuthenticationOperationStatusResponseFactory,
    ):
        expected = auth_status_resp.build()
        expected_dump = expected.model_dump(mode="json")
        bearer_token = "test-bearer-token"
        reference_number = "20250625-AUTH-2C3E6C8000-B675CF5D68-07"

        fake_transport.enqueue(expected_dump)
        response = auth_eps.auth_status(bearer_token, reference_number)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == AuthRoutes.AUTH_STATUS.format(
            referenceNumber=reference_number
        )
        assert call.headers is not None
        assert call.headers == headers.KSeFHeaders.bearer(bearer_token)
        assert call.json is None
        assert call.content is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_auth_status_response_validation(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_status_resp: AuthenticationOperationStatusResponseFactory,
    ):
        bearer_token = "test-bearer-token"
        reference_number = "20250625-AUTH-2C3E6C8000-B675CF5D68-07"
        response_data = auth_status_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = auth_eps.auth_status(bearer_token, reference_number)

        assert fake_transport.responses == []

    def test_auth_status_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_status_resp: AuthenticationOperationStatusResponseFactory,
    ):
        bearer_token = "test-bearer-token"
        reference_number = "20250625-AUTH-2C3E6C8000-B675CF5D68-07"
        response = auth_status_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel,
                    handled_auth_eps.auth_status(bearer_token, reference_number),
                )

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == AuthRoutes.AUTH_STATUS.format(
                referenceNumber=reference_number
            )
            assert call.headers == headers.KSeFHeaders.bearer(bearer_token)
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_redeem_token(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_tokens_resp: AuthenticationTokensResponseFactory,
    ):
        expected = auth_tokens_resp.build()
        expected_dump = expected.model_dump(mode="json")
        bearer_token = "test-bearer-token"

        fake_transport.enqueue(expected_dump)
        response = auth_eps.redeem_token(bearer_token)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == AuthRoutes.REDEEM_TOKEN
        assert call.headers == headers.KSeFHeaders.bearer(bearer_token)
        assert call.json is None
        assert call.content is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_redeem_token_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_tokens_resp: AuthenticationTokensResponseFactory,
    ):
        bearer_token = "test-bearer-token"
        response = auth_tokens_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_auth_eps.redeem_token(bearer_token))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == AuthRoutes.REDEEM_TOKEN
            assert call.headers == headers.KSeFHeaders.bearer(bearer_token)
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_refresh_token(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_refresh_resp: AuthenticationTokenRefreshResponseFactory,
    ):
        expected = auth_refresh_resp.build()
        expected_dump = expected.model_dump(mode="json")
        bearer_token = "test-bearer-token"

        fake_transport.enqueue(expected_dump)
        response = auth_eps.refresh_token(bearer_token)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == AuthRoutes.REFRESH_TOKEN
        assert call.headers == headers.KSeFHeaders.bearer(bearer_token)
        assert call.json is None
        assert call.content is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_refresh_token_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_refresh_resp: AuthenticationTokenRefreshResponseFactory,
    ):
        bearer_token = "test-bearer-token"
        response = auth_refresh_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_auth_eps.refresh_token(bearer_token))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == AuthRoutes.REFRESH_TOKEN
            assert call.headers == headers.KSeFHeaders.bearer(bearer_token)
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_list_sessions(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_list_resp: AuthenticationListResponseFactory,
    ):
        expected = auth_list_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = auth_eps.list_sessions()

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == AuthRoutes.LIST_SESSIONS
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_list_sessions_continuation_token(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_list_resp: AuthenticationListResponseFactory,
    ):
        expected = auth_list_resp.build()
        expected_dump = expected.model_dump(mode="json")
        continuation_token = "test-continuation-token"

        fake_transport.enqueue(expected_dump)
        response = auth_eps.list_sessions(continuation_token=continuation_token)

        assert response == expected
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == AuthRoutes.LIST_SESSIONS
        assert call.headers is not None
        assert call.headers.get("x-continuation-token") == continuation_token
        assert fake_transport.responses == []

    def test_list_sessions_with_params(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_list_resp: AuthenticationListResponseFactory,
    ):
        expected = auth_list_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = auth_eps.list_sessions(pageSize=20)

        assert response == expected
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == AuthRoutes.LIST_SESSIONS
        assert call.params is not None
        assert call.params.get("pageSize") == "20"
        assert fake_transport.responses == []

    def test_list_sessions_response_validation(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_list_resp: AuthenticationListResponseFactory,
    ):
        response_data = auth_list_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = auth_eps.list_sessions()

        assert fake_transport.responses == []

    def test_list_sessions_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
        auth_list_resp: AuthenticationListResponseFactory,
    ):
        response = auth_list_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_auth_eps.list_sessions())

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == AuthRoutes.LIST_SESSIONS
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    def test_terminate_current_session(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        fake_transport.enqueue(status_code=204)
        assert None is auth_eps.terminate_current_session()
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert str(call.path) == AuthRoutes.TERMINATE_CURRENT_SESSION
        assert fake_transport.responses == []

    def test_terminate_current_session_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code)

            with pytest.raises(exc):
                handled_auth_eps.terminate_current_session()

            call = fake_transport.calls[0]
            assert call.method == "DELETE"
            assert str(call.path) == AuthRoutes.TERMINATE_CURRENT_SESSION
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_terminate_auth_session(
        self,
        auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-AUTH-2C3E6C8000-B675CF5D68-07"

        fake_transport.enqueue(status_code=204)
        assert auth_eps.terminate_auth_session(reference_number) is None
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert str(call.path) == AuthRoutes.TERMINATE_AUTH_SESSION.format(
            referenceNumber=reference_number
        )
        assert fake_transport.responses == []

    def test_terminate_auth_session_transport_error(
        self,
        handled_auth_eps: AuthEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-AUTH-2C3E6C8000-B675CF5D68-07"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code)

            with pytest.raises(exc):
                handled_auth_eps.terminate_auth_session(reference_number)

            call = fake_transport.calls[0]
            assert call.method == "DELETE"
            assert str(call.path) == AuthRoutes.TERMINATE_AUTH_SESSION.format(
                referenceNumber=reference_number
            )
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []
