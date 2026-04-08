from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any

import httpx

from ksef2.core import protocols


@dataclass
class RecordedCall:
    method: str
    path: str
    headers: dict[str, str] | None
    params: httpx.QueryParams | None
    json: dict[str, Any] | None
    content: bytes | None = None


@dataclass()
class FakeTransport(protocols.Middleware):
    calls: list[RecordedCall] = field(default_factory=list)
    responses: list[httpx.Response] = field(default_factory=list)

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        self.calls.append(
            RecordedCall(
                method=method,
                path=path,
                headers=headers,
                params=httpx.QueryParams(params) if params is not None else None,
                json=json,
                content=content,
            )
        )

        return self._next_response()

    def get(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        return self.request("GET", path, headers=headers, params=params)

    def post(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        return self.request(
            "POST", path, headers=headers, json=json, params=params, content=content
        )

    def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        return self.request("DELETE", path, headers=headers, params=params)

    def enqueue(
        self,
        json_body: Any | None = None,
        status_code: int = 200,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if content is not None:
            resp = httpx.Response(
                status_code=status_code, content=content, headers=headers
            )
        else:
            resp = httpx.Response(
                status_code=status_code, json=json_body, headers=headers
            )
        self.responses.append(resp)

    def clear(self) -> None:
        self.calls.clear()
        self.responses.clear()

    def _next_response(self) -> httpx.Response:
        if not self.responses:
            raise RuntimeError("FakeTransport: no more queued responses")
        return self.responses.pop(0)
