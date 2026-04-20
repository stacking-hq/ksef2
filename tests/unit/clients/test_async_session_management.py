import asyncio

from polyfactory import BaseFactory

from ksef2.clients.async_session_management import AsyncSessionManagementClient
from ksef2.domain.models.auth import AuthenticationSessionsResponse
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport


async def _collect_pages(iterator):
    pages = []
    async for page in iterator:
        pages.append(page)
    return pages


class TestAsyncSessionManagementClient:
    def test_query(
        self,
        async_fake_transport: AsyncFakeTransport,
        auth_list_resp: BaseFactory[spec.AuthenticationListResponse],
    ) -> None:
        client = AsyncSessionManagementClient(async_fake_transport)
        async_fake_transport.enqueue(
            auth_list_resp.build(continuationToken=None).model_dump(mode="json")
        )

        result = asyncio.run(client.query())

        assert isinstance(result, AuthenticationSessionsResponse)
        assert async_fake_transport.calls[0].method == "GET"

    def test_all(
        self,
        async_fake_transport: AsyncFakeTransport,
        auth_list_resp: BaseFactory[spec.AuthenticationListResponse],
    ) -> None:
        client = AsyncSessionManagementClient(async_fake_transport)
        async_fake_transport.enqueue(
            auth_list_resp.build(continuationToken="next-token").model_dump(mode="json")
        )
        async_fake_transport.enqueue(
            auth_list_resp.build(continuationToken=None).model_dump(mode="json")
        )

        results = asyncio.run(_collect_pages(client.all()))

        assert len(results) == 2
