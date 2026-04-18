from collections.abc import Mapping
from typing import final, override

import httpx

from ksef2.core import protocols
from ksef2.core.response_errors import raise_for_ksef_status
from ksef2.core.middlewares.base import BaseMiddleware


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
        headers: dict[str, str] | None = None,
        params: Mapping[str, object] | None = None,
        json: dict[str, object] | None = None,
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
