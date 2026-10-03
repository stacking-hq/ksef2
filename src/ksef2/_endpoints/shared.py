from collections.abc import Mapping
from typing import Protocol, cast
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, TypeAdapter, ValidationError

from ksef2._core import codecs, exceptions
from ksef2._domain.types import OffsetPaginationQueryParams


class QueryParamsAdapter(Protocol):
    def validate_python(self, value: object, /) -> Mapping[str, object]: ...


DEFAULT_PARAMS_ADAPTER = cast(
    QueryParamsAdapter, cast(object, TypeAdapter(OffsetPaginationQueryParams))
)


def parse_response[T: BaseModel](response: httpx.Response, response_type: type[T]) -> T:
    try:
        return codecs.JsonResponseCodec.parse(response, response_type)
    except ValidationError as e:
        raise exceptions.KSeFValidationError("Invalid response payload") from e


def parse_response_list[T: BaseModel](
    response: httpx.Response, response_type: type[T]
) -> list[T]:
    try:
        return codecs.JsonResponseCodec.parse_list(response, response_type)
    except ValidationError as e:
        raise exceptions.KSeFValidationError("Invalid response payload") from e


def build_params(
    params: Mapping[str, object],
    adapter: QueryParamsAdapter | None = None,
) -> httpx.QueryParams:
    validated = (adapter or DEFAULT_PARAMS_ADAPTER).validate_python(params)
    filtered = {key: value for key, value in validated.items() if value is not None}
    return httpx.QueryParams(urlencode(filtered, doseq=True))
