"""Mappings from FA(3) address schema models to domain objects."""

from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3 import InvoiceAddress
from ksef2.infra.schema.fa3.models.schemat import Tadres


@overload
def from_spec(schema: Tadres) -> InvoiceAddress: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert an FA(3) address schema model into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: Tadres) -> InvoiceAddress:
    return InvoiceAddress(
        country_code=schema.kod_kraju.value,
        address_line_1=schema.adres_l1,
        address_line_2=schema.adres_l2,
        gln=schema.gln,
    )
