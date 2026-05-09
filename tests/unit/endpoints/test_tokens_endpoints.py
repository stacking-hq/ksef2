from typing import cast

import pytest

from polyfactory.factories import BaseFactory
from pydantic import BaseModel

from ksef2.core import exceptions
from ksef2.core.routes import TokenRoutes
from ksef2.endpoints.tokens import TokenEndpoints, ListTokensQueryParams
from tests.unit.fakes import transport
from tests.unit.factories.tokens import (
    GenerateTokenRequestFactory,
    GenerateTokenResponseFactory,
    QueryTokensResponseFactory,
    TokenStatusResponseFactory,
)

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


@pytest.fixture
def req_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


@pytest.fixture
def resp_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


class TestTokenEndpoints:
    @pytest.fixture
    def token_eps(self, fake_transport: transport.FakeTransport) -> TokenEndpoints:
        return TokenEndpoints(fake_transport)

    @pytest.fixture
    def handled_token_eps(
        self, fake_transport: transport.FakeTransport
    ) -> TokenEndpoints:
        return TokenEndpoints(KSeFExceptionMiddleware(fake_transport))

    def test_generate_token(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_generate_req: GenerateTokenRequestFactory,
        token_generate_resp: GenerateTokenResponseFactory,
    ):
        request = token_generate_req.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = token_generate_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = token_eps.generate_token(request)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == TokenRoutes.GENERATE_TOKEN
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_generate_token_response_validation(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_generate_req: GenerateTokenRequestFactory,
        token_generate_resp: GenerateTokenResponseFactory,
    ):
        request = token_generate_req.build()
        response_data = token_generate_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = token_eps.generate_token(request)

        assert fake_transport.responses == []

    def test_generate_token_transport_error(
        self,
        handled_token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_generate_req: GenerateTokenRequestFactory,
        token_generate_resp: GenerateTokenResponseFactory,
    ):
        request = token_generate_req.build()
        expected = token_generate_resp.build()
        expected_dump = expected.model_dump(mode="json")

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                status_code=code, content=None, json_body=expected_dump
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel,
                    handled_token_eps.generate_token(request),
                )

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == TokenRoutes.GENERATE_TOKEN
            assert call.headers is None
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_list_tokens(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_list_resp: QueryTokensResponseFactory,
    ):
        expected = token_list_resp.build()
        expected_dump = expected.model_dump(mode="json")
        params: ListTokensQueryParams = {"pageSize": 10}

        fake_transport.enqueue(expected_dump)
        response = token_eps.list_tokens(**params)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == TokenRoutes.LIST_TOKENS
        assert call.params is not None
        assert call.params.get("pageSize") == "10"
        assert call.headers is None
        assert fake_transport.responses == []

    def test_list_tokens_continuation_token(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_list_resp: QueryTokensResponseFactory,
    ):
        expected = token_list_resp.build()
        expected_dump = expected.model_dump(mode="json")
        continuation_token = "test-continuation-token"

        fake_transport.enqueue(expected_dump)
        response = token_eps.list_tokens(continuation_token=continuation_token)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == TokenRoutes.LIST_TOKENS
        assert call.headers is not None
        assert call.headers.get("x-continuation-token") == continuation_token
        assert fake_transport.responses == []

    def test_list_tokens_query_params(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_list_resp: QueryTokensResponseFactory,
    ):
        expected = token_list_resp.build()
        expected_dump = expected.model_dump(mode="json")
        params: ListTokensQueryParams = {
            "status": ["Active"],
            "description": "test-token",
            "authorIdentifier": "123456789",
            "authorIdentifierType": "NIP",
            "pageSize": 50,
        }

        fake_transport.enqueue(expected_dump)
        response = token_eps.list_tokens(**params)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == TokenRoutes.LIST_TOKENS
        assert call.params is not None
        assert call.params.get("status") == "Active"
        assert call.params.get("description") == "test-token"
        assert call.params.get("authorIdentifier") == "123456789"
        assert call.params.get("authorIdentifierType") == "NIP"
        assert call.params.get("pageSize") == "50"
        assert fake_transport.responses == []

    def test_list_tokens_response_validation(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_list_resp: QueryTokensResponseFactory,
    ):
        response_data = token_list_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = token_eps.list_tokens()

        assert fake_transport.responses == []

    def test_list_tokens_transport_error(
        self,
        handled_token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_list_resp: QueryTokensResponseFactory,
    ):
        response = token_list_resp.build()

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
                _ = cast(BaseModel, handled_token_eps.list_tokens())

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == TokenRoutes.LIST_TOKENS
            assert call.headers is None

            assert fake_transport.responses == []

    def test_token_status(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_status_resp: TokenStatusResponseFactory,
    ):
        expected = token_status_resp.build()
        expected_dump = expected.model_dump(mode="json")
        reference_number = "20250625-TOKEN-2C3E6C8000-B675CF5D68-07"

        fake_transport.enqueue(expected_dump)
        response = token_eps.token_status(reference_number)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == TokenRoutes.TOKEN_STATUS.format(
            referenceNumber=reference_number
        )
        assert fake_transport.responses == []

    def test_token_status_response_validation(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_status_resp: TokenStatusResponseFactory,
    ):
        response_data = token_status_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = token_eps.token_status("20250625-TOKEN-2C3E6C8000-B675CF5D68-07")

        assert fake_transport.responses == []

    def test_token_status_transport_error(
        self,
        handled_token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
        token_status_resp: TokenStatusResponseFactory,
    ):
        response = token_status_resp.build()
        reference_number = "20250625-TOKEN-2C3E6C8000-B675CF5D68-07"

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
                _ = cast(BaseModel, handled_token_eps.token_status(reference_number))

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == TokenRoutes.TOKEN_STATUS.format(
                referenceNumber=reference_number
            )

            assert fake_transport.responses == []

    def test_revoke_token(
        self,
        token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-TOKEN-2C3E6C8000-B675CF5D68-07"

        fake_transport.enqueue(status_code=204, json_body=None)
        response = token_eps.revoke_token(reference_number)

        assert response is None
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert str(call.path) == TokenRoutes.REVOKE_TOKEN.format(
            referenceNumber=reference_number
        )
        assert fake_transport.responses == []

    def test_revoke_token_transport_error(
        self,
        handled_token_eps: TokenEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-TOKEN-2C3E6C8000-B675CF5D68-07"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code, content=None, json_body=None)

            with pytest.raises(exc):
                _ = handled_token_eps.revoke_token(reference_number)

            call = fake_transport.calls[0]
            assert call.method == "DELETE"
            assert str(call.path) == TokenRoutes.REVOKE_TOKEN.format(
                referenceNumber=reference_number
            )
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []
