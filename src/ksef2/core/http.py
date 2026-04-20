from typing import final, Literal, override

import httpx

from ksef2.core.middlewares.base import BaseMiddleware
from ksef2.core.types import Headers, JsonObject, QueryParamsInput

HttpMethod = Literal["POST", "GET", "DELETE"]


@final
class HttpTransport(BaseMiddleware):
    def __init__(self, client: httpx.Client, headers: Headers) -> None:
        self._client = client
        self._headers = headers

    def _merge(self, extra: Headers | None) -> Headers:
        if not extra:
            return self._headers
        return self._headers | extra

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
        return self._client.request(
            method,
            path,
            headers=self._merge(headers),
            json=json,
            content=content,
            params=params,
        )

    def with_headers(self, headers: Headers) -> "HttpTransport":
        merged_headers = self._headers | headers
        return HttpTransport(self._client, headers=merged_headers)
