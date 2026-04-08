"""Mappings from FA(3) system context domain models to generated schema header models."""

from datetime import datetime
from functools import singledispatch
from typing import overload

from pydantic import BaseModel
from xsdata.models.datatype import XmlDateTime

from ksef2.domain.models.fa3 import InvoiceHeader
from ksef2.infra.schema.fa3.models.schemat import (
    TkodFormularza,
    Tnaglowek,
    TnaglowekKodFormularza,
    TnaglowekWariantFormularza,
)

from ksef2.infra.mappers.helpers import to_aware_datetime


def _to_xml_generation_timestamp(value: datetime) -> XmlDateTime:
    return XmlDateTime.from_datetime(to_aware_datetime(value))


@overload
def to_spec(request: InvoiceHeader) -> Tnaglowek: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a system context domain model into the FA(3) header schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: InvoiceHeader) -> Tnaglowek:
    return Tnaglowek(
        kod_formularza=TnaglowekKodFormularza(
            value=TkodFormularza.FA,
        ),
        wariant_formularza=TnaglowekWariantFormularza.VALUE_3,
        data_wytworzenia_fa=_to_xml_generation_timestamp(request.generation_timestamp),
        system_info=request.system_info,
    )
