"""Turn failed KSeF responses into SDK exceptions.

The pipeline has three steps, each in one place:

1. ``_normalize`` reads a response in any of its shapes (``application/problem+json``,
   the legacy ``ExceptionResponse`` / ``TooManyRequestsResponse``, other JSON, text or
   an empty body) into one ``_ErrorRecord``.
2. ``_classify`` looks the record up in ``_RULES``, the one table that maps a status
   and a KSeF code to an exception class and an optional hint.
3. ``_build`` formats the single message and constructs the exception.
"""

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

import httpx
from pydantic import BaseModel, ValidationError

from ksef2._core import exceptions
from ksef2._core.retry_after import parse_retry_after
from ksef2._infra.schema.api import spec

_SNIPPET_LENGTH = 200

_PROBLEM_MODELS: dict[int, type[BaseModel]] = {
    400: spec.BadRequestProblemDetails,
    401: spec.UnauthorizedProblemDetails,
    403: spec.ForbiddenProblemDetails,
    410: spec.GoneProblemDetails,
    429: spec.TooManyRequestsProblemDetails,
}


@dataclass(frozen=True, slots=True)
class _ErrorRecord:
    """Everything the SDK knows about one failed response, whatever its shape."""

    status: int
    method: str
    path: str
    ksef_code: int | None
    description: str
    details: tuple[str, ...]
    trace_id: str | None
    retry_after: int | None
    body: BaseModel | None


@dataclass(frozen=True, slots=True)
class _Fields:
    ksef_code: int | None
    description: str | None
    details: tuple[str, ...] = ()
    trace_id: str | None = None


@dataclass(frozen=True, slots=True)
class _Rule:
    exc_type: type[exceptions.KSeFApiError]
    hint: str | None = None


_NOT_READY_INVOICE_HINT = (
    "KSeF has processed the invoice but has not made it available yet. Call "
    "`download()` with a `timeout` so the SDK keeps polling until it is."
)
_NOT_READY_UPO_HINT = (
    "KSeF has not issued the UPO yet. Wait for processing to finish and request it "
    "again: `download_upo()` on a session or an invoice submission waits for "
    "processing first."
)
_UNAUTHORIZED_HINT = (
    "KSeF rejected the credentials or the access token. Authenticate again with "
    "`client.authentication.with_token()` or `client.authentication.with_xades()`, "
    "and check that the token or certificate is valid for this context."
)
_FORBIDDEN_HINT = (
    "The authenticated identity is not allowed to do this in the current context. "
    "Check the reason in `details`, and grant the missing permission with the "
    "permissions client, for example `grant_person()`."
)

# Looked up as (status, code), then (None, code), then (status, None), then
# (None, None). ``None`` matches anything. 429 gets its hint from the exception
# itself, because it depends on ``retry_after``.
_RULES: dict[tuple[int | None, int | None], _Rule] = {
    (None, 21165): _Rule(exceptions.KSeFNotReadyError, _NOT_READY_INVOICE_HINT),
    (None, 21178): _Rule(exceptions.KSeFNotReadyError, _NOT_READY_UPO_HINT),
    (401, None): _Rule(exceptions.KSeFAuthError, _UNAUTHORIZED_HINT),
    (403, None): _Rule(exceptions.KSeFAuthError, _FORBIDDEN_HINT),
    (429, None): _Rule(exceptions.KSeFRateLimitError),
    (None, None): _Rule(exceptions.KSeFApiError),
}


def _lines(
    code: int | None, description: str | None, details: list[str] | None
) -> list[str]:
    """Render a secondary error entry as detail lines."""
    head = f"[{code}] {description}" if code is not None else description
    return [line for line in (head, *(details or [])) if line]


def _problem_fields(model: BaseModel) -> _Fields | None:
    if isinstance(model, spec.BadRequestProblemDetails):
        if not model.errors:
            return _Fields(None, model.detail, trace_id=model.traceId)
        first, *rest = model.errors
        details = list(first.details or [])
        for error in rest:
            details.extend(_lines(error.code, error.description, error.details))
        return _Fields(first.code, first.description, tuple(details), model.traceId)
    if isinstance(model, spec.ForbiddenProblemDetails):
        return _Fields(
            None,
            model.detail,
            (f"reasonCode: {model.reasonCode}",),
            model.traceId,
        )
    if isinstance(
        model,
        spec.UnauthorizedProblemDetails
        | spec.GoneProblemDetails
        | spec.TooManyRequestsProblemDetails,
    ):
        return _Fields(None, model.detail, trace_id=model.traceId)
    return None


def _legacy_fields(model: BaseModel) -> _Fields | None:
    if isinstance(model, spec.TooManyRequestsResponse):
        return _Fields(None, model.status.description, tuple(model.status.details))
    if isinstance(model, spec.ExceptionResponse):
        entries = (model.exception.exceptionDetailList or []) if model.exception else []
        if not entries:
            return None
        first, *rest = entries
        details = list(first.details or [])
        for entry in rest:
            details.extend(
                _lines(entry.exceptionCode, entry.exceptionDescription, entry.details)
            )
        return _Fields(first.exceptionCode, first.exceptionDescription, tuple(details))
    return None


def _try_parse[T: BaseModel](text: str, model: type[T]) -> T | None:
    try:
        return model.model_validate_json(text)
    except (ValidationError, ValueError):
        return None


def _parse_body(status: int, text: str) -> tuple[BaseModel | None, _Fields | None]:
    """Parse a body into a spec model and the fields read from it."""
    if not text.strip():
        return None, None
    problem_model = _PROBLEM_MODELS.get(status)
    if problem_model is not None and (model := _try_parse(text, problem_model)):
        return model, _problem_fields(model)
    legacy_model = (
        spec.TooManyRequestsResponse if status == 429 else spec.ExceptionResponse
    )
    if model := _try_parse(text, legacy_model):
        fields = _legacy_fields(model)
        if fields is None:
            fields = _generic_problem_fields(text)
        return model, fields
    return None, _generic_problem_fields(text)


def _generic_problem_fields(text: str) -> _Fields | None:
    """Read ``detail``/``title`` and ``traceId`` from any JSON object body."""
    try:
        data = cast(object, json.loads(text))
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    obj = cast(Mapping[str, object], data)
    description = obj.get("detail") or obj.get("title")
    trace_id = obj.get("traceId")
    if not isinstance(description, str):
        return None
    return _Fields(
        None, description, trace_id=trace_id if isinstance(trace_id, str) else None
    )


def _snippet(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SNIPPET_LENGTH:
        return collapsed
    return collapsed[:_SNIPPET_LENGTH] + "..."


def _retry_after_seconds(value: str | None) -> int | None:
    seconds = parse_retry_after(value)
    return None if seconds is None else math.ceil(seconds)


def _normalize(response: httpx.Response, method: str, path: str) -> _ErrorRecord:
    text = response.text
    body, fields = _parse_body(response.status_code, text)
    description = fields.description if fields else None
    if not description:
        description = _snippet(text) or response.reason_phrase or "no description"
    headers = response.headers
    return _ErrorRecord(
        status=response.status_code,
        method=method,
        path=path,
        ksef_code=fields.ksef_code if fields else None,
        description=description,
        details=fields.details if fields else (),
        trace_id=fields.trace_id if fields else None,
        retry_after=_retry_after_seconds(cast(str | None, headers.get("Retry-After"))),
        body=body,
    )


def _classify(record: _ErrorRecord) -> _Rule:
    for key in (
        (record.status, record.ksef_code),
        (None, record.ksef_code),
        (record.status, None),
    ):
        if key in _RULES:
            return _RULES[key]
    return _RULES[(None, None)]


def _build_message(record: _ErrorRecord) -> str:
    code = f", KSeF code {record.ksef_code}" if record.ksef_code is not None else ""
    lines = [
        f"KSeF rejected {record.method} {record.path} "
        f"(HTTP {record.status}{code}): {record.description}"
    ]
    if record.details:
        lines.append(f"Details: {'; '.join(record.details)}")
    if record.trace_id:
        lines.append(f"Trace ID: {record.trace_id}")
    return "\n".join(lines)


def _build(record: _ErrorRecord, rule: _Rule) -> exceptions.KSeFApiError:
    message = _build_message(record)
    details = list(record.details)
    if issubclass(rule.exc_type, exceptions.KSeFRateLimitError):
        return rule.exc_type(
            retry_after=record.retry_after,
            message=message,
            response=record.body,
            ksef_code=record.ksef_code,
            trace_id=record.trace_id,
            details=details,
            hint=rule.hint,
        )
    if issubclass(rule.exc_type, exceptions.KSeFAuthError):
        return rule.exc_type(
            status_code=record.status,
            message=message,
            response=record.body,
            ksef_code=record.ksef_code,
            trace_id=record.trace_id,
            details=details,
            hint=rule.hint,
        )
    return rule.exc_type(
        status_code=record.status,
        exception_code=exceptions.ExceptionCode.from_code(record.ksef_code),
        message=message,
        response=record.body,
        ksef_code=record.ksef_code,
        trace_id=record.trace_id,
        details=details,
        hint=rule.hint,
    )


def raise_for_ksef_status(response: httpx.Response, *, method: str, path: str) -> None:
    """Raise the matching SDK exception when KSeF returned an error status.

    Args:
        response: The HTTP response to check.
        method: HTTP method of the request, quoted in the message.
        path: Request path, quoted in the message.

    Raises:
        KSeFApiError: If the status is not a success, or a subclass chosen by status and KSeF code.
    """
    if response.is_success:
        return
    record = _normalize(response, method, path)
    raise _build(record, _classify(record))
