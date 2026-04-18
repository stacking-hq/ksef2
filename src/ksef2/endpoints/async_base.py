"""Shared parsing and query-parameter helpers for async endpoint wrappers."""

import abc
from collections.abc import Mapping
from typing import ClassVar

import httpx
from pydantic import BaseModel

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.endpoints.shared import (
    DEFAULT_PARAMS_ADAPTER,
    QueryParamsAdapter,
    build_params as build_query_params,
    parse_response,
    parse_response_list,
)


class AsyncBaseEndpoints(abc.ABC):
    _PARAMS_ADAPTER: ClassVar[QueryParamsAdapter] = DEFAULT_PARAMS_ADAPTER

    def __init__(self, transport: AsyncMiddleware):
        self._transport = transport

    @classmethod
    def _parse[T: BaseModel](
        cls, response: httpx.Response, response_type: type[T]
    ) -> T:
        return parse_response(response, response_type)

    @classmethod
    def _parse_list[T: BaseModel](
        cls, response: httpx.Response, response_type: type[T]
    ) -> list[T]:
        return parse_response_list(response, response_type)

    def build_params(
        self,
        params: Mapping[str, object],
        adapter: QueryParamsAdapter | None = None,
    ) -> httpx.QueryParams:
        return build_query_params(params, adapter or self._PARAMS_ADAPTER)
