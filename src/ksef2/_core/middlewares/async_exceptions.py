from typing import cast, final, override

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


def _transport_error_details(
    method: str, path: str, error: Exception
) -> tuple[bool, str | None]:
    if method.upper() in _SAFE_METHODS:
        return False, None
    prior_attempt_ambiguous = cast(
        bool, error.__dict__.get("_ksef2_outcome_ambiguous", False)
    )
    is_connect_failure = isinstance(error, (httpx.ConnectError, httpx.ConnectTimeout))
    if is_connect_failure and not prior_attempt_ambiguous:
        return False, None
    if (
        method.upper() == "POST"
        and path.startswith("/sessions/online/")
        and path.endswith("/invoices")
    ):
        return True, "Check `session.list_invoices()` before resending the invoice."
    return True, "The request may have reached KSeF. Check its status before retrying."


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
        try:
            raise_for_ksef_status(response, method=method, path=path)
        except exceptions.KSeFRateLimitError as error:
            if response.extensions.get("ksef2_retry_after_exceeds_ceiling") is True:
                error.context["retry_after_exceeds_ceiling"] = True
            raise
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
            outcome_ambiguous, hint = _transport_error_details(method, path, exc)
            raise exceptions.KSeFTransportError(
                _TRANSPORT_FAILED_MESSAGE,
                hint=hint,
                method=method,
                path=path,
                outcome_ambiguous=outcome_ambiguous,
            ) from exc
        return self._handle(response, method, path)
