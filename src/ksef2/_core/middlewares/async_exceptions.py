import re
from typing import final, override

import httpx

from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.middlewares.async_base import AsyncBaseMiddleware
from ksef2._core.response_errors import raise_for_ksef_status
from ksef2._core.types import Headers, JsonObject, QueryParamsInput

_TRANSPORT_FAILED_MESSAGE = (
    "The HTTP request failed before the SDK could use a response from KSeF."
)


_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_URL = re.compile(r"https?://[^\s)]+")


def _safe_cause_message(error: Exception) -> str:
    return _URL.sub("[URL]", str(error)).split("?", 1)[0]


@final
class AsyncKSeFExceptionMiddleware(AsyncBaseMiddleware):
    """Classify failed HTTP requests and error responses as SDK exceptions.

    It is the outermost middleware of the KSeF API path, so it sees a request
    failure only after the retry middleware used its attempts up. The retry
    middleware keeps seeing the raw ``httpx`` error and only retries the failures it
    has always retried: a response the HTTP client could not decode, or a redirect
    chain it gave up on, is reported at once.
    """

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._next = transport

    def _handle(
        self, response: httpx.Response, method: str, path: str
    ) -> httpx.Response:
        raise_for_ksef_status(response, method=method, path=path)
        return response

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
        try:
            response = await self._next.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json,
                content=content,
                **kwargs,
            )
        except (httpx.RequestError, httpx.InvalidURL, httpx.StreamError) as exc:
            raise exceptions.KSeFTransportError(
                _TRANSPORT_FAILED_MESSAGE,
                method=method,
                path=path,
                cause_type=type(exc).__name__,
                cause_message=_safe_cause_message(exc),
                outcome_ambiguous=method.upper() not in _SAFE_METHODS,
            ) from exc
        return self._handle(response, method, path)
