from dataclasses import dataclass
from typing import final, override

import httpx

from ksef2.core import exceptions, protocols
from ksef2.core.middlewares.base import BaseMiddleware
from ksef2.core.types import Headers, JsonObject, QueryParamsInput


@dataclass(slots=True)
class ClientLifecycleState:
    closed: bool = False


@final
class ClientLifecycleMiddleware(BaseMiddleware):
    def __init__(
        self,
        transport: protocols.Middleware,
        state: ClientLifecycleState,
    ) -> None:
        self._next = transport
        self._state = state

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
        if self._state.closed:
            raise exceptions.KSeFClientClosedError("Client is closed.")

        return self._next.request(
            method,
            path,
            headers=headers,
            params=params,
            json=json,
            content=content,
        )
