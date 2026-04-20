import asyncio
from typing import Any, final, override

import httpx

from ksef2._async.core.protocols import AsyncMiddleware
from ksef2._async.core.middlewares.base import AsyncBaseMiddleware
from ksef2.config import RetryConfig
from ksef2.core import routes
from ksef2.core.types import Headers, JsonObject, QueryParamsInput

_RETRYABLE_POST_PATHS = frozenset(
    {
        routes.AuthRoutes.CHALLENGE,
        routes.AuthRoutes.REDEEM_TOKEN,
        routes.AuthRoutes.REFRESH_TOKEN,
        routes.InvoiceRoutes.QUERY_METADATA,
        routes.CertificateRoutes.QUERY,
        routes.CertificateRoutes.RETRIEVE,
        routes.QueryPermissionsRoutes.QUERY_PERSONAL_GRANTS,
        routes.QueryPermissionsRoutes.QUERY_AUTHORIZATIONS_GRANTS,
        routes.QueryPermissionsRoutes.QUERY_EU_ENTITIES_GRANTS,
        routes.QueryPermissionsRoutes.QUERY_PERSONS_GRANTS,
        routes.QueryPermissionsRoutes.QUERY_SUBORDINATE_ENTITIES_ROLES,
        routes.QueryPermissionsRoutes.QUERY_SUBUNITS_GRANTS,
    }
)


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
        if method in {"GET", "DELETE"}:
            return True
        return method == "POST" and path in _RETRYABLE_POST_PATHS

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

    async def _sleep_for(
        self,
        attempt: int,
        response: httpx.Response | None = None,
        *,
        _sleep_fn: Any = None,
    ) -> None:
        sleep_fn = _sleep_fn or asyncio.sleep

        if response is not None:
            retry_after = self._parse_retry_after(response)
            if retry_after is not None:
                await sleep_fn(retry_after)
                return

        await sleep_fn(self._backoff_delay(attempt))

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
        _sleep_fn: Any = None,
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

            await self._sleep_for(attempt, response, _sleep_fn=_sleep_fn)

        assert last_response is not None
        return last_response
