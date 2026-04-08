from collections.abc import Mapping
from unittest.mock import patch

import httpx

from ksef2.config import RetryConfig
from ksef2.core.middlewares.retry import RetryMiddleware
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
    @patch("ksef2.core.middlewares.retry.time.sleep")
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

    @patch("ksef2.core.middlewares.retry.time.sleep")
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

    @patch("ksef2.core.middlewares.retry.time.sleep")
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

    @patch("ksef2.core.middlewares.retry.time.sleep")
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
