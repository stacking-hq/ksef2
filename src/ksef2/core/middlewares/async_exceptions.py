from typing import final, override

import httpx

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.middlewares.async_base import AsyncBaseMiddleware
from ksef2.core.response_errors import raise_for_ksef_status
from ksef2.core.types import Headers, JsonObject, QueryParamsInput


@final
class AsyncKSeFExceptionMiddleware(AsyncBaseMiddleware):
    def __init__(self, transport: AsyncMiddleware) -> None:
        self._next = transport

    def _handle(self, response: httpx.Response) -> httpx.Response:
        raise_for_ksef_status(response)
        return response

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
        return self._handle(
            await self._next.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json,
                content=content,
                **kwargs,
            )
        )
