"""Mappings for FA(3) correction-specific party blocks."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import CorrectedBuyerEntity, CorrectedSellerEntity
from ksef2.infra.mappers.invoices.fa3.domain.subject import to_spec as subject_to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaPodmiot1K,
    FakturaFaPodmiot2K,
    TkodyKrajowUe,
    Tpodmiot1,
    Tpodmiot2,
)


def _to_ue_country_code(value: str | None) -> TkodyKrajowUe | None:
    if value is None:
        return None

    try:
        return TkodyKrajowUe[value.upper()]
    except KeyError:
        raise ValueError(f"Unsupported FA(3) EU country code: {value}") from None


def _to_country_code(value: str | None) -> TkodKraju | None:
    if value is None:
        return None

    try:
        return TkodKraju[value.upper()]
    except KeyError:
        raise ValueError(f"Unsupported FA(3) country code: {value}") from None


def _split_eu_vat_id(eu_vat_id: str | None) -> tuple[TkodyKrajowUe | None, str | None]:
    if eu_vat_id is None:
        return None, None
    if len(eu_vat_id) < 3:
        raise ValueError("eu_vat_id must contain a 2-letter country prefix and number")

    country_prefix = eu_vat_id[:2].upper()
    vat_number = eu_vat_id[2:]

    try:
        return TkodyKrajowUe[country_prefix], vat_number
    except KeyError:
        raise ValueError(f"Unsupported FA(3) EU VAT prefix: {country_prefix}") from None


@overload
def to_spec(request: CorrectedSellerEntity) -> FakturaFaPodmiot1K: ...


@overload
def to_spec(request: CorrectedBuyerEntity) -> FakturaFaPodmiot2K: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert correction-specific party models into FA(3) schema blocks."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: CorrectedSellerEntity) -> FakturaFaPodmiot1K:
    seller_identity = Tpodmiot1(
        nip=request.tax_id,
        nazwa=request.name,
    )
    seller_address = subject_to_spec(request.address)
    seller_prefix = _to_ue_country_code(request.vat_prefix)

    return FakturaFaPodmiot1K(
        prefiks_podatnika=seller_prefix,
        dane_identyfikacyjne=seller_identity,
        adres=seller_address,
    )


@_to_spec.register
def _(request: CorrectedBuyerEntity) -> FakturaFaPodmiot2K:
    country_prefix, eu_vat_number = _split_eu_vat_id(request.eu_vat_id)
    buyer_identity = Tpodmiot2(
        nip=request.tax_id,
        kod_ue=country_prefix,
        nr_vat_ue=eu_vat_number,
        kod_kraju=_to_country_code(request.country_code),
        nr_id=request.other_id,
        brak_id=Twybor1.VALUE_1 if request.no_id else None,
        nazwa=request.name,
    )
    buyer_address = subject_to_spec(request.address) if request.address else None

    return FakturaFaPodmiot2K(
        dane_identyfikacyjne=buyer_identity,
        adres=buyer_address,
        idnabywcy=request.buyer_id,
    )
