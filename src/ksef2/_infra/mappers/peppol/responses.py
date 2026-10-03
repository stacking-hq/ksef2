from enum import Enum
from functools import singledispatch
from typing import overload

from ksef2._domain.models.peppol import (
    ListPeppolProvidersResponse,
    PeppolProvider,
)
from ksef2._infra.schema.api import spec

from pydantic import BaseModel


@overload
def from_spec(
    response: spec.PeppolProvider,
) -> PeppolProvider: ...


@overload
def from_spec(
    response: spec.QueryPeppolProvidersResponse,
) -> ListPeppolProvidersResponse: ...


def from_spec(response: BaseModel | Enum) -> object:
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(response: spec.PeppolProvider) -> PeppolProvider:
    return PeppolProvider(
        id=response.id,
        name=response.name,
        date_created=response.dateCreated,
    )


@_from_spec.register
def _(
    response: spec.QueryPeppolProvidersResponse,
) -> ListPeppolProvidersResponse:
    return ListPeppolProvidersResponse(
        providers=[from_spec(p) for p in response.peppolProviders],
        has_more=response.hasMore,
    )
