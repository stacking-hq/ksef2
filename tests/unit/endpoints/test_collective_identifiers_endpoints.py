from polyfactory.factories import BaseFactory

from ksef2.core.routes import CollectiveIdentifierRoutes
from ksef2.endpoints.collective_identifiers import CollectiveIdentifiersEndpoints
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport

_KSEF_NUMBER = "1234567890-20250625-ABC123-DEF456-07"
_COLLECTIVE_IDENTIFIER_NUMBER = "1111111111-IZ202607-65ED02180000-E7"


class TestCollectiveIdentifiersEndpoints:
    def test_generate(
        self,
        fake_transport: FakeTransport,
        collective_generate_req: BaseFactory[spec.GenerateCollectiveIdentifierRequest],
        collective_generate_resp: BaseFactory[
            spec.GenerateCollectiveIdentifierResponse
        ],
    ) -> None:
        request = collective_generate_req.build()
        expected = collective_generate_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = CollectiveIdentifiersEndpoints(fake_transport).generate(request)

        assert result == expected
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == CollectiveIdentifierRoutes.GENERATE
        assert call.json == request.model_dump(mode="json")

    def test_query_sends_pagination_state(
        self,
        fake_transport: FakeTransport,
        collective_query_req: BaseFactory[spec.CollectiveIdentifiersQueryRequest],
        collective_query_resp: BaseFactory[spec.CollectiveIdentifiersQueryResponse],
    ) -> None:
        request = collective_query_req.build()
        expected = collective_query_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = CollectiveIdentifiersEndpoints(fake_transport).query(
            request,
            continuation_token="next-page",
            pageSize=25,
        )

        assert result == expected
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == CollectiveIdentifierRoutes.QUERY
        assert call.headers == {"x-continuation-token": "next-page"}
        assert call.params is not None
        assert call.params["pageSize"] == "25"

    def test_query_by_ksef_number(
        self,
        fake_transport: FakeTransport,
        collective_by_ksef_resp: BaseFactory[
            spec.CollectiveIdentifiersByKsefNumberQueryResponse
        ],
    ) -> None:
        expected = collective_by_ksef_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = CollectiveIdentifiersEndpoints(fake_transport).query_by_ksef_number(
            _KSEF_NUMBER
        )

        assert result == expected
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == CollectiveIdentifierRoutes.QUERY_BY_KSEF_NUMBER.format(
            ksefNumber=_KSEF_NUMBER
        )

    def test_list_invoices_sends_identifier_numbers_and_pagination_state(
        self,
        fake_transport: FakeTransport,
        collective_invoices_req: BaseFactory[
            spec.CollectiveIdentifierInvoicesQueryRequest
        ],
        collective_invoices_resp: BaseFactory[
            spec.CollectiveIdentifierInvoicesQueryResponse
        ],
    ) -> None:
        request = collective_invoices_req.build()
        expected = collective_invoices_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = CollectiveIdentifiersEndpoints(fake_transport).list_invoices(
            request,
            continuation_token="next-page",
            pageSize=25,
        )

        assert result == expected
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == "/collective-identifiers/invoices"
        assert call.json == request.model_dump(mode="json")
        assert call.headers == {"x-continuation-token": "next-page"}
        assert call.params is not None
        assert call.params["pageSize"] == "25"
