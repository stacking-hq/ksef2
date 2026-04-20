from typing import final, Literal, override

import httpx

from ksef2._async.core.middlewares.base import AsyncBaseMiddleware
from ksef2.core.types import Headers, JsonObject, QueryParamsInput

HttpMethod = Literal["POST", "GET", "DELETE"]


@final
class AsyncHttpTransport(AsyncBaseMiddleware):
    def __init__(
        self,
        client: httpx.AsyncClient,
        headers: Headers,
        *,
        _owns_client: bool = True,
    ) -> None:
        self._client = client
        self._headers = headers
        self._owns_client = _owns_client

    def _merge(self, extra: Headers | None) -> Headers:
        if not extra:
            return self._headers
        return self._headers | extra

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
    ) -> httpx.Response:
        return await self._client.request(
            method,
            path,
            headers=self._merge(headers),
            json=json,
            content=content,
            params=params,
        )

    async def aclose(self) -> None:
        """Close the internal AsyncClient if it was created internally."""
        if self._owns_client:
            await self._client.aclose()

    def with_headers(self, headers: Headers) -> "AsyncHttpTransport":
        merged_headers = self._headers | headers
        return AsyncHttpTransport(
            self._client, headers=merged_headers, _owns_client=self._owns_client
        )
