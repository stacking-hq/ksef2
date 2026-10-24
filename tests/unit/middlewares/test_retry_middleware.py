from collections.abc import Mapping
import asyncio
from unittest.mock import patch

import httpx
import pytest

from ksef2._config import RetryConfig
from ksef2._core.exceptions import (
    KSeFAuthError,
    KSeFRateLimitError,
    KSeFTransportError,
)
from ksef2._core.middlewares.async_exceptions import AsyncKSeFExceptionMiddleware
from ksef2._core.middlewares.exceptions import KSeFExceptionMiddleware
from ksef2._core.middlewares.async_retry import AsyncRetryMiddleware
from ksef2._core.http import HttpTransport
from ksef2._core.async_http import AsyncHttpTransport
from ksef2._core.middlewares.retry import RetryMiddleware
from ksef2._core.routes import AuthRoutes, CollectiveIdentifierRoutes, InvoiceRoutes
from tests.unit.fakes.transport import AsyncFakeTransport, FakeTransport


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
    def test_invoice_send_retries_429_with_retry_after_on_custom_httpx_transport(
        self,
    ) -> None:
        requests: list[httpx.Request] = []
        delays: list[float] = []

        def _handle(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            status_code = 429 if len(requests) == 1 else 200
            return httpx.Response(
                status_code,
                headers={"Retry-After": "3"} if status_code == 429 else {},
                request=request,
            )

        with httpx.Client(
            base_url="https://ksef.mock", transport=httpx.MockTransport(_handle)
        ) as client:
            middleware = RetryMiddleware(
                HttpTransport(client, headers={}),
                RetryConfig(max_attempts=2, max_retry_after=10.0),
            )
            response = middleware.request(
                "POST",
                InvoiceRoutes.SEND.format(referenceNumber="session-ref"),
                json={"encryptedInvoice": "payload"},
                _sleep_fn=delays.append,
            )

        assert response.status_code == 200
        assert len(requests) == 2
        assert delays == [3.0]

    def test_async_invoice_send_retries_429_with_retry_after_on_custom_httpx_transport(
        self,
    ) -> None:
        requests: list[httpx.Request] = []
        delays: list[float] = []

        def _handle(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            status_code = 429 if len(requests) == 1 else 200
            return httpx.Response(
                status_code,
                headers={"Retry-After": "3"} if status_code == 429 else {},
                request=request,
            )

        async def _run() -> None:
            async with httpx.AsyncClient(
                base_url="https://ksef.mock", transport=httpx.MockTransport(_handle)
            ) as client:
                middleware = AsyncRetryMiddleware(
                    AsyncHttpTransport(client, headers={}),
                    RetryConfig(max_attempts=2, max_retry_after=10.0),
                )

                async def _sleep(delay: float) -> None:
                    delays.append(delay)

                response = await middleware.request(
                    "POST",
                    InvoiceRoutes.SEND.format(referenceNumber="session-ref"),
                    json={"encryptedInvoice": "payload"},
                    _sleep_fn=_sleep,
                )
                assert response.status_code == 200

        asyncio.run(_run())
        assert len(requests) == 2
        assert delays == [3.0]

    def test_invoice_send_does_not_retry_503(self) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        transport.enqueue(status_code=200, json_body={"unexpected": True})
        delays: list[float] = []
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        response = middleware.request(
            "POST",
            InvoiceRoutes.SEND.format(referenceNumber="session-ref"),
            json={"encryptedInvoice": "payload"},
            _sleep_fn=delays.append,
        )

        assert response.status_code == 503
        assert len(transport.calls) == 1
        assert delays == []

    def test_invoice_send_does_not_retry_transport_error(self) -> None:
        requests: list[httpx.Request] = []
        delays: list[float] = []

        def _handle(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            raise httpx.ReadError("response lost", request=request)

        with httpx.Client(
            base_url="https://ksef.mock", transport=httpx.MockTransport(_handle)
        ) as client:
            middleware = RetryMiddleware(
                HttpTransport(client, headers={}), RetryConfig(max_attempts=3)
            )
            with pytest.raises(httpx.ReadError):
                middleware.request(
                    "POST",
                    InvoiceRoutes.SEND.format(referenceNumber="session-ref"),
                    json={"encryptedInvoice": "payload"},
                    _sleep_fn=delays.append,
                )

        assert len(requests) == 1
        assert delays == []

    def test_async_invoice_send_does_not_retry_transport_error(self) -> None:
        requests: list[httpx.Request] = []
        delays: list[float] = []

        def _handle(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            raise httpx.ReadError("response lost", request=request)

        async def _run() -> None:
            async with httpx.AsyncClient(
                base_url="https://ksef.mock", transport=httpx.MockTransport(_handle)
            ) as client:
                middleware = AsyncRetryMiddleware(
                    AsyncHttpTransport(client, headers={}),
                    RetryConfig(max_attempts=3),
                )

                async def _sleep(delay: float) -> None:
                    delays.append(delay)

                with pytest.raises(httpx.ReadError):
                    await middleware.request(
                        "POST",
                        InvoiceRoutes.SEND.format(referenceNumber="session-ref"),
                        json={"encryptedInvoice": "payload"},
                        _sleep_fn=_sleep,
                    )

        asyncio.run(_run())
        assert len(requests) == 1
        assert delays == []

    def test_retry_attempt_ambiguity_is_sticky_for_sync_and_async(self) -> None:
        sync_transport = FakeTransport()
        sync_transport.enqueue_error(httpx.ReadError("first response lost"))
        sync_transport.enqueue_error(httpx.ConnectError("second connect failed"))
        sync_error_layer = KSeFExceptionMiddleware(
            RetryMiddleware(sync_transport, RetryConfig(max_attempts=2))
        )
        sync_delays: list[float] = []
        with pytest.raises(KSeFTransportError) as sync_error:
            sync_error_layer.request("PUT", "/resource", _sleep_fn=sync_delays.append)

        async_transport = AsyncFakeTransport()
        async_transport.enqueue_error(httpx.ReadError("first response lost"))
        async_transport.enqueue_error(httpx.ConnectError("second connect failed"))
        async_error_layer = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(async_transport, RetryConfig(max_attempts=2))
        )
        async_delays: list[float] = []

        async def _run() -> KSeFTransportError:
            async def _sleep(delay: float) -> None:
                async_delays.append(delay)

            with pytest.raises(KSeFTransportError) as async_error:
                await async_error_layer.request("PUT", "/resource", _sleep_fn=_sleep)
            return async_error.value

        async_error = asyncio.run(_run())
        assert sync_error.value.outcome_ambiguous is True
        assert isinstance(sync_error.value.__cause__, httpx.ConnectError)
        assert async_error.outcome_ambiguous is True
        assert isinstance(async_error.__cause__, httpx.ConnectError)
        assert sync_delays == [0.5]
        assert async_delays == [0.5]

    def test_over_ceiling_retry_after_is_marked_for_sync_and_async_pollers(
        self,
    ) -> None:
        sync_transport = FakeTransport()
        sync_transport.enqueue(status_code=429, headers={"Retry-After": "600"})
        sync_layer = KSeFExceptionMiddleware(
            RetryMiddleware(
                sync_transport,
                RetryConfig(max_attempts=3, max_retry_after=2.0),
            )
        )
        sync_delays: list[float] = []
        with pytest.raises(KSeFRateLimitError) as sync_error:
            sync_layer.request("GET", "/resource", _sleep_fn=sync_delays.append)

        async_transport = AsyncFakeTransport()
        async_transport.enqueue(status_code=429, headers={"Retry-After": "600"})
        async_layer = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                async_transport,
                RetryConfig(max_attempts=3, max_retry_after=2.0),
            )
        )
        async_delays: list[float] = []

        async def _run() -> KSeFRateLimitError:
            async def _sleep(delay: float) -> None:
                async_delays.append(delay)

            with pytest.raises(KSeFRateLimitError) as async_error:
                await async_layer.request("GET", "/resource", _sleep_fn=_sleep)
            return async_error.value

        async_error = asyncio.run(_run())
        assert sync_error.value.retry_after == 600
        assert sync_error.value.context["retry_after_exceeds_ceiling"] is True
        assert async_error.retry_after == 600
        assert async_error.context["retry_after_exceeds_ceiling"] is True
        assert sync_delays == []
        assert async_delays == []

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

    def test_refresh_token_does_not_retry_transport_error(self) -> None:
        transport = FakeTransport()
        transport.enqueue_error(httpx.ReadError("refresh response lost"))
        transport.enqueue(status_code=200, json_body={"unexpected": "retry"})
        delays: list[float] = []
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        with pytest.raises(httpx.ReadError):
            middleware.request(
                "POST", AuthRoutes.REFRESH_TOKEN, _sleep_fn=delays.append
            )

        assert len(transport.calls) == 1
        assert delays == []

    def test_refresh_token_does_not_retry_503(self) -> None:
        transport = FakeTransport()
        transport.enqueue(status_code=503, json_body={"message": "busy"})
        transport.enqueue(status_code=200, json_body={"unexpected": "retry"})
        delays: list[float] = []
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        response = middleware.request(
            "POST", AuthRoutes.REFRESH_TOKEN, _sleep_fn=delays.append
        )

        assert response.status_code == 503
        assert len(transport.calls) == 1
        assert delays == []

    def test_async_refresh_token_does_not_retry_transport_error(self) -> None:
        transport = AsyncFakeTransport()
        transport.enqueue_error(httpx.ReadError("refresh response lost"))
        transport.enqueue(status_code=200, json_body={"unexpected": "retry"})
        delays: list[float] = []
        middleware = AsyncRetryMiddleware(transport, RetryConfig(max_attempts=3))

        async def _run() -> None:
            async def _sleep(delay: float) -> None:
                delays.append(delay)

            with pytest.raises(httpx.ReadError):
                await middleware.request(
                    "POST", AuthRoutes.REFRESH_TOKEN, _sleep_fn=_sleep
                )

        asyncio.run(_run())
        assert len(transport.calls) == 1
        assert delays == []

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
    def test_repeated_retry_after_sleeps_the_ceiling_once_per_retry(
        self,
        sleep_mock,
    ) -> None:
        """One request can wait `(max_attempts - 1) * max_retry_after` in total."""
        transport = FakeTransport()
        for _ in range(3):
            transport.enqueue(
                status_code=429,
                json_body=_RATE_LIMIT_BODY,
                headers={"Retry-After": "120"},
            )
        middleware = RetryMiddleware(transport, RetryConfig(max_attempts=3))

        response = middleware.get("/resource")

        assert response.status_code == 429
        assert len(transport.calls) == 3
        assert [c.args[0] for c in sleep_mock.call_args_list] == [120.0, 120.0]

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
