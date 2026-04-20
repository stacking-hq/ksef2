"""Tests for async middleware chain.

Covers validation contract assertions:
- VAL-CORE-004: AsyncBearerTokenMiddleware injects Authorization header
- VAL-CORE-005: AsyncRetryMiddleware retries with async sleep
- VAL-CORE-006: AsyncKSeFExceptionMiddleware converts errors
- VAL-CORE-007: AsyncClientLifecycleMiddleware rejects closed state
- VAL-CORE-008: Full async middleware chain composes correctly
"""

from unittest.mock import AsyncMock

import pytest

from ksef2.core.middlewares.async_auth import AsyncBearerTokenMiddleware
from ksef2.core.middlewares.async_retry import AsyncRetryMiddleware
from ksef2.core.middlewares.async_exceptions import AsyncKSeFExceptionMiddleware
from ksef2.core.middlewares.async_lifecycle import (
    AsyncClientLifecycleMiddleware,
    AsyncClientLifecycleState,
)
from ksef2.config import RetryConfig
from ksef2.core.exceptions import (
    KSeFApiError,
    KSeFAuthError,
    KSeFClientClosedError,
    KSeFRateLimitError,
)
from tests.unit.fakes.transport import AsyncFakeTransport


# ---------------------------------------------------------------------------
# AsyncBearerTokenMiddleware tests (VAL-CORE-004)
# ---------------------------------------------------------------------------


class TestAsyncBearerTokenMiddleware:
    """VAL-CORE-004: AsyncBearerTokenMiddleware injects Authorization header."""

    async def test_injects_authorization_header(self) -> None:
        """Bearer token middleware adds Authorization: Bearer <token>."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True})

        middleware = AsyncBearerTokenMiddleware(fake, "test-token")
        await middleware.request("GET", "/test")

        assert len(fake.calls) == 1
        assert fake.calls[0].headers is not None
        assert fake.calls[0].headers["Authorization"] == "Bearer test-token"

    async def test_merges_with_existing_headers(self) -> None:
        """Bearer token is merged with other headers passed in the call."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True})

        middleware = AsyncBearerTokenMiddleware(fake, "test-token")
        await middleware.request("GET", "/test", headers={"X-Custom": "value"})

        assert len(fake.calls) == 1
        assert fake.calls[0].headers is not None
        assert fake.calls[0].headers["Authorization"] == "Bearer test-token"
        assert fake.calls[0].headers["X-Custom"] == "value"

    async def test_awaits_next_middleware(self) -> None:
        """Bearer token middleware awaits the next middleware in the chain."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True})

        middleware = AsyncBearerTokenMiddleware(fake, "test-token")
        response = await middleware.request("GET", "/test")

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    async def test_get_delegates_to_request(self) -> None:
        """AsyncBearerTokenMiddleware.get() adds bearer header."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True})

        middleware = AsyncBearerTokenMiddleware(fake, "token-123")
        await middleware.get("/path")

        assert len(fake.calls) == 1
        assert fake.calls[0].headers is not None
        assert fake.calls[0].headers["Authorization"] == "Bearer token-123"

    async def test_post_delegates_to_request(self) -> None:
        """AsyncBearerTokenMiddleware.post() adds bearer header."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True})

        middleware = AsyncBearerTokenMiddleware(fake, "token-123")
        await middleware.post("/path", json={"data": 1})

        assert len(fake.calls) == 1
        assert fake.calls[0].headers is not None
        assert fake.calls[0].headers["Authorization"] == "Bearer token-123"
        assert fake.calls[0].json == {"data": 1}

    async def test_delete_delegates_to_request(self) -> None:
        """AsyncBearerTokenMiddleware.delete() adds bearer header."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True})

        middleware = AsyncBearerTokenMiddleware(fake, "token-123")
        await middleware.delete("/path")

        assert len(fake.calls) == 1
        assert fake.calls[0].method == "DELETE"


# ---------------------------------------------------------------------------
# AsyncRetryMiddleware tests (VAL-CORE-005)
# ---------------------------------------------------------------------------


class TestAsyncRetryMiddleware:
    """VAL-CORE-005: AsyncRetryMiddleware retries with async sleep."""

    async def test_retries_on_retryable_status(self) -> None:
        """Retries on configured retryable status codes (e.g. 503)."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"error": "unavailable"}, status_code=503)
        fake.enqueue(json_body={"error": "unavailable"}, status_code=503)
        fake.enqueue(json_body={"ok": True}, status_code=200)

        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        sleep_calls: list[float] = []
        mock_sleep = AsyncMock(side_effect=lambda s: sleep_calls.append(s))

        middleware = AsyncRetryMiddleware(fake, config)
        response = await middleware.request("GET", "/test", _sleep_fn=mock_sleep)

        assert response.status_code == 200
        assert len(fake.calls) == 3
        assert len(sleep_calls) == 2

    async def test_respects_max_attempts(self) -> None:
        """Does not exceed max_attempts even if retryable status persists."""
        fake = AsyncFakeTransport()
        for _ in range(5):
            fake.enqueue(json_body={"error": "unavailable"}, status_code=503)

        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        mock_sleep = AsyncMock()

        middleware = AsyncRetryMiddleware(fake, config)
        response = await middleware.request("GET", "/test", _sleep_fn=mock_sleep)

        assert response.status_code == 503
        assert len(fake.calls) == 3

    async def test_returns_success_immediately(self) -> None:
        """Returns immediately on success without retrying."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True}, status_code=200)

        config = RetryConfig(max_attempts=3)
        mock_sleep = AsyncMock()

        middleware = AsyncRetryMiddleware(fake, config)
        response = await middleware.request("GET", "/test", _sleep_fn=mock_sleep)

        assert response.status_code == 200
        assert len(fake.calls) == 1
        mock_sleep.assert_not_awaited()

    async def test_non_retryable_status_not_retried(self) -> None:
        """Non-retryable status codes (e.g. 400) are not retried."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"error": "bad request"}, status_code=400)

        config = RetryConfig(max_attempts=3)
        mock_sleep = AsyncMock()

        middleware = AsyncRetryMiddleware(fake, config)
        response = await middleware.request("GET", "/test", _sleep_fn=mock_sleep)

        assert response.status_code == 400
        assert len(fake.calls) == 1
        mock_sleep.assert_not_awaited()

    async def test_respects_retry_after_header(self) -> None:
        """Uses Retry-After header value for sleep delay."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body={"error": "rate limited"},
            status_code=503,
            headers={"Retry-After": "2"},
        )
        fake.enqueue(json_body={"ok": True}, status_code=200)

        config = RetryConfig(max_attempts=3, initial_delay=0.5, max_delay=10.0)
        sleep_calls: list[float] = []
        mock_sleep = AsyncMock(side_effect=lambda s: sleep_calls.append(s))

        middleware = AsyncRetryMiddleware(fake, config)
        await middleware.request("GET", "/test", _sleep_fn=mock_sleep)

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 2.0

    async def test_post_non_retryable_path_not_retried(self) -> None:
        """POST to non-retryable path is not retried."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"error": "server"}, status_code=503)

        config = RetryConfig(max_attempts=3)
        mock_sleep = AsyncMock()

        middleware = AsyncRetryMiddleware(fake, config)
        response = await middleware.request(
            "POST", "/non/retryable/path", _sleep_fn=mock_sleep
        )

        assert response.status_code == 503
        assert len(fake.calls) == 1
        mock_sleep.assert_not_awaited()

    async def test_no_retry_when_max_attempts_is_one(self) -> None:
        """No retries when max_attempts is 1."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"error": "server"}, status_code=503)

        config = RetryConfig(max_attempts=1)
        mock_sleep = AsyncMock()

        middleware = AsyncRetryMiddleware(fake, config)
        response = await middleware.request("GET", "/test", _sleep_fn=mock_sleep)

        assert response.status_code == 503
        assert len(fake.calls) == 1
        mock_sleep.assert_not_awaited()


# ---------------------------------------------------------------------------
# AsyncKSeFExceptionMiddleware tests (VAL-CORE-006)
# ---------------------------------------------------------------------------


class TestAsyncKSeFExceptionMiddleware:
    """VAL-CORE-006: AsyncKSeFExceptionMiddleware converts errors."""

    async def test_400_raises_api_error(self) -> None:
        """400 response raises KSeFApiError."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body={
                "exception": {
                    "exceptionDetailList": [
                        {
                            "exceptionCode": 21405,
                            "exceptionDescription": "Validation error",
                        }
                    ]
                }
            },
            status_code=400,
        )

        middleware = AsyncKSeFExceptionMiddleware(fake)
        with pytest.raises(KSeFApiError):
            await middleware.request("POST", "/test")

    async def test_401_raises_auth_error(self) -> None:
        """401 response raises KSeFAuthError."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body={
                "exception": {
                    "exceptionDetailList": [
                        {
                            "exceptionCode": 10000,
                            "exceptionDescription": "Unauthorized",
                        }
                    ]
                }
            },
            status_code=401,
        )

        middleware = AsyncKSeFExceptionMiddleware(fake)
        with pytest.raises(KSeFAuthError):
            await middleware.request("GET", "/test")

    async def test_403_raises_auth_error(self) -> None:
        """403 response raises KSeFAuthError."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body={
                "exception": {
                    "exceptionDetailList": [
                        {
                            "exceptionCode": 10000,
                            "exceptionDescription": "Forbidden",
                        }
                    ]
                }
            },
            status_code=403,
        )

        middleware = AsyncKSeFExceptionMiddleware(fake)
        with pytest.raises(KSeFAuthError):
            await middleware.request("GET", "/test")

    async def test_429_raises_rate_limit_error(self) -> None:
        """429 response raises KSeFRateLimitError."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body={"status": {"description": "Too many requests"}},
            status_code=429,
            headers={"Retry-After": "30"},
        )

        middleware = AsyncKSeFExceptionMiddleware(fake)
        with pytest.raises(KSeFRateLimitError) as exc_info:
            await middleware.request("GET", "/test")

        assert exc_info.value.retry_after == 30

    async def test_500_raises_api_error(self) -> None:
        """500 response raises KSeFApiError."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body={
                "exception": {
                    "exceptionDetailList": [
                        {
                            "exceptionCode": 10000,
                            "exceptionDescription": "Internal error",
                        }
                    ]
                }
            },
            status_code=500,
        )

        middleware = AsyncKSeFExceptionMiddleware(fake)
        with pytest.raises(KSeFApiError) as exc_info:
            await middleware.request("GET", "/test")

        assert exc_info.value.status_code == 500

    async def test_200_passes_through(self) -> None:
        """Successful response passes through without exception."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True}, status_code=200)

        middleware = AsyncKSeFExceptionMiddleware(fake)
        response = await middleware.request("GET", "/test")

        assert response.status_code == 200

    async def test_problem_plus_json_parsed(self) -> None:
        """application/problem+json responses are parsed correctly."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            content=b'{"status":400,"detail":"Bad request","title":"Bad Request","errors":[]}',
            status_code=400,
            headers={"content-type": "application/problem+json"},
        )

        middleware = AsyncKSeFExceptionMiddleware(fake)
        with pytest.raises(KSeFApiError):
            await middleware.request("POST", "/test")


# ---------------------------------------------------------------------------
# AsyncClientLifecycleMiddleware tests (VAL-CORE-007)
# ---------------------------------------------------------------------------


class TestAsyncClientLifecycleMiddleware:
    """VAL-CORE-007: AsyncClientLifecycleMiddleware rejects closed state."""

    async def test_rejects_request_when_closed(self) -> None:
        """When closed=True, raises KSeFClientClosedError without making request."""
        fake = AsyncFakeTransport()
        state = AsyncClientLifecycleState(closed=True)

        middleware = AsyncClientLifecycleMiddleware(fake, state)
        with pytest.raises(KSeFClientClosedError):
            await middleware.request("GET", "/test")

        # No request should have been made
        assert len(fake.calls) == 0

    async def test_forwards_request_when_open(self) -> None:
        """When closed=False, request is forwarded to next middleware."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True})
        state = AsyncClientLifecycleState(closed=False)

        middleware = AsyncClientLifecycleMiddleware(fake, state)
        response = await middleware.request("GET", "/test")

        assert response.status_code == 200
        assert len(fake.calls) == 1


# ---------------------------------------------------------------------------
# Full middleware chain composition test (VAL-CORE-008)
# ---------------------------------------------------------------------------


class TestAsyncMiddlewareChain:
    """VAL-CORE-008: Full async middleware chain composes correctly."""

    async def test_full_chain_happy_path(self) -> None:
        """Bearer token present, request goes through full chain."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"ok": True}, status_code=200)

        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        state = AsyncClientLifecycleState(closed=False)

        # Chain: Exception -> Retry -> Lifecycle -> Transport
        chain = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                AsyncClientLifecycleMiddleware(fake, state),
                config,
            )
        )

        # Wrap with bearer
        bearer = AsyncBearerTokenMiddleware(chain, "my-token")
        response = await bearer.request("GET", "/test")

        assert response.status_code == 200
        assert fake.calls[0].headers is not None
        assert fake.calls[0].headers["Authorization"] == "Bearer my-token"

    async def test_chain_rejects_closed_client(self) -> None:
        """Closed state is rejected by lifecycle middleware."""
        fake = AsyncFakeTransport()
        state = AsyncClientLifecycleState(closed=True)

        config = RetryConfig(max_attempts=3)
        chain = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                AsyncClientLifecycleMiddleware(fake, state),
                config,
            )
        )
        bearer = AsyncBearerTokenMiddleware(chain, "my-token")

        with pytest.raises(KSeFClientClosedError):
            await bearer.request("GET", "/test")

    async def test_chain_retries_on_503(self) -> None:
        """503 is retried and eventually succeeds."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"error": "unavailable"}, status_code=503)
        fake.enqueue(json_body={"ok": True}, status_code=200)

        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        state = AsyncClientLifecycleState(closed=False)
        mock_sleep = AsyncMock()

        chain = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                AsyncClientLifecycleMiddleware(fake, state),
                config,
            )
        )
        bearer = AsyncBearerTokenMiddleware(chain, "my-token")
        response = await bearer.request("GET", "/test", _sleep_fn=mock_sleep)

        assert response.status_code == 200
        assert len(fake.calls) == 2

    async def test_chain_maps_400_to_api_error(self) -> None:
        """400 response is mapped to KSeFApiError."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body={
                "exception": {
                    "exceptionDetailList": [
                        {
                            "exceptionCode": 21405,
                            "exceptionDescription": "Validation error",
                        }
                    ]
                }
            },
            status_code=400,
        )

        config = RetryConfig(max_attempts=1)
        state = AsyncClientLifecycleState(closed=False)

        chain = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                AsyncClientLifecycleMiddleware(fake, state),
                config,
            )
        )
        bearer = AsyncBearerTokenMiddleware(chain, "my-token")

        with pytest.raises(KSeFApiError):
            await bearer.request("POST", "/test")

    async def test_chain_bearer_injection_with_retry(self) -> None:
        """Bearer token is present on every retry attempt."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"error": "unavailable"}, status_code=503)
        fake.enqueue(json_body={"ok": True}, status_code=200)

        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        state = AsyncClientLifecycleState(closed=False)
        mock_sleep = AsyncMock()

        chain = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                AsyncClientLifecycleMiddleware(fake, state),
                config,
            )
        )
        bearer = AsyncBearerTokenMiddleware(chain, "my-token")
        await bearer.request("GET", "/test", _sleep_fn=mock_sleep)

        # Both calls should have the bearer token
        for call in fake.calls:
            assert call.headers is not None
            assert call.headers["Authorization"] == "Bearer my-token"
