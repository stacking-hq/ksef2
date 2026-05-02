"""Shared FA(3) subject mappers."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import InvoiceAddress
from ksef2.infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2.infra.schema.fa3.models.schemat import Tadres


def _to_country_code(value: str | None) -> TkodKraju | None:
    if value is None:
        return None
    try:
        return TkodKraju[value.upper()]
    except KeyError:
        raise ValueError(f"Unsupported FA(3) country code: {value}") from None


@overload
def to_spec(request: InvoiceAddress) -> Tadres: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a public address model into the FA(3) address schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: InvoiceAddress) -> Tadres:
    return Tadres(
        kod_kraju=_to_country_code(request.country_code),
        adres_l1=request.address_line_1,
        adres_l2=request.address_line_2,
        gln=request.gln,
    )
