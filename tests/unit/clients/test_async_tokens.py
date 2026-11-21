import asyncio
from collections.abc import AsyncIterator
import warnings

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._clients.async_tokens import AsyncTokensClient
from ksef2._core import exceptions
from ksef2._core.routes import TokenRoutes
from ksef2._domain.models import tokens
from ksef2._infra.schema.api import spec
from tests.unit.factories.tokens import (
    QueryTokensResponseItemRev2Factory,
    TokenStatusResponseRev2Factory,
    token_status_rev2,
)
from tests.unit.fakes.transport import AsyncFakeTransport
from tests.unit.support.helpers import legacy_api


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
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))

        result = asyncio.run(
            tokens_client.generate(
                permissions=["invoice_read"],
                description="Test token",
            )
        )

        assert isinstance(result.response, tokens.GenerateTokenResponse)
        assert result.reference_number == gen_resp.referenceNumber
        assert result.token == gen_resp.token
        assert len(async_fake_transport.calls) == 1
        assert async_fake_transport.calls[0].method == "POST"
        assert (
            str(async_fake_transport.calls[0].path) == TokenRoutes.GENERATE_TOKEN_REV2
        )

    @legacy_api
    def test_wait_for_activation_polls_until_active(
        self,
        async_fake_transport: AsyncFakeTransport,
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        pending_resp = TokenStatusResponseRev2Factory.build(
            status=token_status_rev2(spec.TokenStatusRev2Code.Pending)
        )
        active_resp = TokenStatusResponseRev2Factory.build(
            status=token_status_rev2(spec.TokenStatusRev2Code.Active)
        )
        async_fake_transport.enqueue(pending_resp.model_dump(mode="json"))
        async_fake_transport.enqueue(active_resp.model_dump(mode="json"))

        result = asyncio.run(
            tokens_client.wait_for_activation(
                reference_number=active_resp.referenceNumber,
                poll_interval=0.0,
            )
        )

        assert result.status == "active"
        assert len(async_fake_transport.calls) == 2

    @legacy_api
    def test_wait_for_activation_raises_on_failed_status(
        self,
        async_fake_transport: AsyncFakeTransport,
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        failed_resp = TokenStatusResponseRev2Factory.build(
            status=token_status_rev2(spec.TokenStatusRev2Code.Failed)
        )
        async_fake_transport.enqueue(failed_resp.model_dump(mode="json"))

        with pytest.raises(
            exceptions.KSeFTokenActivationFailedError, match="Token activation failed"
        ) as exc_info:
            _ = asyncio.run(
                tokens_client.wait_for_activation(
                    reference_number=failed_resp.referenceNumber,
                )
            )

        assert exc_info.value.reference_number == failed_resp.referenceNumber
        assert exc_info.value.token_status == "failed"
        assert isinstance(exc_info.value, exceptions.KSeFApiError)

    @legacy_api
    def test_activation_timeout_does_not_discard_generated_token(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        gen_resp = token_generate_resp.build()
        pending_resp = TokenStatusResponseRev2Factory.build(
            status=token_status_rev2(spec.TokenStatusRev2Code.Pending)
        )
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        async_fake_transport.enqueue(pending_resp.model_dump(mode="json"))

        generated = asyncio.run(
            tokens_client.generate(
                permissions=["invoice_read"],
                description="Test token",
            )
        )

        with pytest.raises(
            exceptions.KSeFTokenStatusTimeoutError,
            match="not active",
        ) as exc_info:
            _ = asyncio.run(
                tokens_client.wait_for_activation(
                    reference_number=generated.reference_number,
                    timeout=0.0,
                    poll_interval=0.0,
                )
            )

        assert exc_info.value.reference_number == gen_resp.referenceNumber
        assert exc_info.value.timeout == 0.0
        assert not hasattr(exc_info.value, "attempts")
        assert not hasattr(exc_info.value, "status_code")
        assert generated.token == gen_resp.token
        assert len(async_fake_transport.calls) == 2
        assert async_fake_transport.calls[1].method == "GET"

    @legacy_api
    def test_activation_transport_error_does_not_discard_generated_token(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        gen_resp = token_generate_resp.build()
        async_fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        async_fake_transport.enqueue_error(httpx.ReadError("status response lost"))

        generated = asyncio.run(
            tokens_client.generate(
                permissions=["invoice_read"],
                description="Test token",
            )
        )

        with pytest.raises(httpx.ReadError, match="status response lost"):
            _ = asyncio.run(
                tokens_client.wait_for_activation(
                    reference_number=generated.reference_number,
                )
            )

        assert generated.token == gen_resp.token
        assert len(async_fake_transport.calls) == 2
        assert async_fake_transport.calls[1].method == "GET"

    def test_list_page(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_list_rev2_resp: BaseFactory[spec.QueryTokensResponseRev2],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        expected = token_list_rev2_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        result = asyncio.run(tokens_client.list_page())

        assert isinstance(result, tokens.QueryTokensResponse)
        assert len(async_fake_transport.calls) == 1
        assert async_fake_transport.calls[0].method == "GET"
        assert str(async_fake_transport.calls[0].path) == TokenRoutes.LIST_TOKENS_REV2

    def test_list_page_does_not_warn(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_list_rev2_resp: BaseFactory[spec.QueryTokensResponseRev2],
    ) -> None:
        """Bindings fetch one page per call, so ``list_page`` stays a supported API."""
        tokens_client = AsyncTokensClient(async_fake_transport)
        async_fake_transport.enqueue(
            token_list_rev2_resp.build(continuationToken=None).model_dump(mode="json")
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            result = asyncio.run(tokens_client.list_page())

        assert isinstance(result, tokens.QueryTokensResponse)
        assert len(async_fake_transport.calls) == 1

    def test_list_all_still_warns(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_list_rev2_resp: BaseFactory[spec.QueryTokensResponseRev2],
    ) -> None:
        tokens_client = AsyncTokensClient(async_fake_transport)
        async_fake_transport.enqueue(
            token_list_rev2_resp.build(continuationToken=None).model_dump(mode="json")
        )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            pages = asyncio.run(_collect_async_pages(tokens_client.list_all()))

        assert len(pages) == 1
        assert [warning.category for warning in caught] == [DeprecationWarning]

    @legacy_api
    def test_list_all_multiple_pages(
        self,
        async_fake_transport: AsyncFakeTransport,
        token_list_rev2_resp: BaseFactory[spec.QueryTokensResponseRev2],
    ):
        tokens_client = AsyncTokensClient(async_fake_transport)
        page1 = token_list_rev2_resp.build(
            tokens=[QueryTokensResponseItemRev2Factory.build()],
            continuationToken="ct-page2",
        )
        page2 = token_list_rev2_resp.build(
            tokens=[QueryTokensResponseItemRev2Factory.build()],
            continuationToken=None,
        )
        async_fake_transport.enqueue(page1.model_dump(mode="json"))
        async_fake_transport.enqueue(page2.model_dump(mode="json"))

        pages = asyncio.run(_collect_async_pages(tokens_client.list_all()))

        assert len(pages) == 2
        assert len(async_fake_transport.calls) == 2
