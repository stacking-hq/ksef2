"""Tests for AsyncMiddleware protocol and AsyncFakeTransport.

Covers validation contract assertions:
- VAL-CORE-001: AsyncMiddleware protocol defines async methods
- VAL-CORE-009: All async middleware methods are coroutines
"""

import inspect
from collections.abc import Mapping
from typing import Any

import httpx
import pytest

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.async_http import AsyncHttpTransport
from ksef2.core.middlewares.async_base import AsyncBaseMiddleware
from tests.unit.fakes.transport import AsyncFakeTransport


# ---------------------------------------------------------------------------
# Minimal concrete subclass of AsyncBaseMiddleware for protocol checks
# ---------------------------------------------------------------------------


class _StubAsyncMiddleware(AsyncBaseMiddleware):
    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})


class TestAsyncMiddlewareProtocol:
    """VAL-CORE-001: AsyncMiddleware protocol is runtime-checkable with async methods."""

    def test_isinstance_async_fake_transport(self) -> None:
        """AsyncFakeTransport satisfies the AsyncMiddleware protocol."""
        transport = AsyncFakeTransport()
        assert isinstance(transport, AsyncMiddleware)

    def test_isinstance_stub_middleware(self) -> None:
        """A concrete AsyncBaseMiddleware subclass satisfies AsyncMiddleware."""
        stub = _StubAsyncMiddleware()
        assert isinstance(stub, AsyncMiddleware)

    def test_isinstance_async_http_transport(self) -> None:
        """AsyncHttpTransport satisfies the AsyncMiddleware protocol."""
        client = httpx.AsyncClient()
        transport = AsyncHttpTransport(client, {}, _owns_client=False)
        assert isinstance(transport, AsyncMiddleware)

    def test_non_matching_class_is_not_instance(self) -> None:
        """A plain object does NOT satisfy AsyncMiddleware."""
        assert not isinstance(object(), AsyncMiddleware)


class TestAsyncMiddlewareMethodsAreCoroutines:
    """VAL-CORE-009: All async middleware methods are coroutines."""

    async def test_request_returns_coroutine(self) -> None:
        """Calling request() without await returns a coroutine object."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        result = transport.request("GET", "/test")
        assert inspect.iscoroutine(result)
        # Must await to avoid RuntimeWarning
        await result

    async def test_get_returns_coroutine(self) -> None:
        """Calling get() without await returns a coroutine object."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        result = transport.get("/test")
        assert inspect.iscoroutine(result)
        await result

    async def test_post_returns_coroutine(self) -> None:
        """Calling post() without await returns a coroutine object."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        result = transport.post("/test")
        assert inspect.iscoroutine(result)
        await result

    async def test_delete_returns_coroutine(self) -> None:
        """Calling delete() without await returns a coroutine object."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        result = transport.delete("/test")
        assert inspect.iscoroutine(result)
        await result


class TestAsyncFakeTransport:
    """Tests for AsyncFakeTransport basic functionality."""

    async def test_request_records_call(self) -> None:
        """AsyncFakeTransport records all call parameters."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        await transport.request(
            "POST",
            "/test/path",
            headers={"X-Custom": "value"},
            json={"data": 42},
        )

        assert len(transport.calls) == 1
        call = transport.calls[0]
        assert call.method == "POST"
        assert call.path == "/test/path"
        assert call.headers == {"X-Custom": "value"}
        assert call.json == {"data": 42}

    async def test_get_delegates_to_request(self) -> None:
        """AsyncFakeTransport.get() delegates to request() with GET method."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        await transport.get("/path", params={"key": "value"})

        assert len(transport.calls) == 1
        assert transport.calls[0].method == "GET"
        assert transport.calls[0].path == "/path"

    async def test_post_delegates_to_request(self) -> None:
        """AsyncFakeTransport.post() delegates to request() with POST method."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        await transport.post("/path", json={"key": "value"})

        assert len(transport.calls) == 1
        assert transport.calls[0].method == "POST"
        assert transport.calls[0].json == {"key": "value"}

    async def test_delete_delegates_to_request(self) -> None:
        """AsyncFakeTransport.delete() delegates to request() with DELETE method."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})

        await transport.delete("/path")

        assert len(transport.calls) == 1
        assert transport.calls[0].method == "DELETE"

    async def test_returns_queued_response(self) -> None:
        """AsyncFakeTransport returns queued responses in FIFO order."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"first": True})
        transport.enqueue(json_body={"second": True})

        resp1 = await transport.get("/path")
        resp2 = await transport.get("/path")

        assert resp1.json() == {"first": True}
        assert resp2.json() == {"second": True}

    async def test_raises_when_no_responses_queued(self) -> None:
        """AsyncFakeTransport raises RuntimeError when no responses are queued."""
        transport = AsyncFakeTransport()

        with pytest.raises(RuntimeError, match="no more queued responses"):
            await transport.get("/path")

    async def test_enqueue_with_status_code(self) -> None:
        """AsyncFakeTransport can enqueue responses with custom status codes."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"error": "bad"}, status_code=400)

        resp = await transport.get("/path")
        assert resp.status_code == 400

    async def test_enqueue_with_content_bytes(self) -> None:
        """AsyncFakeTransport can enqueue responses with raw bytes content."""
        transport = AsyncFakeTransport()
        transport.enqueue(content=b"raw-bytes", status_code=200)

        resp = await transport.get("/path")
        assert resp.content == b"raw-bytes"

    async def test_clear_resets_state(self) -> None:
        """AsyncFakeTransport.clear() removes all recorded calls and queued responses."""
        transport = AsyncFakeTransport()
        transport.enqueue(json_body={"ok": True})
        await transport.get("/path")

        transport.clear()

        assert len(transport.calls) == 0
        assert len(transport.responses) == 0
