from typing import final

import httpx

from ksef2._async.core.middlewares.base import AsyncBaseMiddleware
from ksef2._async.core.protocols import AsyncMiddleware
from ksef2.core.types import Headers, JsonObject, QueryParamsInput


@final
class AsyncBearerTokenMiddleware(AsyncBaseMiddleware):
    def __init__(self, transport: AsyncMiddleware, token: str) -> None:
        self._next = transport
        self._token = token

    def _merge(self, extra: Headers | None) -> Headers:
        headers = {"Authorization": f"Bearer {self._token}"}
        return headers | (extra or {})

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
            headers=self._merge(headers),
            params=params,
            json=json,
            content=content,
            **kwargs,
        )
