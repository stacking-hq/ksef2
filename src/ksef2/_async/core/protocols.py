from typing import Protocol, runtime_checkable

import httpx

from ksef2.core.types import Headers, JsonObject, QueryParamsInput


@runtime_checkable
class AsyncMiddleware(Protocol):
    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
    ) -> httpx.Response: ...

    async def get(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
    ) -> httpx.Response: ...

    async def post(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
    ) -> httpx.Response: ...

    async def delete(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
    ) -> httpx.Response: ...
