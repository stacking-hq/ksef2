"""``X-Error-Format: problem-details`` goes to the KSeF API and never to storage."""

from typing import Any

import httpx
import pytest

from ksef2 import AsyncClient, Client
from ksef2._config import Environment, TransportConfig
from ksef2._core.middlewares.async_base import AsyncBaseMiddleware
from ksef2._core.middlewares import (
    AsyncErrorFormatMiddleware,
    ErrorFormatMiddleware,
)
from tests.unit.fakes.transport import FakeTransport

HEADER = "X-Error-Format"
STORAGE_URL = "https://storage.example.net/part-1?sig=abc"


class _Recorder:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, content=b"ok")

    def sent(self, url_part: str) -> httpx.Request:
        (request,) = (r for r in self.requests if url_part in str(r.url))
        return request


class TestErrorFormatMiddleware:
    def test_adds_the_header(self) -> None:
        fake = FakeTransport()
        fake.enqueue(content=b"ok")

        _ = ErrorFormatMiddleware(fake).get("/x", headers={"X-Other": "1"})

        assert fake.calls[0].headers == {
            HEADER: "problem-details",
            "X-Other": "1",
        }

    def test_a_caller_header_wins(self) -> None:
        fake = FakeTransport()
        fake.enqueue(content=b"ok")

        _ = ErrorFormatMiddleware(fake).get("/x", headers={HEADER: "legacy"})

        assert fake.calls[0].headers == {HEADER: "legacy"}

    def test_legacy_sends_no_header(self) -> None:
        fake = FakeTransport()
        fake.enqueue(content=b"ok")

        _ = ErrorFormatMiddleware(fake, "legacy").get("/x", headers={"X-Other": "1"})

        assert fake.calls[0].headers == {"X-Other": "1"}

    async def test_async_adds_the_header(self) -> None:
        fake = FakeTransport()
        fake.enqueue(content=b"ok")

        class _AsyncInner(AsyncBaseMiddleware):
            async def request(
                self, method: str, path: str, **kwargs: Any
            ) -> httpx.Response:
                return fake.request(method, path, **kwargs)  # pyright: ignore[reportArgumentType]

        middleware = AsyncErrorFormatMiddleware(_AsyncInner())
        _ = await middleware.get("/x")

        assert fake.calls[0].headers == {HEADER: "problem-details"}


class TestClientWiring:
    def test_api_requests_carry_the_header_and_storage_transfers_do_not(self) -> None:
        recorder = _Recorder()
        client = Client(
            environment=Environment.TEST,
            http_client=httpx.Client(
                base_url=Environment.TEST.base_url,
                transport=httpx.MockTransport(recorder.handle),
            ),
        )

        _ = client._transport.get("/limits/context")  # pyright: ignore[reportPrivateUsage]
        _ = client._transfer_transport.put(  # pyright: ignore[reportPrivateUsage]
            STORAGE_URL, content=b"part"
        )

        assert recorder.sent("/limits/context").headers[HEADER] == "problem-details"
        assert HEADER not in recorder.sent("storage.example.net").headers

    async def test_async_api_requests_carry_the_header_and_storage_transfers_do_not(
        self,
    ) -> None:
        recorder = _Recorder()

        async def handler(request: httpx.Request) -> httpx.Response:
            return recorder.handle(request)

        client = AsyncClient(
            environment=Environment.TEST,
            http_client=httpx.AsyncClient(
                base_url=Environment.TEST.base_url,
                transport=httpx.MockTransport(handler),
            ),
        )

        _ = await client._transport.get("/limits/context")  # pyright: ignore[reportPrivateUsage]
        _ = await client._transfer_transport.put(  # pyright: ignore[reportPrivateUsage]
            STORAGE_URL, content=b"part"
        )

        assert recorder.sent("/limits/context").headers[HEADER] == "problem-details"
        assert HEADER not in recorder.sent("storage.example.net").headers

    @pytest.mark.parametrize(
        ("config", "expected"),
        [
            (None, "problem-details"),
            (TransportConfig(), "problem-details"),
            (TransportConfig(error_format="legacy"), None),
        ],
        ids=["default", "problem-details", "legacy"],
    )
    def test_error_format_option(
        self, config: TransportConfig | None, expected: str | None
    ) -> None:
        recorder = _Recorder()
        client = Client(
            environment=Environment.TEST,
            transport_config=config,
            http_client=httpx.Client(
                base_url=Environment.TEST.base_url,
                transport=httpx.MockTransport(recorder.handle),
            ),
        )

        _ = client._transport.get("/limits/context")  # pyright: ignore[reportPrivateUsage]
        _ = client._transfer_transport.put(  # pyright: ignore[reportPrivateUsage]
            STORAGE_URL, content=b"part"
        )

        assert recorder.sent("/limits/context").headers.get(HEADER) == expected
        assert HEADER not in recorder.sent("storage.example.net").headers

    async def test_async_legacy_sends_no_header(self) -> None:
        recorder = _Recorder()

        async def handler(request: httpx.Request) -> httpx.Response:
            return recorder.handle(request)

        client = AsyncClient(
            environment=Environment.TEST,
            transport_config=TransportConfig(error_format="legacy"),
            http_client=httpx.AsyncClient(
                base_url=Environment.TEST.base_url,
                transport=httpx.MockTransport(handler),
            ),
        )

        _ = await client._transport.get("/limits/context")  # pyright: ignore[reportPrivateUsage]
        _ = await client._transfer_transport.put(  # pyright: ignore[reportPrivateUsage]
            STORAGE_URL, content=b"part"
        )

        assert HEADER not in recorder.sent("/limits/context").headers
        assert HEADER not in recorder.sent("storage.example.net").headers
