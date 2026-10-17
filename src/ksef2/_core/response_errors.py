import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

import httpx
from pydantic import BaseModel, ValidationError

from ksef2._core import exceptions
from ksef2._core.codecs import JsonResponseCodec
from ksef2._core.retry_after import parse_retry_after
from ksef2._infra.schema.api import spec

_SNIPPET_LENGTH = 200

type LegacyExceptionResponseModel = (
    spec.UnauthorizedProblemDetails
    | spec.TooManyRequestsResponse
    | spec.ExceptionResponse
)
type ProblemDetailsExceptionResponseModel = (
    spec.BadRequestProblemDetails
    | spec.UnauthorizedProblemDetails
    | spec.ForbiddenProblemDetails
    | spec.GoneProblemDetails
    | spec.TooManyRequestsProblemDetails
)

type ExceptionResponseModel = (
    LegacyExceptionResponseModel | ProblemDetailsExceptionResponseModel
)

# The response's media type picks what map is used
# KSeF 2.0 API returns errors in Problem Details format
# if requests are sent with ``X-Error-Format: problem-details`` header
# SDK sends attaches these headers by default
# you can switch to legacy format by configuring the client

LEGACY_EXC_RESPONSE_MAP: dict[int, type[LegacyExceptionResponseModel]] = {
    401: spec.UnauthorizedProblemDetails,  # Unauthorized
    429: spec.TooManyRequestsResponse,  # Too Many Requests
}

PROBLEM_DETAILS_EXC_RESPONSE_MAP: dict[
    int, type[ProblemDetailsExceptionResponseModel]
] = {
    400: spec.BadRequestProblemDetails,  # Bad Request
    401: spec.UnauthorizedProblemDetails,  # Unauthorized
    403: spec.ForbiddenProblemDetails,  # Forbidden
    410: spec.GoneProblemDetails,  # Gone, resource is no longer available
    429: spec.TooManyRequestsProblemDetails,  # Too Many Requests
}

# A body its model above rejects (a required field missing, a value outside the
# spec's limits), or Problem Details with a status the spec has no model for, is
# read again with a loose twin: the same shape, every field optional. Its KSeF
# code, description and trace ID still count, but ``response`` stays ``None``.


class _LooseApiError(BaseModel):
    code: int | None = None
    description: str | None = None
    details: list[str] | None = None


class _LooseProblemDetails(BaseModel):
    title: str | None = None
    detail: str | None = None
    errors: list[_LooseApiError] | None = None
    reasonCode: str | None = None
    security: dict[str, object] | None = None
    traceId: str | None = None


class _LooseExceptionInfo(BaseModel):
    exceptionDetailList: list[spec.ExceptionDetails] | None = None
    serviceCode: str | None = None


class _LooseExceptionResponse(BaseModel):
    exception: _LooseExceptionInfo | None = None


class _LooseTooManyRequestsResponse(BaseModel):
    status: _LooseApiError | None = None


type LooseLegacyExceptionResponseModel = (
    _LooseProblemDetails | _LooseTooManyRequestsResponse | _LooseExceptionResponse
)

LOOSE_LEGACY_EXC_RESPONSE_MAP: dict[int, type[LooseLegacyExceptionResponseModel]] = {
    401: _LooseProblemDetails,  # Unauthorized
    429: _LooseTooManyRequestsResponse,  # Too Many Requests
}


# mapped to KSeFNotReadyError
_NOT_READY_CODES = frozenset(
    {
        exceptions.ExceptionCode.NOT_PROCESSED_YET,
        exceptions.ExceptionCode.UPO_NOT_FOUND,
    }
)

# mapped to KSeFAuthError
_AUTH_CODES = frozenset(
    {
        exceptions.ExceptionCode.NO_AUTHORIZATION,
        exceptions.ExceptionCode.NO_AUTHENTICATION,
        exceptions.ExceptionCode.DECEASED_PERSON_AUTHENTICATION,
    }
)

# mapped to KSeFNotFoundError
_NOT_FOUND_CODES = frozenset(
    {
        exceptions.ExceptionCode.INVOICE_NOT_FOUND,
        exceptions.ExceptionCode.SESSION_NOT_FOUND,
        exceptions.ExceptionCode.QUERY_RESULT_NOT_FOUND,
        exceptions.ExceptionCode.ENROLLMENT_NOT_FOUND,
        exceptions.ExceptionCode.CERTIFICATE_NOT_FOUND,
        exceptions.ExceptionCode.COLLECTIVE_INVOICE_NOT_FOUND,
    }
)

# mapped to KSeFServerError
_SERVER_ERROR_CODES = frozenset(
    {exceptions.ExceptionCode.SESSION_TEMPORARILY_UNAVAILABLE}
)

type ApiResponseExceptions = (
    exceptions.KSeFNotReadyError
    | exceptions.KSeFAuthError
    | exceptions.KSeFNotFoundError
    | exceptions.KSeFServerError
    | exceptions.KSeFRateLimitError
    | exceptions.KSeFApiError
)

EXCEPTION_CODE_TO_EXCEPTION_MAP: dict[
    exceptions.ExceptionCode, type[ApiResponseExceptions]
] = {
    **{code: exceptions.KSeFNotReadyError for code in _NOT_READY_CODES},
    **{code: exceptions.KSeFAuthError for code in _AUTH_CODES},
    **{code: exceptions.KSeFNotFoundError for code in _NOT_FOUND_CODES},
    **{code: exceptions.KSeFServerError for code in _SERVER_ERROR_CODES},
}

STATUS_CODE_TO_EXCEPTION_MAP: dict[int, type[ApiResponseExceptions]] = {
    401: exceptions.KSeFAuthError,
    403: exceptions.KSeFAuthError,
    404: exceptions.KSeFNotFoundError,
    410: exceptions.KSeFNotFoundError,
    429: exceptions.KSeFRateLimitError,
}


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
        "The session has reached its invoice limit. Close it with `close()` and send "
        "the remaining invoices in a new session from `online_session()`."
    ),
    21157: (
        "Build the encrypted package with `auth.batch.prepare()`, which splits parts "
        "within KSeF size and count limits."
    ),
    21161: (
        "Build the encrypted package with `auth.batch.prepare()`, which splits parts "
        "within KSeF size and count limits."
    ),
    21165: (
        "KSeF has processed the invoice but has not made it available yet. Call "
        "`download()` with a `timeout` so the SDK keeps polling until it is."
    ),
    21178: (
        "KSeF has no UPO for this yet. Call `wait()` on the invoice submission or the"
        " session first, then call `download_upo()` or `download_invoice_upo()` "
        "again. If `wait()` raises `KSeFInvoiceRejectedError`, KSeF rejected the "
        "invoice and will never issue a UPO for it."
    ),
    21180: (
        "The session is already closed or in a state that does not allow this "
        "operation. Check its state with `get_status()`, or open a new session with "
        "`online_session()` or `batch_session()`."
    ),
    21182: (
        "KSeF limits how many exports can run at once. Wait for a running export to "
        "finish with `wait()`, then call `export()` again."
    ),
    21183: (
        "The date range reaches outside the data KSeF keeps. Narrow the date range in"
        " the filters passed to `search()`."
    ),
    21184: (
        "KSeF cannot accept invoices in this session at the moment. Retry later, or "
        "send the invoice in a new session from `online_session()`."
    ),
    21205: (
        "Upload every declared batch part with `upload_parts()` before closing the "
        "session, or send the batch with `submit()`."
    ),
    21208: (
        "KSeF cancelled the batch session because the parts were not uploaded or the "
        "session was not closed in time. Send the package again in a new session from"
        " `batch_session()`."
    ),
    21418: (
        "Continuation tokens come from KSeF and are only valid as returned. Iterate "
        "the pager the SDK returns, or use its `pages()`, instead of building or "
        "reusing a token yourself."
    ),
    21470: (
        "KSeF does not know the public key the request was encrypted with, or has "
        "retired it. The SDK keeps KSeF certificates for 24 hours; create a new "
        "client so it loads the current ones."
    ),
    25001: (
        "Certificate enrollment requires XAdES authentication. Authenticate with "
        "`client.authentication.with_xades()` instead of "
        "`client.authentication.with_token()`."
    ),
    25002: (
        "Certificate enrollment requires XAdES authentication. Authenticate with "
        "`client.authentication.with_xades()` instead of "
        "`client.authentication.with_token()`."
    ),
    25003: (
        "Fetch the subject data KSeF expects with `get_enrollment_data()` and build a"
        " new CSR before calling `enroll()`."
    ),
    25006: (
        "KSeF allows only a limited number of certificate enrollments. `get_limits()`"
        " shows how many are still allowed."
    ),
    25007: (
        "You hold the maximum number of KSeF certificates. Revoke one you no longer "
        "use with `revoke()`, and check `get_limits()` for the limit."
    ),
    26001: (
        "A token can only get permissions the authenticated identity holds. Request "
        "fewer permissions in `generate()`."
    ),
    26002: (
        "KSeF tokens cannot be generated in this context type. Authenticate in a "
        "supported context before calling `generate()`."
    ),
    30001: (
        "The subject or person already exists on KSeF TEST. Reuse it, or remove it "
        "first with `delete_subject()` or `delete_person()`."
    ),
}


def _snippet(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SNIPPET_LENGTH:
        return collapsed
    return collapsed[:_SNIPPET_LENGTH] + "..."


def _detail_lines(
    code: int | None, description: str | None, details: list[str] | None
) -> list[str]:
    """Render a further error entry as ``[code] description`` plus its details."""
    head = f"[{code}] {description}" if code is not None else description
    return [line for line in (head, *(details or [])) if line]


def _trace_id_from_service_code(service_code: str | None) -> str | None:
    """Return the trace ID a legacy body carries in ``serviceCode``.

    KSeF fills ``serviceCode`` with a W3C ``traceparent``
    (``00-<trace id>-<span id>-00``); Problem Details carry the ``<trace id>``
    part as ``traceId``. Any other value is returned as it is.
    """
    if service_code is None:
        return None
    parts = service_code.split("-")
    if len(parts) == 4 and len(parts[1]) == 32:
        return parts[1]
    return service_code


def _security_lines(security: Mapping[str, object] | None) -> list[str]:
    """Render the 403 ``security`` data as ``key: value`` lines, lists comma-separated."""
    lines: list[str] = []
    for key, value in (security or {}).items():
        if value is None:
            continue
        if isinstance(value, list):
            value = ", ".join(map(str, cast(list[object], value))) or "none"
        lines.append(f"{key}: {value}")
    return lines


@dataclass(frozen=True, slots=True)
class _Fields:
    """What an error body says, whatever its shape."""

    error_code: int | None = None
    description: str | None = None
    details: tuple[str, ...] = ()
    trace_id: str | None = None

    def to_exc_message(
        self, response: httpx.Response, *, method: str, path: str
    ) -> str:
        description = (
            self.description
            or _snippet(response.text)
            or response.reason_phrase
            or "no description"
        )
        code = f", KSeF code {self.error_code}" if self.error_code is not None else ""
        lines = [
            f"KSeF rejected {method} {path} "
            f"(HTTP {response.status_code}{code}): {description}"
        ]
        if self.details:
            lines.append(f"Details: {'; '.join(self.details)}")
        if self.trace_id:
            lines.append(f"Trace ID: {self.trace_id}")
        return "\n".join(lines)


def get_legacy_fields(
    model: LegacyExceptionResponseModel | LooseLegacyExceptionResponseModel,
) -> _Fields:
    match model:
        case spec.ExceptionResponse() | _LooseExceptionResponse():
            entries = (
                (model.exception.exceptionDetailList or []) if model.exception else []
            )
            trace_id = (
                _trace_id_from_service_code(model.exception.serviceCode)
                if model.exception
                else None
            )
            if not entries:
                return _Fields(trace_id=trace_id)

            first, *rest = entries
            details = list(first.details or [])
            for entry in rest:
                details.extend(
                    _detail_lines(
                        entry.exceptionCode, entry.exceptionDescription, entry.details
                    )
                )

            # take the first exception code as the main one
            return _Fields(
                first.exceptionCode,
                first.exceptionDescription,
                tuple(details),
                trace_id,
            )

        case spec.TooManyRequestsResponse() | _LooseTooManyRequestsResponse():
            if model.status is None:
                return _Fields()
            return _Fields(
                description=model.status.description,
                details=tuple(model.status.details or ()),
            )

        case spec.UnauthorizedProblemDetails() | _LooseProblemDetails():
            return _Fields(description=model.detail, trace_id=model.traceId)


def get_problem_details_fields(
    model: ProblemDetailsExceptionResponseModel | _LooseProblemDetails,
) -> _Fields:
    match model:
        case spec.BadRequestProblemDetails():
            if not model.errors:
                return _Fields(description=model.detail, trace_id=model.traceId)
            first, *rest = model.errors
            details = list(first.details or [])
            for error in rest:
                details.extend(
                    _detail_lines(error.code, error.description, error.details)
                )

            # take the first error code as the main one
            return _Fields(first.code, first.description, tuple(details), model.traceId)

        case spec.ForbiddenProblemDetails():
            return _Fields(
                description=model.detail,
                details=(
                    f"reasonCode: {model.reasonCode}",
                    *_security_lines(model.security),
                ),
                trace_id=model.traceId,
            )

        case (
            spec.GoneProblemDetails()
            | spec.TooManyRequestsProblemDetails()
            | spec.UnauthorizedProblemDetails()
        ):
            return _Fields(description=model.detail, trace_id=model.traceId)

        case _LooseProblemDetails():
            # any of the shapes above, so read everything they can carry
            first, *rest = model.errors or [_LooseApiError()]
            details = list(first.details or [])
            for error in rest:
                details.extend(
                    _detail_lines(error.code, error.description, error.details)
                )
            if model.reasonCode:
                details.append(f"reasonCode: {model.reasonCode}")
            details.extend(_security_lines(model.security))

            return _Fields(
                first.code,
                first.description or model.detail or model.title,
                tuple(details),
                model.traceId,
            )


def _read_error_body(
    response: httpx.Response,
) -> tuple[ExceptionResponseModel | None, _Fields]:
    """Parse the body with the model its media type and status call for."""

    def _parse[T: BaseModel](response: httpx.Response, model_type: type[T]) -> T | None:
        if not response.text.strip():
            return None
        try:
            return JsonResponseCodec.parse(response, model_type)
        except (ValidationError, ValueError):
            return None

    content_type = cast(str, response.headers.get("Content-Type", ""))
    media_type = content_type.split(";", 1)[0].strip().lower()

    fields = _Fields()
    model = None

    match media_type:
        case "application/json":
            legacy = _parse(
                response,
                LEGACY_EXC_RESPONSE_MAP.get(
                    response.status_code, spec.ExceptionResponse
                ),
            )
            if legacy is not None:
                model, fields = legacy, get_legacy_fields(legacy)
            else:
                loose_legacy = _parse(
                    response,
                    LOOSE_LEGACY_EXC_RESPONSE_MAP.get(
                        response.status_code, _LooseExceptionResponse
                    ),
                )
                if loose_legacy is not None:
                    fields = get_legacy_fields(loose_legacy)

        case "application/problem+json":
            model_type = PROBLEM_DETAILS_EXC_RESPONSE_MAP.get(response.status_code)
            problem = _parse(response, model_type) if model_type is not None else None
            if problem is not None:
                model, fields = problem, get_problem_details_fields(problem)
            else:
                loose_problem = _parse(response, _LooseProblemDetails)
                if loose_problem is not None:
                    fields = get_problem_details_fields(loose_problem)

        case _:
            # HTML from a gateway, plain text or no body: the message uses a snippet.
            pass

    if fields.description is None:
        # in case a response parses but says nothing
        # we treat it as if it were an empty ExceptionResponse
        model = None

    return model, fields


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

    model, fields = _read_error_body(response)

    message = fields.to_exc_message(response, method=method, path=path)

    status = response.status_code
    exception_code = exceptions.ExceptionCode.from_code(fields.error_code)
    details = list(fields.details)

    hint = _CODE_HINTS.get(fields.error_code) if fields.error_code is not None else None

    # mapping by first exception code returned by API has priority
    if exception_code in EXCEPTION_CODE_TO_EXCEPTION_MAP:
        exception_cls = EXCEPTION_CODE_TO_EXCEPTION_MAP[exception_code]

    # if we don't have a mapping for a specific exception code
    # we fall back to mapping from status code
    elif status in STATUS_CODE_TO_EXCEPTION_MAP:
        exception_cls = STATUS_CODE_TO_EXCEPTION_MAP[status]

    # mapped when API is down or fails to process our request
    elif 500 <= status < 600:
        exception_cls = exceptions.KSeFServerError
    else:
        # everything else
        exception_cls = exceptions.KSeFApiError

    if issubclass(exception_cls, exceptions.KSeFAuthError):
        raise exception_cls(
            status,
            message,
            model,
            ksef_code=fields.error_code,
            trace_id=fields.trace_id,
            details=details,
            hint=hint or (_FORBIDDEN_HINT if status == 403 else _UNAUTHORIZED_HINT),
        )
    elif issubclass(exception_cls, exceptions.KSeFRateLimitError):
        retry_after = parse_retry_after(
            cast(str | None, response.headers.get("Retry-After"))
        )
        raise exception_cls(
            None if retry_after is None else math.ceil(retry_after),
            message,
            model,
            ksef_code=fields.error_code,
            trace_id=fields.trace_id,
            details=details,
            hint=hint,
        )

    else:
        raise exception_cls(
            status,
            exception_code,
            message,
            model,
            ksef_code=fields.error_code,
            trace_id=fields.trace_id,
            details=details,
            hint=hint,
        )
