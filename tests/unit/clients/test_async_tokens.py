import asyncio
from collections.abc import AsyncIterator

import pytest
from polyfactory import BaseFactory

from ksef2.clients.async_tokens import AsyncTokensClient
from ksef2.core import exceptions
from ksef2.core.routes import TokenRoutes
from ksef2.domain.models import tokens
from ksef2.infra.schema.api import spec
from tests.unit.factories.tokens import (
    QueryTokensResponseItemFactory,
    TokenStatusResponseFactory,
)
from tests.unit.fakes.transport import AsyncFakeTransport


async def _collect_async_pages(
    iterator: AsyncIterator[tokens.QueryTokensResponse],
) -> list[tokens.QueryTokensResponse]:
    pages: list[tokens.QueryTokensResponse] = []
    async for item in iterator:
        pages.append(item)
    return pages


class TestAsyncTokensClient:
    def test_initialization(self, async_fake_transport: AsyncFakeTransport):
        assert AsyncTokensClient(async_fake_transport) is not None

    def test_generate(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        gen_resp = token_generate_resp.build()
        status_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Active
        )
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        async_fake_transport.enqueue(status_resp.model_dump(mode="json"))

        result = asyncio.run(
            tokens_client.generate(
                permissions=["invoice_read"],
                description="Test token",
            )
        )

        assert isinstance(result, tokens.GenerateTokenResponse)
        assert result.reference_number == gen_resp.referenceNumber
        assert result.token == gen_resp.token
        assert len(async_fake_transport.calls) == 2
        assert async_fake_transport.calls[0].method == "POST"
        assert str(async_fake_transport.calls[0].path) == TokenRoutes.GENERATE_TOKEN

    def test_generate_polls_until_active(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        gen_resp = token_generate_resp.build()
        pending_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Pending
        )
        active_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Active
        )
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        async_fake_transport.enqueue(pending_resp.model_dump(mode="json"))
        async_fake_transport.enqueue(active_resp.model_dump(mode="json"))

        result = asyncio.run(
            tokens_client.generate(
                permissions=["invoice_read"],
                description="Test token",
                poll_interval=0.0,
            )
        )

        assert isinstance(result, tokens.GenerateTokenResponse)
        assert len(async_fake_transport.calls) == 3

    def test_generate_raises_on_failed_status(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        gen_resp = token_generate_resp.build()
        failed_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Failed
        )
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        async_fake_transport.enqueue(failed_resp.model_dump(mode="json"))

        with pytest.raises(exceptions.KSeFApiError, match="Token activation failed"):
            _ = asyncio.run(
                tokens_client.generate(
                    permissions=["invoice_read"],
                    description="Test token",
                )
            )

    def test_generate_raises_on_timeout(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        gen_resp = token_generate_resp.build()
        pending_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Pending
        )
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        for _ in range(3):
            async_fake_transport.enqueue(pending_resp.model_dump(mode="json"))

        with pytest.raises(exceptions.KSeFApiError, match="polling timed out"):
            _ = asyncio.run(
                tokens_client.generate(
                    permissions=["invoice_read"],
                    description="Test token",
                    poll_interval=0.0,
                    max_poll_attempts=3,
                )
            )

    def test_generate_zero_max_poll_attempts_does_not_poll_status(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        gen_resp = token_generate_resp.build()
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))

        with pytest.raises(exceptions.KSeFApiError, match="polling timed out"):
            _ = asyncio.run(
                tokens_client.generate(
                    permissions=["invoice_read"],
                    description="Test token",
                    poll_interval=0.0,
                    max_poll_attempts=0,
                )
            )

        assert len(async_fake_transport.calls) == 1
        assert async_fake_transport.calls[0].method == "POST"

    def test_list_page(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_list_resp: BaseFactory[spec.QueryTokensResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        expected = token_list_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        result = asyncio.run(tokens_client.list_page())

        assert isinstance(result, tokens.QueryTokensResponse)
        assert len(async_fake_transport.calls) == 1
        assert async_fake_transport.calls[0].method == "GET"
        assert str(async_fake_transport.calls[0].path) == TokenRoutes.LIST_TOKENS

    def test_list_all_multiple_pages(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_list_resp: BaseFactory[spec.QueryTokensResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        page1 = token_list_resp.build(
            tokens=[QueryTokensResponseItemFactory.build()],
            continuationToken="ct-page2",
        )
        page2 = token_list_resp.build(
            tokens=[QueryTokensResponseItemFactory.build()],
            continuationToken=None,
        )
        async_fake_transport.enqueue(page1.model_dump(mode="json"))
        async_fake_transport.enqueue(page2.model_dump(mode="json"))

        pages = asyncio.run(_collect_async_pages(tokens_client.list_all()))

        assert len(pages) == 2
        assert len(async_fake_transport.calls) == 2
