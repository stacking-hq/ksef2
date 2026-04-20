import asyncio

import pytest
from polyfactory import BaseFactory

from ksef2.clients.async_invoice_sessions import AsyncInvoiceSessionsClient
from ksef2.domain.models.session import ListSessionsResponse
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport


async def _collect_pages(iterator):
    pages = []
    async for page in iterator:
        pages.append(page)
    return pages


class TestAsyncInvoiceSessionsClient:
    def test_query(
        self,
        async_fake_transport: AsyncFakeTransport,
        session_list_resp: BaseFactory[spec.SessionsQueryResponse],
    ) -> None:
        client = AsyncInvoiceSessionsClient(async_fake_transport)
        response = session_list_resp.build(continuationToken=None)
        async_fake_transport.enqueue(response.model_dump(mode="json"))

        result = asyncio.run(client.query(session_type="online"))

        assert isinstance(result, ListSessionsResponse)
        assert async_fake_transport.calls[0].method == "GET"

    def test_all(
        self,
        async_fake_transport: AsyncFakeTransport,
        session_list_resp: BaseFactory[spec.SessionsQueryResponse],
    ) -> None:
        client = AsyncInvoiceSessionsClient(async_fake_transport)
        async_fake_transport.enqueue(
            session_list_resp.build(continuationToken="next-token").model_dump(
                mode="json"
            )
        )
        async_fake_transport.enqueue(
            session_list_resp.build(continuationToken=None).model_dump(mode="json")
        )

        results = asyncio.run(_collect_pages(client.all(session_type="online")))

        assert len(results) == 2

    def test_query_rejects_invalid_session_type(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        client = AsyncInvoiceSessionsClient(async_fake_transport)
        with pytest.raises(ValueError, match="Invalid session type"):
            asyncio.run(client.query(session_type="invalid"))  # type: ignore[arg-type]
