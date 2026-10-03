"""Shared type aliases for transport, middleware, and endpoint layers."""

from collections.abc import Mapping, Sequence

type JsonObject = dict[str, object]
type QueryParamValue = (
    str | int | float | bool | None | Sequence[str | int | float | bool]
)
type QueryParamsInput = Mapping[str, QueryParamValue]
type Headers = dict[str, str]
type HeadersInput = Mapping[str, str]
