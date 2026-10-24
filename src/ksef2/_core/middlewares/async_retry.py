import asyncio
from collections.abc import Awaitable, Callable
from typing import cast, final, override

import httpx

from ksef2._config import RetryConfig
from ksef2._core import routes
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.middlewares.async_base import AsyncBaseMiddleware
from ksef2._core.retry_after import parse_retry_after
from ksef2._core.types import Headers, JsonObject, QueryParamsInput

AsyncSleep = Callable[[float], Awaitable[object]]


@final
class AsyncRetryMiddleware(AsyncBaseMiddleware):
    def __init__(
        self,
        transport: AsyncMiddleware,
        config: RetryConfig,
    ) -> None:
        self._next = transport
        self._config = config

    def _is_retryable_request(self, method: str, path: str) -> bool:
        if method in {"GET", "PUT", "DELETE"}:
            return True
        return method == "POST" and (
            path in routes.RETRYABLE_POST_PATHS or self._is_send_invoice_path(path)
        )

    @staticmethod
    def _is_send_invoice_path(path: str) -> bool:
        return path.startswith("/sessions/online/") and path.endswith("/invoices")

    def _is_non_idempotent_post(self, method: str, path: str) -> bool:
        return method == "POST" and (
            self._is_send_invoice_path(path)
            or path == routes.AuthRoutes.REFRESH_TOKEN.path
        )

    def _is_retryable_status(self, method: str, path: str, status_code: int) -> bool:
        if self._is_non_idempotent_post(method, path):
            return (
                status_code == 429
                and status_code in self._config.retryable_status_codes
            )
        return status_code in self._config.retryable_status_codes

    def _parse_retry_after(self, response: httpx.Response) -> float | None:
        delay = parse_retry_after(cast(str | None, response.headers.get("Retry-After")))
        if delay is None:
            return None
        return min(delay, self._config.max_retry_after)

    def _retry_after_over_ceiling(self, response: httpx.Response) -> bool:
        delay = parse_retry_after(cast(str | None, response.headers.get("Retry-After")))
        return delay is not None and delay > self._config.max_retry_after

    def _backoff_delay(self, attempt: int) -> float:
        delay = self._config.initial_delay * (
            self._config.backoff_multiplier ** max(0, attempt - 1)
        )
        return min(delay, self._config.max_delay)

    async def _sleep_for(
        self,
        attempt: int,
        response: httpx.Response | None = None,
        *,
        _sleep_fn: AsyncSleep | None = None,
    ) -> None:
        sleep_fn = _sleep_fn or asyncio.sleep

        if response is not None:
            retry_after = self._parse_retry_after(response)
            if retry_after is not None:
                _ = await sleep_fn(retry_after)
                return

        _ = await sleep_fn(self._backoff_delay(attempt))

    @override
    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
        _sleep_fn: AsyncSleep | None = None,
    ) -> httpx.Response:
        if self._config.max_attempts <= 1 or not self._is_retryable_request(
            method, path
        ):
            response = await self._next.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json,
                content=content,
            )
            if self._retry_after_over_ceiling(response):
                response.extensions["ksef2_retry_after_exceeds_ceiling"] = True
            return response

        last_response: httpx.Response | None = None
        ambiguous_seen = False

        for attempt in range(1, self._config.max_attempts + 1):
            try:
                response = await self._next.request(
                    method,
                    path,
                    headers=headers,
                    params=params,
                    json=json,
                    content=content,
                )
            except httpx.TransportError as error:
                if self._is_non_idempotent_post(method, path):
                    raise
                ambiguous_seen = ambiguous_seen or not isinstance(
                    error, (httpx.ConnectError, httpx.ConnectTimeout)
                )
                if attempt >= self._config.max_attempts:
                    if ambiguous_seen:
                        error.__dict__["_ksef2_outcome_ambiguous"] = True
                    raise
                await self._sleep_for(attempt, _sleep_fn=_sleep_fn)
                continue

            last_response = response
            retry_after_over_ceiling = self._retry_after_over_ceiling(response)
            if retry_after_over_ceiling:
                response.extensions["ksef2_retry_after_exceeds_ceiling"] = True
            if (
                response.is_success
                or not self._is_retryable_status(method, path, response.status_code)
                or attempt >= self._config.max_attempts
                or retry_after_over_ceiling
            ):
                return response

            await self._sleep_for(attempt, response, _sleep_fn=_sleep_fn)

        assert last_response is not None
        return last_response
