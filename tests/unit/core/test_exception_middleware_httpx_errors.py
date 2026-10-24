"""``httpx`` failures outside ``RequestError`` still reach callers as SDK errors."""

import httpx
import pytest

from ksef2 import KSeFTransportError
from ksef2._core.middlewares.async_exceptions import AsyncKSeFExceptionMiddleware
from ksef2._core.middlewares.exceptions import KSeFExceptionMiddleware
from tests.unit.fakes.transport import AsyncFakeTransport, FakeTransport
from tests.unit.support.flavors import Flavor

_FAILURES: list[httpx.RequestError | httpx.InvalidURL | httpx.StreamError] = [
    httpx.InvalidURL("Invalid non-printable ASCII character in URL"),
    httpx.StreamConsumed(),
    httpx.ConnectError("connection refused"),
]


@pytest.mark.parametrize("failure", _FAILURES, ids=lambda f: type(f).__name__)
def test_middleware_wraps_every_httpx_failure(
    flavor: Flavor,
    failure: httpx.RequestError | httpx.InvalidURL | httpx.StreamError,
) -> None:
    flavor.transport.enqueue_error(failure)
    if flavor.is_async:
        assert isinstance(flavor.transport, AsyncFakeTransport)
        middleware = AsyncKSeFExceptionMiddleware(flavor.transport)
    else:
        assert isinstance(flavor.transport, FakeTransport)
        middleware = KSeFExceptionMiddleware(flavor.transport)

    with pytest.raises(KSeFTransportError) as caught:
        _ = flavor.run(middleware.request("GET", "/invoices/query"))

    assert caught.value.__cause__ is failure
    assert caught.value.method == "GET"
    assert caught.value.path == "/invoices/query"
