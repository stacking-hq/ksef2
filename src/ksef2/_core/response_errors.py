"""Turn failed KSeF responses into SDK exceptions.

``raise_for_ksef_status`` reads the response in four plain steps:

1. ``_MODELS`` picks the spec model from the media type and the status.
2. ``_fields`` reads the code, description, details and trace ID from that model.
3. ``_message`` formats the one message every KSeF API error uses.
4. ``_exception`` picks the exception class and the hint.
"""

import math
from dataclasses import dataclass
from functools import singledispatch
from typing import cast

import httpx
from pydantic import BaseModel, ValidationError

from ksef2._core import exceptions
from ksef2._core.retry_after import parse_retry_after
from ksef2._infra.schema.api import spec

_SNIPPET_LENGTH = 200

# Keyed by (media type, status); ``None`` as the status matches any status.
# Problem Details is what the SDK asks for (``X-Error-Format: problem-details``);
# ``application/json`` is the legacy format KSeF sends without that header. KSeF
# sends its 401 as Problem Details labelled ``application/json`` (seen on TEST).
_MODELS: dict[tuple[str, int | None], type[BaseModel]] = {
    ("application/problem+json", 400): spec.BadRequestProblemDetails,
    ("application/problem+json", 401): spec.UnauthorizedProblemDetails,
    ("application/problem+json", 403): spec.ForbiddenProblemDetails,
    ("application/problem+json", 410): spec.GoneProblemDetails,
    ("application/problem+json", 429): spec.TooManyRequestsProblemDetails,
    ("application/json", 401): spec.UnauthorizedProblemDetails,
    ("application/json", 429): spec.TooManyRequestsResponse,
    ("application/json", None): spec.ExceptionResponse,
}

_NOT_READY_CODES = frozenset(
    {
        exceptions.ExceptionCode.NOT_PROCESSED_YET,
        exceptions.ExceptionCode.UPO_NOT_FOUND,
    }
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

# Hints for KSeF codes where the SDK knows the next step. A code hint wins over
# the 401/403 hint. Name only current public methods; a test checks them.
_CODE_HINTS: dict[int, str] = {
    21155: (
        "The session has reached its invoice limit. Close it with `close()` and "
        "send the remaining invoices in a new session from `online_session()`."
    ),
    21165: (
        "KSeF has processed the invoice but has not made it available yet. Call "
        "`download()` with a `timeout` so the SDK keeps polling until it is."
    ),
    21178: (
        "KSeF has no UPO for this yet. Call `wait()` on the invoice submission or "
        "the session first, then call `download_upo()` again. If `wait()` raises "
        "`KSeFInvoiceRejectedError`, KSeF rejected the invoice and will never "
        "issue a UPO for it."
    ),
    21180: (
        "The session is already closed or KSeF is processing it, so it accepts "
        "no more invoices. Send further invoices in a new session from "
        "`online_session()` or `batch_session()`."
    ),
    21182: (
        "KSeF limits how many exports can run at once. Wait for a running export "
        "to finish with `wait()`, then call `export()` again."
    ),
    21183: (
        "The date range reaches outside the data KSeF keeps. Narrow the date "
        "range in the filters passed to `search()`."
    ),
    21184: (
        "KSeF cannot accept invoices in this session at the moment. Retry later, "
        "or send the invoice in a new session from `online_session()`."
    ),
    21208: (
        "KSeF cancelled the batch session because the parts were not uploaded or "
        "the session was not closed in time. Send the package again in a new "
        "session from `batch_session()`."
    ),
    21418: (
        "Continuation tokens come from KSeF and are only valid as returned. "
        "Iterate the pager the SDK returns, or use its `pages()`, instead of "
        "building or reusing a token yourself."
    ),
    21470: (
        "KSeF does not know the public key the request was encrypted with, or "
        "has retired it. The SDK keeps KSeF certificates for 24 hours; create a "
        "new client so it loads the current ones."
    ),
    25006: (
        "KSeF allows only a limited number of certificate enrollments. "
        "`get_limits()` shows how many are still allowed."
    ),
    25007: (
        "You hold the maximum number of KSeF certificates. Revoke one you no "
        "longer use with `revoke()`, and check `get_limits()` for the limit."
    ),
    26001: (
        "A token can only get permissions the authenticated identity holds. "
        "Request fewer permissions in `generate()`."
    ),
    30001: (
        "The subject or person already exists on KSeF TEST. Reuse it, or remove "
        "it first with `delete_subject()` or `delete_person()`."
    ),
}


@dataclass(frozen=True, slots=True)
class _Fields:
    """What an error body says, whatever its shape."""

    ksef_code: int | None = None
    description: str | None = None
    details: tuple[str, ...] = ()
    trace_id: str | None = None


def _detail_lines(
    code: int | None, description: str | None, details: list[str] | None
) -> list[str]:
    """Render a further error entry as ``[code] description`` plus its details."""
    head = f"[{code}] {description}" if code is not None else description
    return [line for line in (head, *(details or [])) if line]


@singledispatch
def _fields(model: BaseModel) -> _Fields:
    """Read the error fields from a parsed body; unknown models give none."""
    del model
    return _Fields()


@_fields.register
def _(model: spec.BadRequestProblemDetails) -> _Fields:
    if not model.errors:
        return _Fields(description=model.detail, trace_id=model.traceId)
    first, *rest = model.errors
    details = list(first.details or [])
    for error in rest:
        details.extend(_detail_lines(error.code, error.description, error.details))
    return _Fields(first.code, first.description, tuple(details), model.traceId)


@_fields.register
def _(model: spec.ForbiddenProblemDetails) -> _Fields:
    return _Fields(
        description=model.detail,
        details=(f"reasonCode: {model.reasonCode}",),
        trace_id=model.traceId,
    )


@_fields.register
def _(
    model: spec.UnauthorizedProblemDetails
    | spec.GoneProblemDetails
    | spec.TooManyRequestsProblemDetails,
) -> _Fields:
    return _Fields(description=model.detail, trace_id=model.traceId)


@_fields.register
def _(model: spec.TooManyRequestsResponse) -> _Fields:
    return _Fields(
        description=model.status.description, details=tuple(model.status.details)
    )


@_fields.register
def _(model: spec.ExceptionResponse) -> _Fields:
    entries = (model.exception.exceptionDetailList or []) if model.exception else []
    if not entries:
        return _Fields()
    first, *rest = entries
    details = list(first.details or [])
    for entry in rest:
        details.extend(
            _detail_lines(
                entry.exceptionCode, entry.exceptionDescription, entry.details
            )
        )
    return _Fields(first.exceptionCode, first.exceptionDescription, tuple(details))


def _parse(response: httpx.Response) -> BaseModel | None:
    """Parse the body with the model for its media type and status, if there is one."""
    content_type = cast(str, response.headers.get("Content-Type", ""))
    media_type = content_type.split(";", 1)[0].strip().lower()
    status = response.status_code
    model_type = _MODELS.get((media_type, status)) or _MODELS.get((media_type, None))
    if model_type is None or not response.text.strip():
        return None
    try:
        return model_type.model_validate_json(response.text)
    except (ValidationError, ValueError):
        return None


def _snippet(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SNIPPET_LENGTH:
        return collapsed
    return collapsed[:_SNIPPET_LENGTH] + "..."


def _message(
    response: httpx.Response, fields: _Fields, *, method: str, path: str
) -> str:
    description = (
        fields.description
        or _snippet(response.text)
        or response.reason_phrase
        or "no description"
    )
    code = f", KSeF code {fields.ksef_code}" if fields.ksef_code is not None else ""
    lines = [
        f"KSeF rejected {method} {path} "
        f"(HTTP {response.status_code}{code}): {description}"
    ]
    if fields.details:
        lines.append(f"Details: {'; '.join(fields.details)}")
    if fields.trace_id:
        lines.append(f"Trace ID: {fields.trace_id}")
    return "\n".join(lines)


def _exception(
    response: httpx.Response,
    model: BaseModel | None,
    fields: _Fields,
    message: str,
) -> exceptions.KSeFApiError:
    """Pick the exception class and hint: the KSeF code first, then the status."""
    status = response.status_code
    code = fields.ksef_code
    details = list(fields.details)
    hint = _CODE_HINTS.get(code) if code is not None else None

    if code in _NOT_READY_CODES:
        return exceptions.KSeFNotReadyError(
            status,
            exceptions.ExceptionCode.from_code(code),
            message,
            model,
            ksef_code=code,
            trace_id=fields.trace_id,
            details=details,
            hint=hint,
        )
    if status in (401, 403):
        return exceptions.KSeFAuthError(
            status,
            message,
            model,
            ksef_code=code,
            trace_id=fields.trace_id,
            details=details,
            hint=hint or (_UNAUTHORIZED_HINT if status == 401 else _FORBIDDEN_HINT),
        )
    if status == 429:
        retry_after = parse_retry_after(
            cast(str | None, response.headers.get("Retry-After"))
        )
        return exceptions.KSeFRateLimitError(
            None if retry_after is None else math.ceil(retry_after),
            message,
            model,
            ksef_code=code,
            trace_id=fields.trace_id,
            details=details,
            hint=hint,
        )
    return exceptions.KSeFApiError(
        status,
        exceptions.ExceptionCode.from_code(code),
        message,
        model,
        ksef_code=code,
        trace_id=fields.trace_id,
        details=details,
        hint=hint,
    )


def raise_for_ksef_status(response: httpx.Response, *, method: str, path: str) -> None:
    """Raise the matching SDK exception when KSeF returned an error status.

    Args:
        response: The HTTP response to check.
        method: HTTP method of the request, quoted in the message.
        path: Request path, quoted in the message.

    Raises:
        KSeFApiError: If the status is not a success, or a subclass chosen by KSeF code and status.
    """
    if response.is_success:
        return
    model = _parse(response)
    fields = _fields(model) if model is not None else _Fields()
    if fields.description is None:
        # A body that parsed but says nothing (an ``application/json`` body of
        # another shape reads as an empty ExceptionResponse) is not kept.
        model = None
    message = _message(response, fields, method=method, path=path)
    raise _exception(response, model, fields, message)
