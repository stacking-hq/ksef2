import time
from typing import final, override

import httpx

from ksef2.config import RetryConfig
from ksef2.core import protocols, routes
from ksef2.core.middlewares.base import BaseMiddleware
from ksef2.core.types import Headers, JsonObject, QueryParamsInput


@final
class RetryMiddleware(BaseMiddleware):
    def __init__(
        self,
        transport: protocols.Middleware,
        config: RetryConfig,
    ) -> None:
        self._next = transport
        self._config = config

    def _is_retryable_request(self, method: str, path: str) -> bool:
        if method in {"GET", "DELETE"}:
            return True
        return method == "POST" and path in routes.RETRYABLE_POST_PATHS

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code in self._config.retryable_status_codes

    def _parse_retry_after(self, response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        if value is None:
            return None

        try:
            delay = float(value)
        except (TypeError, ValueError):
            return None

        return max(0.0, min(delay, self._config.max_delay))

    def _backoff_delay(self, attempt: int) -> float:
        delay = self._config.initial_delay * (
            self._config.backoff_multiplier ** max(0, attempt - 1)
        )
        return min(delay, self._config.max_delay)

    def _sleep_for(self, attempt: int, response: httpx.Response | None = None) -> None:
        if response is not None:
            retry_after = self._parse_retry_after(response)
            if retry_after is not None:
                time.sleep(retry_after)
                return

        time.sleep(self._backoff_delay(attempt))

    @override
    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        if self._config.max_attempts <= 1 or not self._is_retryable_request(
            method, path
        ):
            return self._next.request(
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
                response = self._next.request(
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
                self._sleep_for(attempt)
                continue

            last_response = response
            if (
                response.is_success
                or not self._is_retryable_status(response.status_code)
                or attempt >= self._config.max_attempts
            ):
                return response

            self._sleep_for(attempt, response)

        assert last_response is not None
        return last_response
