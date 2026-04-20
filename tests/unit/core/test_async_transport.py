"""Tests for AsyncHttpTransport.

Covers validation contract assertions:
- VAL-CORE-002: AsyncHttpTransport wraps httpx.AsyncClient
- VAL-CORE-003: AsyncHttpTransport merges headers correctly
- VAL-CORE-011: AsyncHttpTransport manages httpx.AsyncClient lifecycle
"""

from unittest.mock import AsyncMock

import httpx

from ksef2._async.core.http import AsyncHttpTransport
from ksef2._async.core.protocols import AsyncMiddleware


class TestAsyncHttpTransportProtocol:
    """VAL-CORE-002: AsyncHttpTransport wraps httpx.AsyncClient, satisfies protocol."""

    def test_satisfies_async_middleware_protocol(self) -> None:
        """AsyncHttpTransport is an instance of AsyncMiddleware."""
        client = httpx.AsyncClient()
        transport = AsyncHttpTransport(client, {}, _owns_client=False)
        assert isinstance(transport, AsyncMiddleware)

    async def test_request_delegates_to_async_client(self) -> None:
        """AsyncHttpTransport.request() delegates to httpx.AsyncClient.request()."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        expected_response = httpx.Response(200, json={"ok": True})
        mock_client.request = AsyncMock(return_value=expected_response)

        transport = AsyncHttpTransport(mock_client, {"X-Default": "1"})
        response = await transport.request("GET", "/test")

        assert response == expected_response
        mock_client.request.assert_awaited_once()

    async def test_get_delegates_to_request(self) -> None:
        """AsyncHttpTransport.get() delegates to request() with GET method."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {})
        await transport.get("/test", params={"key": "value"})

        args, kwargs = mock_client.request.call_args
        assert args[0] == "GET"
        assert args[1] == "/test"

    async def test_post_delegates_to_request(self) -> None:
        """AsyncHttpTransport.post() delegates to request() with POST method."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {})
        await transport.post("/test", json={"data": 42})

        args, kwargs = mock_client.request.call_args
        assert args[0] == "POST"
        assert args[1] == "/test"

    async def test_delete_delegates_to_request(self) -> None:
        """AsyncHttpTransport.delete() delegates to request() with DELETE method."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {})
        await transport.delete("/test")

        args, kwargs = mock_client.request.call_args
        assert args[0] == "DELETE"
        assert args[1] == "/test"


class TestAsyncHttpTransportHeaderMerging:
    """VAL-CORE-003: AsyncHttpTransport merges headers correctly."""

    async def test_default_headers_present(self) -> None:
        """Constructor headers are included in the request."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {"X-Default": "1"})
        await transport.request("GET", "/test")

        _, kwargs = mock_client.request.call_args
        assert kwargs["headers"]["X-Default"] == "1"

    async def test_per_request_headers_merged(self) -> None:
        """Per-request headers are merged with constructor headers."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {"X-Default": "1"})
        await transport.request("GET", "/test", headers={"X-Custom": "2"})

        _, kwargs = mock_client.request.call_args
        assert kwargs["headers"]["X-Default"] == "1"
        assert kwargs["headers"]["X-Custom"] == "2"

    async def test_per_request_headers_override(self) -> None:
        """Per-request headers override constructor headers for the same key."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {"X-Default": "1"})
        await transport.request("GET", "/test", headers={"X-Default": "override"})

        _, kwargs = mock_client.request.call_args
        assert kwargs["headers"]["X-Default"] == "override"

    async def test_no_extra_headers(self) -> None:
        """When no extra headers are provided, only default headers are used."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {"X-Default": "1"})
        await transport.request("GET", "/test")

        _, kwargs = mock_client.request.call_args
        assert kwargs["headers"] == {"X-Default": "1"}

    async def test_with_headers_creates_new_transport(self) -> None:
        """with_headers() creates a new transport with merged headers."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=httpx.Response(200))

        transport = AsyncHttpTransport(mock_client, {"X-Default": "1"})
        new_transport = transport.with_headers({"X-Added": "2"})

        await new_transport.request("GET", "/test")

        _, kwargs = mock_client.request.call_args
        assert kwargs["headers"]["X-Default"] == "1"
        assert kwargs["headers"]["X-Added"] == "2"


class TestAsyncHttpTransportLifecycle:
    """VAL-CORE-011: AsyncHttpTransport manages httpx.AsyncClient lifecycle."""

    async def test_aclose_closes_internal_client(self) -> None:
        """When AsyncClient was created internally, aclose() closes it."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        transport = AsyncHttpTransport(mock_client, {}, _owns_client=True)

        await transport.aclose()

        mock_client.aclose.assert_awaited_once()

    async def test_aclose_skips_external_client(self) -> None:
        """When AsyncClient was provided externally, aclose() does NOT close it."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        transport = AsyncHttpTransport(mock_client, {}, _owns_client=False)

        await transport.aclose()

        mock_client.aclose.assert_not_awaited()

    async def test_default_owns_client_is_true(self) -> None:
        """By default, AsyncHttpTransport owns the client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        transport = AsyncHttpTransport(mock_client, {})

        await transport.aclose()

        mock_client.aclose.assert_awaited_once()
