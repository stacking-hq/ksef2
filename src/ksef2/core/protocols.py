from typing import Protocol, runtime_checkable

import httpx

from ksef2.core.types import Headers, JsonObject, QueryParamsInput


@runtime_checkable
class Middleware(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
    ) -> httpx.Response: ...

    def get(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
    ) -> httpx.Response: ...

    def post(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
    ) -> httpx.Response: ...

    def delete(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
    ) -> httpx.Response: ...
