"""Shared parsing and query-parameter helpers for endpoint wrappers."""

import abc
from collections.abc import Mapping
from typing import ClassVar, NotRequired, TypedDict
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, TypeAdapter, ValidationError
from ksef2.core import codecs, exceptions
from ksef2.core.protocols import Middleware

OffsetPaginationQueryParams = TypedDict(
    "OffsetPaginationQueryParams",
    {
        "pageOffset": NotRequired[int | None],
        "pageSize": NotRequired[int | None],
    },
)


class BaseEndpoints(abc.ABC):
    """Base class for endpoint wrappers around the transport middleware chain."""

    _PARAMS_ADAPTER: ClassVar[TypeAdapter[OffsetPaginationQueryParams]] = TypeAdapter(
        OffsetPaginationQueryParams
    )

    def __init__(self, transport: Middleware):
        """Bind the endpoint wrapper to a transport implementation."""
        self._transport = transport

    @classmethod
    def _parse[T: BaseModel](
        cls, response: httpx.Response, response_type: type[T]
    ) -> T:
        """Parse a JSON response body into one generated schema model."""
        try:
            return codecs.JsonResponseCodec.parse(response, response_type)
        except ValidationError as e:
            raise exceptions.KSeFValidationError("Invalid response payload") from e

    @classmethod
    def _parse_list[T: BaseModel](
        cls, response: httpx.Response, response_type: type[T]
    ) -> list[T]:
        """Parse a JSON response body into a list of generated schema models."""
        try:
            return codecs.JsonResponseCodec.parse_list(response, response_type)
        except ValidationError as e:
            raise exceptions.KSeFValidationError("Invalid response payload") from e

    def build_params[T: Mapping[str, object]](
        self,
        params: T,
        adapter: TypeAdapter[T] | None = None,
    ) -> httpx.QueryParams:
        """Validate, drop ``None`` values, and encode query parameters."""
        validated = (adapter or self._PARAMS_ADAPTER).validate_python(params)
        filtered = {k: v for k, v in validated.items() if v is not None}
        return httpx.QueryParams(urlencode(filtered, doseq=True))
