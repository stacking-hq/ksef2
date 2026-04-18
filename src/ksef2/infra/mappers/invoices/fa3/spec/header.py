"""Mappings from FA(3) header schema models to domain objects."""

from datetime import datetime
from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3 import InvoiceHeader
from ksef2.domain.models.fa3.header import _default_system_info
from ksef2.infra.schema.fa3.models.schemat import Tnaglowek


@overload
def from_spec(schema: Tnaglowek) -> InvoiceHeader: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert an FA(3) header schema model into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: Tnaglowek) -> InvoiceHeader:
    raw = schema.data_wytworzenia_fa
    timestamp = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))
    return InvoiceHeader(
        generation_timestamp=timestamp,
        system_info=schema.system_info or _default_system_info(),
    )
