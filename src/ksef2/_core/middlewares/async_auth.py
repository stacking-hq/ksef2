from typing import final, override

import httpx

from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.async_token_manager import AsyncTokenManager
from ksef2._core.middlewares.async_base import AsyncBaseMiddleware
from ksef2._core.types import Headers, JsonObject, QueryParamsInput


@final
class AsyncBearerTokenMiddleware(AsyncBaseMiddleware):
    def __init__(self, transport: AsyncMiddleware, tokens: AsyncTokenManager) -> None:
        self._next = transport
        self._tokens = tokens

    def _merge(self, extra: Headers | None, token: str) -> Headers:
        headers = {"Authorization": f"Bearer {token}"}
        return headers | (extra or {})

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
        token = await self._tokens.get_access_token()
        try:
            return await self._next.request(
                method,
                path,
                headers=self._merge(headers, token),
                params=params,
                json=json,
                content=content,
                **kwargs,
            )
        except exceptions.KSeFAuthError as exc:
            if (
                exc.status_code != 401
                or isinstance(exc, exceptions.KSeFAuthenticationExpiredError)
                or not self._tokens.auto_refresh
            ):
                raise

        # A 401 means KSeF did not process the request, so replaying it once is safe.
        token = await self._tokens.refresh_rejected(token)
        return await self._next.request(
            method,
            path,
            headers=self._merge(headers, token),
            params=params,
            json=json,
            content=content,
            **kwargs,
        )
