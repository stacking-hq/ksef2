"""Helpers for converting API exception payloads into SDK exceptions."""

from functools import singledispatch

from pydantic import BaseModel

from ksef2.core.exceptions import ExceptionCode
from ksef2.infra.schema.api import spec
from ksef2.core import exceptions

MAX_RAW_BODY_LENGTH = 200


def _truncate(raw_body: str) -> str:
    """Shorten oversized raw response bodies for exception messages."""
    if len(raw_body) <= MAX_RAW_BODY_LENGTH:
        return raw_body
    return raw_body[:MAX_RAW_BODY_LENGTH] + "..."


def get_primary_exception_details(
    response: spec.ExceptionResponse,
) -> spec.ExceptionDetails | None:
    """Return the first exception detail entry when one is present."""
    if exception := response.exception:
        return (
            exception.exceptionDetailList[0] if exception.exceptionDetailList else None
        )
    return None


def _extract_message(
    status_code: int, model: spec.ExceptionResponse | None, raw_body: str
) -> str:
    """Build a readable error message from an exception payload or raw body."""
    if model is None or model.exception is None:
        return f"KSeF error {status_code}. Raw response: {_truncate(raw_body)}"

    primary = get_primary_exception_details(model)
    if not primary:
        return f"KSeF error {status_code}. No details provided."

    code = primary.exceptionCode
    description = primary.exceptionDescription or "<no description>"

    enum_val = ExceptionCode.from_code(code)
    msg = f"KSeF API error: {status_code}\n[{enum_val.name}:{enum_val}] {description}"

    if primary.details:
        msg += f"\nDetails: {', '.join(primary.details)}"
    return msg


def _problem_details_message(
    title: str, detail: str, errors: list[spec.ApiError] | None = None
) -> str:
    """Build a human-readable message from a ProblemDetails payload."""
    msg = f"{title}: {detail}"
    if errors:
        parts = [f"  [{e.code}] {e.description}" for e in errors]
        msg += "\n" + "\n".join(parts)
    return msg


# ------------------------------------------------------------------
# ExceptionResponse (legacy) mappers
# ------------------------------------------------------------------


def from_auth_error(
    status_code: int, model: spec.ExceptionResponse | None, raw_body: str
) -> exceptions.KSeFAuthError:
    """Create an authentication error from a parsed exception payload."""
    message = _extract_message(status_code, model, raw_body)
    return exceptions.KSeFAuthError(
        status_code=status_code, message=message, response=model
    )


def from_bad_request(
    model: spec.ExceptionResponse | None, raw_body: str
) -> exceptions.KSeFApiError:
    """Create a ``400`` API error from a parsed exception payload."""
    return from_api_error(status_code=400, model=model, raw_body=raw_body)


def from_too_many_requests(
    model: spec.TooManyRequestsResponse | None,
    retry_after: int | None,
    raw_body: str,
) -> exceptions.KSeFRateLimitError:
    """Create a rate-limit error with optional ``Retry-After`` metadata."""
    if model and model.status and model.status.description:
        message = f"KSeF rate limit exceeded: {model.status.description}"
    else:
        message = f"KSeF error 429. Raw response: {_truncate(raw_body)}"

    return exceptions.KSeFRateLimitError(
        retry_after=retry_after,
        message=message,
        response=model,
    )


def from_api_error(
    status_code: int, model: spec.ExceptionResponse | None, raw_body: str
) -> exceptions.KSeFApiError:
    """Create a generic API error from a parsed exception payload."""
    message = _extract_message(status_code, model, raw_body)
    primary = get_primary_exception_details(model) if model else None
    code = ExceptionCode.from_code(primary.exceptionCode if primary else None)

    return exceptions.KSeFApiError(
        status_code=status_code,
        exception_code=code,
        message=message,
        response=model,
    )


# ------------------------------------------------------------------
# ProblemDetails (application/problem+json) singledispatch mapper
# ------------------------------------------------------------------


def from_problem_spec(
    model: BaseModel,
    retry_after: int | None = None,
) -> exceptions.KSeFApiError:
    """Convert a parsed ProblemDetails model into the correct SDK exception.

    Args:
        model: A parsed spec model (BadRequestProblemDetails, etc.).
        retry_after: Optional Retry-After value (only used for 429).

    Returns:
        The matching SDK exception instance.

    Raises:
        NotImplementedError: If no mapper exists for the model type.
    """
    return _from_problem_spec(model, retry_after)


@singledispatch
def _from_problem_spec(
    model: BaseModel,
    retry_after: int | None = None,
) -> exceptions.KSeFApiError:
    raise NotImplementedError(
        f"No ProblemDetails mapper registered for {type(model).__name__}. "
        f"Register one with @_from_problem_spec.register"
    )


@_from_problem_spec.register
def _(
    model: spec.BadRequestProblemDetails,
    _retry_after: int | None = None,
) -> exceptions.KSeFApiError:
    message = _problem_details_message(model.title, model.detail, model.errors)
    return exceptions.KSeFApiError(
        status_code=model.status,
        exception_code=ExceptionCode.UNKNOWN_ERROR,
        message=message,
        response=model,
    )


@_from_problem_spec.register
def _(
    model: spec.UnauthorizedProblemDetails,
    _retry_after: int | None = None,
) -> exceptions.KSeFAuthError:
    message = _problem_details_message(model.title, model.detail)
    return exceptions.KSeFAuthError(
        status_code=model.status,
        message=message,
        response=model,
    )


@_from_problem_spec.register
def _(
    model: spec.ForbiddenProblemDetails,
    _retry_after: int | None = None,
) -> exceptions.KSeFAuthError:
    message = _problem_details_message(model.title, model.detail)
    return exceptions.KSeFAuthError(
        status_code=model.status,
        message=message,
        response=model,
    )


@_from_problem_spec.register
def _(
    model: spec.GoneProblemDetails,
    _retry_after: int | None = None,
) -> exceptions.KSeFApiError:
    message = _problem_details_message(model.title, model.detail)
    return exceptions.KSeFApiError(
        status_code=model.status,
        exception_code=ExceptionCode.UNKNOWN_ERROR,
        message=message,
        response=model,
    )


@_from_problem_spec.register
def _(
    model: spec.TooManyRequestsProblemDetails,
    retry_after: int | None = None,
) -> exceptions.KSeFRateLimitError:
    message = _problem_details_message(model.title, model.detail)
    return exceptions.KSeFRateLimitError(
        retry_after=retry_after,
        message=message,
        response=model,
    )
