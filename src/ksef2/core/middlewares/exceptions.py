from collections.abc import Mapping
from typing import final, override

import httpx
from pydantic import BaseModel, ValidationError

from ksef2.core import protocols
from ksef2.core.middlewares.base import BaseMiddleware
from ksef2.core.types import Headers, JsonObject, QueryParamsInput
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


@final
class KSeFExceptionMiddleware(BaseMiddleware):
    def __init__(self, transport: protocols.Middleware) -> None:
        self._next = transport

    @staticmethod
    def _try_parse[T: BaseModel](content: str, model: type[T]) -> T | None:
        try:
            return model.model_validate_json(content)
        except (ValidationError, ValueError):
            return None

    @staticmethod
    def _parse_retry_after(headers: Mapping[str, str]) -> int | None:
        value = headers.get("Retry-After")
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _is_problem_details(cls, response: httpx.Response) -> bool:
        content_type = response.headers.get("content-type", "")
        return _PROBLEM_DETAILS_CONTENT_TYPE in content_type

    @classmethod
    def _raise_for_problem_details(cls, response: httpx.Response) -> None:
        raw_body = response.text
        status = response.status_code
        model_cls = _PROBLEM_MODELS.get(status)

        if model_cls is not None:
            model = cls._try_parse(raw_body, model_cls)
            if model is not None:
                retry_after = cls._parse_retry_after(response.headers)
                raise mapper.from_problem_spec(model, retry_after)

        cls._raise_for_legacy_error(response)

    @classmethod
    def _raise_for_legacy_error(cls, response: httpx.Response) -> None:
        status = response.status_code
        raw_body = response.text

        if status == 429:
            model = cls._try_parse(raw_body, spec.TooManyRequestsResponse)
            retry_after = cls._parse_retry_after(response.headers)
            raise mapper.from_too_many_requests(model, retry_after, raw_body)

        model = cls._try_parse(raw_body, spec.ExceptionResponse)

        if status in (401, 403):
            raise mapper.from_auth_error(status, model, raw_body)

        if status == 400:
            raise mapper.from_bad_request(model, raw_body)

        raise mapper.from_api_error(status, model, raw_body)

    @classmethod
    def _raise_for_status(cls, response: httpx.Response) -> None:
        if response.is_success:
            return

        if cls._is_problem_details(response):
            cls._raise_for_problem_details(response)
            return

        cls._raise_for_legacy_error(response)

    def _handle(self, response: httpx.Response) -> httpx.Response:
        self._raise_for_status(response)
        return response

    @override
    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Headers | None = None,
        params: QueryParamsInput | None = None,
        json: JsonObject | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        return self._handle(
            self._next.request(
                method,
                path,
                headers=headers,
                params=params,
                json=json,
                content=content,
            )
        )
