from typing import final, override

import httpx

from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.headers import KSeFHeaders
from ksef2._core.middlewares.async_base import AsyncBaseMiddleware
from ksef2._core.types import Headers, JsonObject, QueryParamsInput


@final
class AsyncErrorFormatMiddleware(AsyncBaseMiddleware):
    """Ask KSeF to return 400 and 429 errors as ``application/problem+json``.

    It sits on the KSeF API path only. Presigned storage URLs are reached through
    the transfer transport, which does not pass through it.
    """

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._next = transport

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
        **kwargs: object,
    ) -> httpx.Response:
        return await self._next.request(
            method,
            path,
            headers=KSeFHeaders.problem_details() | (headers or {}),
            params=params,
            json=json,
            content=content,
            **kwargs,
        )
