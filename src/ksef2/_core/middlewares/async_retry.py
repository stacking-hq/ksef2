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
        return method == "POST" and path in routes.RETRYABLE_POST_PATHS

    def _is_retryable_status(self, status_code: int) -> bool:
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
            return await self._next.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json,
                content=content,
            )

        last_response: httpx.Response | None = None

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
            except httpx.TransportError:
                if attempt >= self._config.max_attempts:
                    raise
                await self._sleep_for(attempt, _sleep_fn=_sleep_fn)
                continue

            last_response = response
            if (
                response.is_success
                or not self._is_retryable_status(response.status_code)
                or attempt >= self._config.max_attempts
            ):
                return response

            if self._retry_after_over_ceiling(response):
                # Retry-After exceeds the ceiling: do not park this process waiting.
                # Return the response so the exception middleware raises
                # KSeFRateLimitError with the true header value for the caller to
                # reschedule around.
                return response

            await self._sleep_for(attempt, response, _sleep_fn=_sleep_fn)

        assert last_response is not None
        return last_response
