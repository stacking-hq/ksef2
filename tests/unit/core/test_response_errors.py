"""The KSeF error pipeline: normalize a response, classify it, build the exception."""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from ksef2._core import exceptions, response_errors, retry_after
from ksef2._core.exceptions import ExceptionCode
from ksef2._core.middlewares import KSeFExceptionMiddleware
from ksef2._infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport

PROBLEM = {"content-type": "application/problem+json"}


def _raise(
    status: int,
    *,
    json: Any | None = None,
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    path: str = "/invoices/ksef/1",
) -> exceptions.KSeFApiError:
    if content is not None:
        response = httpx.Response(status, content=content, headers=headers)
    elif json is not None:
        response = httpx.Response(status, json=json, headers=headers)
    else:
        response = httpx.Response(status, headers=headers)
    with pytest.raises(exceptions.KSeFApiError) as exc_info:
        response_errors.raise_for_ksef_status(response, method=method, path=path)
    return exc_info.value


def _legacy(code: int | None, description: str, *details: str) -> dict[str, Any]:
    return {
        "exception": {
            "exceptionDetailList": [
                {
                    "exceptionCode": code,
                    "exceptionDescription": description,
                    "details": list(details),
                }
            ]
        }
    }


def _bad_request(*errors: dict[str, Any], trace_id: str = "trace-1") -> dict[str, Any]:
    return {
        "title": "Bad Request",
        "status": 400,
        "instance": "https://ksef.example/errors/1",
        "detail": "general problem",
        "errors": list(errors),
        "timestamp": "2026-04-16T12:00:00Z",
        "traceId": trace_id,
    }


def _problem(status: int, title: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {
        "title": title,
        "status": status,
        "instance": "https://ksef.example/errors/1",
        "detail": detail,
        "timestamp": "2026-04-16T12:00:00Z",
        **extra,
    }


class TestMessageFormat:
    def test_problem_json_with_details_and_trace_id(self) -> None:
        error = _raise(
            400,
            json=_bad_request(
                {
                    "code": 21405,
                    "description": "Validation error.",
                    "details": ["invoiceNumber is required"],
                },
                {"code": 21418, "description": "Bad token.", "details": None},
            ),
            headers=PROBLEM,
            method="POST",
            path="/invoices/query/metadata",
        )

        assert str(error.args[0]) == (
            "KSeF rejected POST /invoices/query/metadata "
            "(HTTP 400, KSeF code 21405): Validation error.\n"
            "Details: invoiceNumber is required; [21418] Bad token.\n"
            "Trace ID: trace-1"
        )
        assert str(error) == str(error.args[0])

    def test_problem_json_without_errors_uses_detail(self) -> None:
        error = _raise(400, json=_bad_request(), headers=PROBLEM)

        assert error.ksef_code is None
        assert str(error) == (
            "KSeF rejected GET /invoices/ksef/1 (HTTP 400): general problem\n"
            "Trace ID: trace-1"
        )

    def test_legacy_exception_response(self) -> None:
        error = _raise(
            400, json=_legacy(21405, "Validation error.", "field a", "field b")
        )

        assert str(error) == (
            "KSeF rejected GET /invoices/ksef/1 (HTTP 400, KSeF code 21405): "
            "Validation error.\nDetails: field a; field b"
        )

    def test_legacy_response_lists_further_entries_as_details(self) -> None:
        body = _legacy(21405, "First.")
        body["exception"]["exceptionDetailList"].append(
            {"exceptionCode": 21418, "exceptionDescription": "Second.", "details": []}
        )

        error = _raise(400, json=body)

        assert error.details == ["[21418] Second."]

    def test_forbidden_problem_keeps_the_reason_code(self) -> None:
        body = _problem(
            403,
            "Forbidden",
            "Missing permissions.",
            reasonCode="missing-permissions",
            traceId="t-403",
        )

        error = _raise(403, json=body, headers=PROBLEM)

        assert isinstance(error.response, spec.ForbiddenProblemDetails)
        assert error.details == ["reasonCode: missing-permissions"]
        assert error.trace_id == "t-403"
        assert "Details: reasonCode: missing-permissions" in str(error)

    def test_non_json_body_includes_a_truncated_snippet(self) -> None:
        error = _raise(502, content=b"<html>" + b"x" * 500 + b"</html>")

        message = error.args[0]
        assert message.startswith(
            "KSeF rejected GET /invoices/ksef/1 (HTTP 502): <html>"
        )
        assert message.endswith("...")
        assert len(message) < 300
        assert error.response is None
        assert error.ksef_code is None

    def test_json_in_an_unknown_shape_is_summarised_not_dumped_whole(self) -> None:
        error = _raise(500, json={"code": "ERR", "message": "boom"})

        assert str(error) == (
            "KSeF rejected GET /invoices/ksef/1 (HTTP 500): "
            '{"code":"ERR","message":"boom"}'
        )

    def test_empty_body_falls_back_to_the_reason_phrase(self) -> None:
        error = _raise(503)

        assert str(error) == (
            "KSeF rejected GET /invoices/ksef/1 (HTTP 503): Service Unavailable"
        )

    def test_problem_json_for_a_status_without_a_model(self) -> None:
        body = _problem(500, "Internal Server Error", "Boom.", traceId="t-500")

        error = _raise(500, json=body, headers=PROBLEM)

        assert str(error) == (
            "KSeF rejected GET /invoices/ksef/1 (HTTP 500): Boom.\nTrace ID: t-500"
        )

    def test_message_never_dumps_the_response_body(self) -> None:
        error = _raise(400, json=_legacy(21405, "Validation error."))

        assert "Response:" not in str(error)
        assert "exceptionDetailList" not in str(error)
        assert isinstance(error.response, spec.ExceptionResponse)


class TestCodesAndTraceIds:
    def test_known_code_fills_both_the_raw_code_and_the_enum(self) -> None:
        error = _raise(400, json=_legacy(21405, "Validation error."))

        assert error.ksef_code == 21405
        assert error.exception_code is ExceptionCode.VALIDATION_ERROR

    @pytest.mark.parametrize("shape", ["legacy", "problem"])
    def test_unknown_code_survives_as_a_raw_int(self, shape: str) -> None:
        if shape == "legacy":
            error = _raise(400, json=_legacy(29999, "Something new."))
        else:
            error = _raise(
                400,
                json=_bad_request({"code": 29999, "description": "Something new."}),
                headers=PROBLEM,
            )

        assert error.ksef_code == 29999
        assert error.exception_code is ExceptionCode.UNKNOWN_ERROR
        assert "KSeF code 29999" in str(error)
        assert error.context["ksef_code"] == 29999

    def test_trace_id_is_kept(self) -> None:
        error = _raise(
            400,
            json=_bad_request({"code": 21405, "description": "x"}, trace_id="abc-9"),
            headers=PROBLEM,
        )

        assert error.trace_id == "abc-9"
        assert error.context["trace_id"] == "abc-9"
        assert "Trace ID: abc-9" in str(error)

    def test_responses_without_a_code_or_trace_id_leave_them_none(self) -> None:
        error = _raise(500, content=b"nope")

        assert (error.ksef_code, error.trace_id, error.details) == (None, None, [])
        assert error.exception_code is ExceptionCode.UNKNOWN_ERROR


class TestClassMapping:
    @pytest.mark.parametrize("status", [400, 404, 500])
    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            (21165, ExceptionCode.NOT_PROCESSED_YET),
            (21178, ExceptionCode.UPO_NOT_FOUND),
        ],
    )
    def test_not_ready_codes_map_to_not_ready_error(
        self, status: int, code: int, expected: ExceptionCode
    ) -> None:
        error = _raise(status, json=_legacy(code, "Not yet."))

        assert type(error) is exceptions.KSeFNotReadyError
        assert error.status_code == status
        assert error.exception_code is expected

    def test_not_ready_error_from_problem_json(self) -> None:
        error = _raise(
            400,
            json=_bad_request({"code": 21165, "description": "Not yet."}),
            headers=PROBLEM,
        )

        assert type(error) is exceptions.KSeFNotReadyError

    @pytest.mark.parametrize("status", [401, 403])
    def test_auth_statuses_map_to_auth_error(self, status: int) -> None:
        shape = _problem(status, "No", "Denied.", reasonCode="x")
        error = _raise(status, json=shape, headers=PROBLEM)

        assert type(error) is exceptions.KSeFAuthError
        assert error.status_code == status

    def test_legacy_401_maps_to_auth_error_and_keeps_the_code(self) -> None:
        error = _raise(401, json=_legacy(21301, "No authorization."))

        assert type(error) is exceptions.KSeFAuthError
        assert error.ksef_code == 21301

    def test_429_maps_to_rate_limit_error(self) -> None:
        error = _raise(
            429, json={"status": {"code": 429, "description": "x", "details": []}}
        )

        assert type(error) is exceptions.KSeFRateLimitError
        assert error.status_code == 429

    @pytest.mark.parametrize("status", [400, 404, 410, 500, 503])
    def test_everything_else_is_a_plain_api_error(self, status: int) -> None:
        error = _raise(status, json=_legacy(21405, "Validation error."))

        assert type(error) is exceptions.KSeFApiError


class TestHintsFromTheTable:
    def test_not_ready_hints_depend_on_the_code(self) -> None:
        invoice = _raise(400, json=_legacy(21165, "Not yet."))
        upo = _raise(400, json=_legacy(21178, "No UPO."))

        assert invoice.hint is not None and "download()" in invoice.hint
        assert upo.hint is not None and "download_upo()" in upo.hint
        assert f"Hint: {upo.hint}" in str(upo)
        assert upo.context["hint"] == upo.hint

    @pytest.mark.parametrize("status", [401, 403])
    def test_auth_errors_carry_a_hint(self, status: int) -> None:
        error = _raise(
            status,
            json=_problem(status, "No", "Denied.", reasonCode="x"),
            headers=PROBLEM,
        )

        assert error.hint is not None

    def test_unrelated_errors_have_no_hint(self) -> None:
        error = _raise(400, json=_legacy(21405, "Validation error."))

        assert error.hint is None
        assert "Hint:" not in str(error)
        assert "hint" not in error.context


class TestRetryAfter:
    def _429(self, **headers: str) -> exceptions.KSeFRateLimitError:
        error = _raise(
            429,
            json=_problem(429, "Too Many Requests", "Slow down."),
            headers={**PROBLEM, **headers},
        )
        assert isinstance(error, exceptions.KSeFRateLimitError)
        return error

    def test_seconds_form(self) -> None:
        error = self._429(**{"Retry-After": "17"})

        assert error.retry_after == 17
        assert error.hint == "Wait 17 seconds before retrying."
        assert error.context["retry_after"] == 17
        assert str(error).splitlines()[0] == (
            "KSeF rejected GET /invoices/ksef/1 (HTTP 429): Slow down."
        )

    def test_http_date_form(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now = datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC)
        monkeypatch.setattr(retry_after, "_now", lambda: now)

        error = self._429(**{"Retry-After": "Fri, 01 May 2026 12:00:42 GMT"})

        assert error.retry_after == 42
        assert error.hint == "Wait 42 seconds before retrying."

    def test_legacy_429_body(self) -> None:
        body = {
            "status": {
                "code": 429,
                "description": "Too Many Requests",
                "details": ["Limit exceeded, retry in 3 seconds."],
            }
        }

        error = _raise(429, json=body, headers={"Retry-After": "3"})

        assert isinstance(error.response, spec.TooManyRequestsResponse)
        assert str(error).startswith(
            "KSeF rejected GET /invoices/ksef/1 (HTTP 429): Too Many Requests\n"
            "Details: Limit exceeded, retry in 3 seconds."
        )

    def test_missing_header_gives_a_generic_hint(self) -> None:
        error = self._429()

        assert error.retry_after is None
        assert error.hint is not None and "None" not in error.hint

    def test_unreadable_header_is_ignored(self) -> None:
        assert self._429(**{"Retry-After": "soon"}).retry_after is None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("5", 5.0),
            (" 5 ", 5.0),
            ("1.5", 1.5),
            ("0", 0.0),
            ("-3", 0.0),
            ("Wed, 21 Oct 2026 07:28:30 GMT", 30.0),
            ("Wed, 21 Oct 2026 07:27:00 GMT", 0.0),
            ("21 Oct 2026 07:28:30 -0000", 30.0),
            ("nan", None),
            ("inf", None),
            ("tomorrow", None),
            ("", None),
            (None, None),
        ],
    )
    def test_parse(
        self, monkeypatch: pytest.MonkeyPatch, value: str | None, expected: float | None
    ) -> None:
        now = datetime(2026, 10, 21, 7, 28, 0, tzinfo=UTC)
        monkeypatch.setattr(retry_after, "_now", lambda: now)

        assert retry_after.parse_retry_after(value) == expected

    def test_a_date_in_the_future_rounds_up_to_whole_seconds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        now = datetime(2026, 5, 1, 12, 0, 0, 500_000, tzinfo=UTC)
        monkeypatch.setattr(retry_after, "_now", lambda: now)
        later = (now + timedelta(seconds=10)).replace(microsecond=0)
        header = later.strftime("%a, %d %b %Y %H:%M:%S GMT")

        assert self._429(**{"Retry-After": header}).retry_after == 10


class TestMiddlewareRequestContext:
    def test_message_names_the_method_and_path_of_the_request(self) -> None:
        transport = FakeTransport()
        transport.enqueue(_legacy(21405, "Validation error."), status_code=400)
        middleware = KSeFExceptionMiddleware(transport)

        with pytest.raises(exceptions.KSeFApiError) as exc_info:
            middleware.request("DELETE", "/tokens/abc")

        assert str(exc_info.value).startswith(
            "KSeF rejected DELETE /tokens/abc (HTTP 400, KSeF code 21405)"
        )

    def test_success_passes_through(self) -> None:
        transport = FakeTransport()
        transport.enqueue({"ok": True})

        response = KSeFExceptionMiddleware(transport).request("GET", "/x")

        assert response.json() == {"ok": True}
