from typing import cast

import pytest

from pydantic import BaseModel

from ksef2.core import exceptions
from ksef2.core.routes import PeppolRoutes
from ksef2.endpoints.peppol import PeppolEndpoints
from tests.unit.fakes import transport
from tests.unit.factories.peppol import QueryPeppolProvidersResponseFactory

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


class TestPeppolEndpoints:
    @pytest.fixture
    def peppol_eps(self, fake_transport: transport.FakeTransport) -> PeppolEndpoints:
        return PeppolEndpoints(fake_transport)

    @pytest.fixture
    def handled_peppol_eps(
        self, fake_transport: transport.FakeTransport
    ) -> PeppolEndpoints:
        return PeppolEndpoints(KSeFExceptionMiddleware(fake_transport))

    def test_query_providers(
        self,
        peppol_eps: PeppolEndpoints,
        fake_transport: transport.FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        expected = peppol_providers_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = peppol_eps.query_providers()

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == PeppolRoutes.QUERY_PROVIDERS
        assert not call.params
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_query_providers_no_params(
        self,
        peppol_eps: PeppolEndpoints,
        fake_transport: transport.FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        expected = peppol_providers_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = peppol_eps.query_providers()

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == PeppolRoutes.QUERY_PROVIDERS
        assert not call.params
        assert fake_transport.responses == []

    def test_query_providers_pagination(
        self,
        peppol_eps: PeppolEndpoints,
        fake_transport: transport.FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        expected = peppol_providers_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = peppol_eps.query_providers(pageOffset=20, pageSize=50)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == PeppolRoutes.QUERY_PROVIDERS
        assert call.params is not None
        assert call.params.get("pageOffset") == "20"
        assert call.params.get("pageSize") == "50"
        assert fake_transport.responses == []

    def test_query_providers_response_validation(
        self,
        peppol_eps: PeppolEndpoints,
        fake_transport: transport.FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        response_data = peppol_providers_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = peppol_eps.query_providers()

        assert fake_transport.responses == []

    def test_query_providers_transport_error(
        self,
        handled_peppol_eps: PeppolEndpoints,
        fake_transport: transport.FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        response = peppol_providers_resp.build()

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
                _ = cast(BaseModel, handled_peppol_eps.query_providers())

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == PeppolRoutes.QUERY_PROVIDERS
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert not call.params

            assert fake_transport.responses == []
