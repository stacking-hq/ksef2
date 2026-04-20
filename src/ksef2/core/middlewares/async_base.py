import abc

import httpx

from ksef2.core.types import Headers, JsonObject, QueryParamsInput


class AsyncBaseMiddleware(abc.ABC):
    @abc.abstractmethod
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
    ) -> httpx.Response:
        return await self.request("GET", path, headers=headers, params=params)

    async def post(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        return await self.request(
            "POST",
            path,
            headers=headers,
            json=json,
            params=params,
            content=content,
        )

    async def delete(
        self,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
    ) -> httpx.Response:
        return await self.request("DELETE", path, headers=headers, params=params)
