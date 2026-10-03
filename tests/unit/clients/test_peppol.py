from ksef2._clients.peppol import PeppolClient
from ksef2._core.routes import PeppolRoutes
from tests.unit.factories.peppol import (
    PeppolProviderFactory,
    QueryPeppolProvidersResponseFactory,
)
from tests.unit.fakes.transport import FakeTransport
from tests.unit.helpers import legacy_api


class TestPeppolClient:
    def test_initialization(self, peppol_client: PeppolClient):
        assert peppol_client is not None

    @legacy_api
    def test_query(
        self,
        peppol_client: PeppolClient,
        fake_transport: FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        expected = peppol_providers_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = peppol_client.query()

        assert response is not None
        assert len(response.providers) == len(expected.peppolProviders)
        assert response.has_more == expected.hasMore

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == PeppolRoutes.QUERY_PROVIDERS

    @legacy_api
    def test_query_with_pagination(
        self,
        peppol_client: PeppolClient,
        fake_transport: FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        expected = peppol_providers_resp.build(hasMore=False)
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = peppol_client.query()

        assert response is not None

    @legacy_api
    def test_all_single_page(
        self,
        peppol_client: PeppolClient,
        fake_transport: FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        expected = peppol_providers_resp.build(peppolProviders=[], hasMore=False)
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        providers = list(peppol_client.all())

        assert len(providers) == 0

    @legacy_api
    def test_all_multiple_pages(
        self,
        peppol_client: PeppolClient,
        fake_transport: FakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        page1 = peppol_providers_resp.build(
            peppolProviders=[
                PeppolProviderFactory.build(id="PPL000001"),
                PeppolProviderFactory.build(id="PPL000002"),
            ],
            hasMore=True,
        )
        page2 = peppol_providers_resp.build(
            peppolProviders=[
                PeppolProviderFactory.build(id="PPL000003"),
            ],
            hasMore=False,
        )

        fake_transport.enqueue(page1.model_dump(mode="json"))
        fake_transport.enqueue(page2.model_dump(mode="json"))

        providers = list(peppol_client.all())

        assert len(providers) == 3
        assert providers[0].id == "PPL000001"
        assert providers[1].id == "PPL000002"
        assert providers[2].id == "PPL000003"
        assert len(fake_transport.calls) == 2
