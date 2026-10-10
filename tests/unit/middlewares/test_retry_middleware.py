from collections.abc import Mapping
from unittest.mock import patch

import httpx
import pytest

from ksef2._config import RetryConfig
from ksef2._core.exceptions import KSeFAuthError, KSeFRateLimitError
from ksef2._core.middlewares.exceptions import KSeFExceptionMiddleware
from ksef2._core.middlewares.retry import RetryMiddleware
from ksef2._core.routes import AuthRoutes, CollectiveIdentifierRoutes
from tests.unit.fakes.transport import FakeTransport


class FailingThenSucceedingTransport(FakeTransport):
    def __init__(self) -> None:
        super().__init__()
        self._attempts = 0

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: Mapping[str, object] | None = None,
        json: dict[str, object] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        self._attempts += 1
        if self._attempts == 1:
            raise httpx.ConnectError("boom")
        return super().request(
            method,
            path,
            headers=headers,
            params=params,
            json=json,
            content=content,
        )


class TestRetryMiddleware:
    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retries_get_on_retryable_status(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        transport.enqueue(status_code=200, json_body={"ok": True})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=2))

        response = middleware.get("/resource")

        assert response.status_code == 200
        assert len(transport.calls) == 2
        sleep_mock.assert_called_once()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retries_put_on_retryable_status(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        transport.enqueue(status_code=200, json_body={"ok": True})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=2))

        response = middleware.put("/resource", json={"value": "updated"})

        assert response.status_code == 200
        assert len(transport.calls) == 2
        sleep_mock.assert_called_once()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_does_not_retry_non_retryable_post(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        response = middleware.post("/sessions/ref-123/invoices", json={"foo": "bar"})

        assert response.status_code == 503
        assert len(transport.calls) == 1
        sleep_mock.assert_not_called()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_one_shot_redemption_response_is_not_retried(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        transport.enqueue(status_code=200, json_body={"unexpected": "retry"})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        response = middleware.post(AuthRoutes.REDEEM_TOKEN)

        assert response.status_code == 503
        assert len(transport.calls) == 1
        sleep_mock.assert_not_called()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_one_shot_redemption_transport_error_is_not_retried(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue_error(httpx.ReadError("redemption response lost"))
        transport.enqueue(status_code=200, json_body={"unexpected": "retry"})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        with pytest.raises(httpx.ReadError, match="redemption response lost"):
            _ = middleware.post(AuthRoutes.REDEEM_TOKEN)

        assert len(transport.calls) == 1
        sleep_mock.assert_not_called()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retries_safe_post_query_paths(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        transport.enqueue(status_code=200, json_body={"items": []})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=2))

        response = middleware.post("/invoices/query/metadata", json={"foo": "bar"})

        assert response.status_code == 200
        assert len(transport.calls) == 2
        sleep_mock.assert_called_once()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retries_collective_identifier_invoices_post(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        transport.enqueue(status_code=200, json_body={"invoices": []})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=2))

        response = middleware.post(
            CollectiveIdentifierRoutes.LIST_INVOICES,
            json={
                "collectiveIdentifierNumbers": ["1111111111-IZ202607-65ED02180000-E7"]
            },
        )

        assert response.status_code == 200
        assert len(transport.calls) == 2
        sleep_mock.assert_called_once()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retries_transport_errors_for_retryable_requests(
        self,
        sleep_mock,
    ) -> None:
        transport = FailingThenSucceedingTransport()
        transport.enqueue(status_code=200, json_body={"ok": True})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=2))

        response = middleware.get("/resource")

        assert response.status_code == 200
        assert len(transport.calls) == 1
        sleep_mock.assert_called_once()


_RATE_LIMIT_BODY = {"status": {"code": 429, "description": "Slow down.", "details": []}}
_UNAUTHORIZED_BODY = {
    "status": {"code": 401, "description": "Expired token.", "details": []}
}


class TestRetryAfterCeiling:
    """Retry-After honors its own ceiling (`max_retry_after`), not `max_delay`."""

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retry_after_under_ceiling_is_honored_exactly(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(
            status_code=429,
            json_body=_RATE_LIMIT_BODY,
            headers={"Retry-After": "30"},
        )
        transport.enqueue(status_code=200, json_body={"ok": True})
        middleware = RetryMiddleware(
            transport, RetryConfig(max_attempts=3, max_delay=4.0)
        )

        response = middleware.get("/resource")

        assert response.status_code == 200
        assert len(transport.calls) == 2
        sleep_mock.assert_called_once_with(30.0)

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retry_after_equal_to_ceiling_is_honored(self, sleep_mock) -> None:
        transport = FakeTransport()
        transport.enqueue(
            status_code=429,
            json_body=_RATE_LIMIT_BODY,
            headers={"Retry-After": "120"},
        )
        transport.enqueue(status_code=200, json_body={"ok": True})
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        response = middleware.get("/resource")

        assert response.status_code == 200
        sleep_mock.assert_called_once_with(120.0)

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_retry_after_over_ceiling_raises_immediately_with_true_value(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(
            status_code=429,
            json_body=_RATE_LIMIT_BODY,
            headers={"Retry-After": "600"},
        )
        transport.enqueue(status_code=200, json_body={"ok": True})
        middleware = KSeFExceptionMiddleware(
            RetryMiddleware(transport, RetryConfig(max_attempts=3))
        )

        with pytest.raises(KSeFRateLimitError) as exc_info:
            _ = middleware.get("/resource")

        assert exc_info.value.retry_after == 600
        assert len(transport.calls) == 1
        sleep_mock.assert_not_called()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_over_ceiling_gives_up_even_with_attempts_remaining(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        transport.enqueue(
            status_code=429,
            json_body=_RATE_LIMIT_BODY,
            headers={"Retry-After": "18000"},
        )
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=5))

        response = middleware.get("/resource")

        assert response.status_code == 429
        assert len(transport.calls) == 1
        sleep_mock.assert_not_called()

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_exponential_backoff_still_capped_by_max_delay(
        self,
        sleep_mock,
    ) -> None:
        transport = FakeTransport()
        for _ in range(5):
            transport.enqueue(status_code=503, json_body={"message": "busy"})
        middleware = RetryMiddleware(
            transport,
            RetryConfig(
                max_attempts=5, initial_delay=0.5, backoff_multiplier=2.0, max_delay=4.0
            ),
        )

        response = middleware.get("/resource")

        assert response.status_code == 503
        assert len(transport.calls) == 5
        assert [call.args[0] for call in sleep_mock.call_args_list] == [
            0.5,
            1.0,
            2.0,
            4.0,
        ]

    @patch("ksef2._core.middlewares.retry.time.sleep")
    def test_401_is_not_retried_and_raises_auth_error(self, sleep_mock) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=401, json_body=_UNAUTHORIZED_BODY, content=None)
        transport.enqueue(status_code=200, json_body={"ok": True})
        middleware = KSeFExceptionMiddleware(
            RetryMiddleware(transport, RetryConfig(max_attempts=3))
        )

        with pytest.raises(KSeFAuthError) as exc_info:
            _ = middleware.get("/resource")

        assert exc_info.value.status_code == 401
        assert len(transport.calls) == 1
        sleep_mock.assert_not_called()
