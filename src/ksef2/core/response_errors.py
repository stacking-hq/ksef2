from collections.abc import Mapping

import httpx
from pydantic import BaseModel, ValidationError

from ksef2.infra.mappers import exceptions as mapper
from ksef2.infra.schema.api import spec

_PROBLEM_DETAILS_CONTENT_TYPE = "application/problem+json"

_PROBLEM_MODELS: dict[int, type[BaseModel]] = {
    400: spec.BadRequestProblemDetails,
    401: spec.UnauthorizedProblemDetails,
    403: spec.ForbiddenProblemDetails,
    410: spec.GoneProblemDetails,
    429: spec.TooManyRequestsProblemDetails,
}


def _try_parse[T: BaseModel](content: str, model: type[T]) -> T | None:
    try:
        return model.model_validate_json(content)
    except (ValidationError, ValueError):
        return None


def _parse_retry_after(headers: Mapping[str, str]) -> int | None:
    value = headers.get("Retry-After")
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _is_problem_details(response: httpx.Response) -> bool:
    content_type = (
        response.headers["content-type"] if "content-type" in response.headers else ""
    )
    return _PROBLEM_DETAILS_CONTENT_TYPE in content_type


def _raise_for_legacy_error(response: httpx.Response) -> None:
    status = response.status_code
    raw_body = response.text

    if status == 429:
        model = _try_parse(raw_body, spec.TooManyRequestsResponse)
        retry_after = _parse_retry_after(response.headers)
        raise mapper.from_too_many_requests(model, retry_after, raw_body)

    model = _try_parse(raw_body, spec.ExceptionResponse)

    if status in (401, 403):
        raise mapper.from_auth_error(status, model, raw_body)

    if status == 400:
        raise mapper.from_bad_request(model, raw_body)

    raise mapper.from_api_error(status, model, raw_body)


def _raise_for_problem_details(response: httpx.Response) -> None:
    raw_body = response.text
    model_cls = _PROBLEM_MODELS.get(response.status_code)

    if model_cls is not None:
        model = _try_parse(raw_body, model_cls)
        if model is not None:
            retry_after = _parse_retry_after(response.headers)
            raise mapper.from_problem_spec(model, retry_after)

    _raise_for_legacy_error(response)


def raise_for_ksef_status(response: httpx.Response) -> None:
    if response.is_success:
        return

    if _is_problem_details(response):
        _raise_for_problem_details(response)
        return

    _raise_for_legacy_error(response)
