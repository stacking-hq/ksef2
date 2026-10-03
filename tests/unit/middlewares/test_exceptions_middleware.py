import pytest

import httpx

from ksef2._core import exceptions, middlewares
from tests.unit.fakes.transport import FakeTransport


class TestExceptionsMiddleware:
    @pytest.fixture
    def exceptions_middleware(self, fake_transport: FakeTransport):
        return middlewares.KSeFExceptionMiddleware(fake_transport)

    @pytest.mark.parametrize(
        "expected_exception, status_code",
        [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ],
    )
    def test_middleware_maps_to_exceptions(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
        status_code: int,
        expected_exception: type[exceptions.KSeFException],
    ):
        response_body = {"code": "ERR", "message": "boom"}

        fake_transport.enqueue(
            status_code=status_code,
            json_body=response_body,
        )

        with pytest.raises(expected_exception):
            response = exceptions_middleware.request("POST", "/whatever")

            assert response.status_code == status_code
            assert response.json() == response_body
            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert call.path == "/whatever"
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert fake_transport.responses == []

    @pytest.mark.parametrize(
        "status_code",
        [
            200,
            201,
            204,
        ],
    )
    def test_middleware_passes_requests_on_success(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
        status_code: int,
    ):
        response_body = {"result": "ok"}

        fake_transport.enqueue(
            status_code=status_code,
            json_body=response_body,
        )

        response = exceptions_middleware.request("POST", "/whatever")

        assert response.status_code == status_code
        assert response.json() == response_body
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == "/whatever"

    @pytest.mark.parametrize(
        "method",
        [
            "GET",
            "POST",
            "DELETE",
        ],
    )
    def test_different_http_methods(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
        method: str,
    ):
        fake_transport.enqueue(status_code=200, json_body={"ok": True})

        exceptions_middleware.request(method, "/resource")

        call = fake_transport.calls[0]
        assert call.method == method
        assert call.path == "/resource"

    def test_passes_headers_params_json_content(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        fake_transport.enqueue(status_code=200, json_body={"ok": True})

        exceptions_middleware.request(
            "POST",
            "/resource",
            headers={"Authorization": "Bearer token"},
            params=httpx.QueryParams({"foo": "bar"}),
            json={"key": "value"},
            content=b"raw bytes",
        )

        call = fake_transport.calls[0]
        assert call.headers == {"Authorization": "Bearer token"}
        assert call.params == httpx.QueryParams({"foo": "bar"})
        assert call.json == {"key": "value"}
        assert call.content == b"raw bytes"
