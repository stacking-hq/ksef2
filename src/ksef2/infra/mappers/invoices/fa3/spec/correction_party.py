"""Mappings for FA(3) correction-specific party blocks from schema to domain."""

from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3.body.correction import (
    CorrectedBuyerEntity,
    CorrectedSellerEntity,
)
from ksef2.infra.mappers.invoices.fa3.spec.subject import from_spec as subject_from_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.schemat import FakturaFaPodmiot1K, FakturaFaPodmiot2K


@overload
def from_spec(schema: FakturaFaPodmiot1K) -> CorrectedSellerEntity: ...


@overload
def from_spec(schema: FakturaFaPodmiot2K) -> CorrectedBuyerEntity: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert correction-specific party schema into domain objects."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: FakturaFaPodmiot1K) -> CorrectedSellerEntity:
    identity = schema.dane_identyfikacyjne
    if identity.nazwa is None:
        raise ValueError("Corrected seller name is required for FA(3) mapping")

    return CorrectedSellerEntity(
        vat_prefix=schema.prefiks_podatnika.value if schema.prefiks_podatnika else None,
        tax_id=identity.nip,
        name=identity.nazwa,
        address=subject_from_spec(schema.adres),
    )


@_from_spec.register
def _(schema: FakturaFaPodmiot2K) -> CorrectedBuyerEntity:
    identity = schema.dane_identyfikacyjne
    if identity.nazwa is None:
        raise ValueError("Corrected buyer name is required for FA(3) mapping")
    eu_vat_id = (
        f"{identity.kod_ue.value}{identity.nr_vat_ue}"
        if identity.kod_ue is not None and identity.nr_vat_ue is not None
        else None
    )

    return CorrectedBuyerEntity(
        tax_id=identity.nip,
        eu_vat_id=eu_vat_id,
        country_code=identity.kod_kraju.value if identity.kod_kraju else None,
        other_id=identity.nr_id,
        no_id=identity.brak_id == Twybor1.VALUE_1,
        name=identity.nazwa,
        address=subject_from_spec(schema.adres) if schema.adres else None,
        buyer_id=schema.idnabywcy,
    )
