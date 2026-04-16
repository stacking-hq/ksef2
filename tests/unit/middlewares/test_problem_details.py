"""Tests for ProblemDetails (application/problem+json) error handling."""

import pytest

import httpx

from ksef2.core import exceptions, middlewares
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport

_CONTENT_TYPE_PROBLEM = "application/problem+json"


def _make_problem_response(
    status_code: int,
    body: dict,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    merged_headers = {"content-type": _CONTENT_TYPE_PROBLEM}
    if headers:
        merged_headers.update(headers)
    return httpx.Response(status_code=status_code, json=body, headers=merged_headers)


class TestProblemDetailsMiddleware:
    @pytest.fixture
    def exceptions_middleware(self, fake_transport: FakeTransport):
        return middlewares.KSeFExceptionMiddleware(fake_transport)

    def test_400_problem_details(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        body = {
            "title": "Bad Request",
            "status": 400,
            "instance": "https://ksef.mf.gov.pl/errors/123",
            "detail": "Invalid invoice data",
            "errors": [
                {
                    "code": 100,
                    "description": "Missing field",
                    "details": ["invoiceNumber is required"],
                },
                {"code": 200, "description": "Bad format", "details": None},
            ],
            "timestamp": "2026-04-16T12:00:00Z",
            "traceId": "abc-123",
        }
        fake_transport.responses.append(_make_problem_response(400, body))

        with pytest.raises(exceptions.KSeFApiError) as exc_info:
            exceptions_middleware.request("POST", "/invoice")

        err = exc_info.value
        assert err.status_code == 400
        assert isinstance(err.response, spec.BadRequestProblemDetails)
        assert err.response.detail == "Invalid invoice data"
        assert len(err.response.errors) == 2
        assert err.response.errors[0].code == 100
        assert "Missing field" in str(err)

    def test_401_problem_details(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        body = {
            "title": "Unauthorized",
            "status": 401,
            "detail": "Token expired",
            "instance": "https://ksef.mf.gov.pl/errors/456",
            "traceId": "def-456",
            "timestamp": "2026-04-16T12:00:00Z",
        }
        fake_transport.responses.append(_make_problem_response(401, body))

        with pytest.raises(exceptions.KSeFAuthError) as exc_info:
            exceptions_middleware.request("GET", "/invoice")

        err = exc_info.value
        assert err.status_code == 401
        assert isinstance(err.response, spec.UnauthorizedProblemDetails)
        assert "Token expired" in str(err)

    def test_403_problem_details(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        body = {
            "title": "Forbidden",
            "status": 403,
            "detail": "Insufficient permissions",
            "instance": "https://ksef.mf.gov.pl/errors/789",
            "reasonCode": "missing-permissions",
            "security": {
                "requiredAnyOfPermissions": ["InvoiceWrite"],
                "presentPermissions": ["InvoiceRead"],
            },
            "traceId": "ghi-789",
            "timestamp": "2026-04-16T12:00:00Z",
        }
        fake_transport.responses.append(_make_problem_response(403, body))

        with pytest.raises(exceptions.KSeFAuthError) as exc_info:
            exceptions_middleware.request("POST", "/invoice")

        err = exc_info.value
        assert err.status_code == 403
        assert isinstance(err.response, spec.ForbiddenProblemDetails)
        assert err.response.reasonCode == "missing-permissions"
        assert "Insufficient permissions" in str(err)

    def test_410_problem_details(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        body = {
            "title": "Gone",
            "status": 410,
            "instance": "https://ksef.mf.gov.pl/errors/gone",
            "detail": "Session no longer available",
            "timestamp": "2026-04-16T12:00:00Z",
            "traceId": "jkl-012",
        }
        fake_transport.responses.append(_make_problem_response(410, body))

        with pytest.raises(exceptions.KSeFApiError) as exc_info:
            exceptions_middleware.request("GET", "/session")

        err = exc_info.value
        assert err.status_code == 410
        assert isinstance(err.response, spec.GoneProblemDetails)
        assert "Session no longer available" in str(err)

    def test_429_problem_details(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        body = {
            "title": "Too Many Requests",
            "status": 429,
            "instance": "https://ksef.mf.gov.pl/errors/rate",
            "detail": "Rate limit exceeded, retry later",
            "timestamp": "2026-04-16T12:00:00Z",
            "traceId": "mno-345",
        }
        fake_transport.responses.append(
            _make_problem_response(429, body, headers={"Retry-After": "30"})
        )

        with pytest.raises(exceptions.KSeFRateLimitError) as exc_info:
            exceptions_middleware.request("GET", "/invoice")

        err = exc_info.value
        assert err.retry_after == 30
        assert isinstance(err.response, spec.TooManyRequestsProblemDetails)
        assert "Rate limit exceeded" in str(err)

    def test_problem_details_falls_back_on_parse_failure(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        fake_transport.responses.append(
            _make_problem_response(400, {"garbage": "not a valid problem details"})
        )

        with pytest.raises(exceptions.KSeFApiError) as exc_info:
            exceptions_middleware.request("POST", "/invoice")

        err = exc_info.value
        assert err.status_code == 400

    def test_problem_details_unrecognized_status_falls_back(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        fake_transport.responses.append(
            _make_problem_response(
                500, {"title": "Internal Server Error", "detail": "oops"}
            )
        )

        with pytest.raises(exceptions.KSeFApiError) as exc_info:
            exceptions_middleware.request("GET", "/invoice")

        err = exc_info.value
        assert err.status_code == 500

    def test_existing_exception_response_format_still_works(
        self,
        fake_transport: FakeTransport,
        exceptions_middleware: middlewares.KSeFExceptionMiddleware,
    ):
        body = {
            "exception": {
                "exceptionDetailList": [
                    {
                        "exceptionCode": 21405,
                        "exceptionDescription": "Validation error",
                        "details": ["field X is required"],
                    }
                ]
            }
        }
        fake_transport.enqueue(status_code=400, json_body=body)

        with pytest.raises(exceptions.KSeFApiError) as exc_info:
            exceptions_middleware.request("POST", "/invoice")

        err = exc_info.value
        assert err.status_code == 400
        assert err.exception_code == exceptions.ExceptionCode.VALIDATION_ERROR
        assert "Validation error" in str(err)
