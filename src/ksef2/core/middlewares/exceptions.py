from typing import final, override

import httpx

from ksef2.core import protocols
from ksef2.core.middlewares.base import BaseMiddleware
from ksef2.core.response_errors import raise_for_ksef_status
from ksef2.core.types import Headers, JsonObject, QueryParamsInput


@final
class KSeFExceptionMiddleware(BaseMiddleware):
    def __init__(self, transport: protocols.Middleware) -> None:
        self._next = transport

    def _handle(self, response: httpx.Response) -> httpx.Response:
        raise_for_ksef_status(response)
        return response

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
        return self._handle(
            self._next.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json,
                content=content,
            )
        )
