import asyncio

from tests.unit.factories.peppol import (
    PeppolProviderFactory,
    QueryPeppolProvidersResponseFactory,
)
from tests.unit.fakes.transport import AsyncFakeTransport
from ksef2.clients.async_peppol import AsyncPeppolClient
from ksef2.core.routes import PeppolRoutes


async def _collect_async_providers(iterator):
    providers = []
    async for provider in iterator:
        providers.append(provider)
    return providers


class TestAsyncPeppolClient:
    def test_query(
        self,
        async_fake_transport: AsyncFakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        client = AsyncPeppolClient(async_fake_transport)
        expected = peppol_providers_resp.build()

        async_fake_transport.enqueue(expected.model_dump(mode="json"))
        response = asyncio.run(client.query())

        assert len(response.providers) == len(expected.peppolProviders)
        assert async_fake_transport.calls[0].method == "GET"
        assert str(async_fake_transport.calls[0].path) == PeppolRoutes.QUERY_PROVIDERS

    def test_all_multiple_pages(
        self,
        async_fake_transport: AsyncFakeTransport,
        peppol_providers_resp: QueryPeppolProvidersResponseFactory,
    ):
        client = AsyncPeppolClient(async_fake_transport)
        page1 = peppol_providers_resp.build(
            peppolProviders=[
                PeppolProviderFactory.build(id="PPL000001"),
                PeppolProviderFactory.build(id="PPL000002"),
            ],
            hasMore=True,
        )
        page2 = peppol_providers_resp.build(
            peppolProviders=[PeppolProviderFactory.build(id="PPL000003")],
            hasMore=False,
        )
        async_fake_transport.enqueue(page1.model_dump(mode="json"))
        async_fake_transport.enqueue(page2.model_dump(mode="json"))

        providers = asyncio.run(_collect_async_providers(client.all()))

        assert len(providers) == 3
