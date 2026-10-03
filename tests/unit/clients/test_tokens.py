import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._clients.tokens import TokensClient
from ksef2._core import exceptions
from ksef2._core.routes import TokenRoutes
from ksef2._domain.models import tokens
from ksef2._infra.schema.api import spec
from tests.unit.factories.tokens import (
    QueryTokensResponseItemFactory,
    TokenStatusResponseFactory,
)
from tests.unit.fakes.transport import FakeTransport


class TestTokensClient:
    def test_initialization(self, tokens_client: TokensClient):
        assert tokens_client is not None

    def test_generate(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        gen_resp = token_generate_resp.build()
        fake_transport.enqueue(gen_resp.model_dump(mode="json"))

        result = tokens_client.generate(
            permissions=["invoice_read"],
            description="Test token",
        )

        assert isinstance(result, tokens.GenerateTokenResponse)
        assert result.reference_number == gen_resp.referenceNumber
        assert result.token == gen_resp.token
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == TokenRoutes.GENERATE_TOKEN

    def test_wait_for_activation_polls_until_active(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
    ):
        pending_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Pending
        )
        active_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Active
        )
        fake_transport.enqueue(pending_resp.model_dump(mode="json"))
        fake_transport.enqueue(active_resp.model_dump(mode="json"))

        result = tokens_client.wait_for_activation(
            reference_number=active_resp.referenceNumber,
            poll_interval=0.0,
        )

        assert result.status == "active"
        assert len(fake_transport.calls) == 2

    def test_wait_for_activation_raises_on_failed_status(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
    ):
        failed_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Failed
        )
        fake_transport.enqueue(failed_resp.model_dump(mode="json"))

        with pytest.raises(exceptions.KSeFApiError, match="Token activation failed"):
            _ = tokens_client.wait_for_activation(
                reference_number=failed_resp.referenceNumber,
            )

    def test_activation_timeout_does_not_discard_generated_token(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        gen_resp = token_generate_resp.build()
        pending_resp = TokenStatusResponseFactory.build(
            status=spec.AuthenticationTokenStatus.Pending
        )
        fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        fake_transport.enqueue(pending_resp.model_dump(mode="json"))

        generated = tokens_client.generate(
            permissions=["invoice_read"],
            description="Test token",
        )

        with pytest.raises(
            exceptions.KSeFTokenStatusTimeoutError,
            match="not active",
        ) as exc_info:
            _ = tokens_client.wait_for_activation(
                reference_number=generated.reference_number,
                timeout=0.0,
                poll_interval=0.0,
            )

        assert exc_info.value.reference_number == gen_resp.referenceNumber
        assert exc_info.value.timeout == 0.0
        assert not hasattr(exc_info.value, "attempts")
        assert not hasattr(exc_info.value, "status_code")
        assert generated.token == gen_resp.token
        assert len(fake_transport.calls) == 2
        assert fake_transport.calls[1].method == "GET"

    def test_activation_transport_error_does_not_discard_generated_token(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ):
        gen_resp = token_generate_resp.build()
        fake_transport.enqueue(gen_resp.model_dump(mode="json"))
        fake_transport.enqueue_error(httpx.ReadError("status response lost"))

        generated = tokens_client.generate(
            permissions=["invoice_read"],
            description="Test token",
        )

        with pytest.raises(httpx.ReadError, match="status response lost"):
            _ = tokens_client.wait_for_activation(
                reference_number=generated.reference_number,
            )

        assert generated.token == gen_resp.token
        assert len(fake_transport.calls) == 2
        assert fake_transport.calls[1].method == "GET"

    def test_list_page(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_list_resp: BaseFactory[spec.QueryTokensResponse],
    ):
        expected = token_list_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = tokens_client.list_page()

        assert isinstance(result, tokens.QueryTokensResponse)
        assert len(result.tokens) == len(expected.tokens)
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == TokenRoutes.LIST_TOKENS

    def test_list_page_with_continuation_token(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_list_resp: BaseFactory[spec.QueryTokensResponse],
    ):
        expected = token_list_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = tokens_client.list_page(continuation_token="ct-abc")

        assert isinstance(result, tokens.QueryTokensResponse)
        call = fake_transport.calls[0]
        assert call.headers is not None
        assert call.headers["x-continuation-token"] == "ct-abc"

    def test_list_all_single_page(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_list_resp: BaseFactory[spec.QueryTokensResponse],
    ):
        expected = token_list_resp.build(continuationToken=None)
        fake_transport.enqueue(expected.model_dump(mode="json"))

        pages = list(tokens_client.list_all())

        assert len(pages) == 1
        assert len(fake_transport.calls) == 1

    def test_list_all_multiple_pages(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_list_resp: BaseFactory[spec.QueryTokensResponse],
    ):
        page1 = token_list_resp.build(
            tokens=[QueryTokensResponseItemFactory.build()],
            continuationToken="ct-page2",
        )
        page2 = token_list_resp.build(
            tokens=[QueryTokensResponseItemFactory.build()],
            continuationToken=None,
        )
        fake_transport.enqueue(page1.model_dump(mode="json"))
        fake_transport.enqueue(page2.model_dump(mode="json"))

        pages = list(tokens_client.list_all())

        assert len(pages) == 2
        assert len(fake_transport.calls) == 2

    def test_status(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
        token_status_resp: BaseFactory[spec.TokenStatusResponse],
    ):
        expected = token_status_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = tokens_client.status(reference_number="ref-123")

        assert isinstance(result, tokens.TokenStatusResponse)
        assert result.reference_number == expected.referenceNumber
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert "ref-123" in str(call.path)

    def test_revoke(
        self,
        tokens_client: TokensClient,
        fake_transport: FakeTransport,
    ):
        fake_transport.enqueue()

        tokens_client.revoke(reference_number="ref-123")

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert "ref-123" in str(call.path)
