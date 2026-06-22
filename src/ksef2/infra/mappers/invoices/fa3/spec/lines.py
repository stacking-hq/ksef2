"""Mappings from FA(3) invoice line schema models to domain objects."""

from datetime import date, datetime
from decimal import Decimal
from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3.body import MarginProcedure
from ksef2.domain.models.fa3.body import InvoiceRow, TaxRegime, VatClassification
from ksef2.domain.models.fa3.body.order import AdvanceOrderLine
from ksef2.infra.mappers.helpers import to_aware_datetime
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaFaWiersz,
    FakturaFaZamowienieZamowienieWiersz,
    TstawkaPodatku,
)


def _to_decimal(value: str | Decimal | None) -> Decimal | None:
    if value is None or isinstance(value, Decimal):
        return value
    return Decimal(value)


def _tax_regime_for_line(
    *,
    margin_procedure: MarginProcedure | None = None,
    vat_classification: VatClassification | None = None,
    vat_rate_xii: Decimal | None = None,
) -> TaxRegime:
    if vat_rate_xii is not None:
        return TaxRegime.SPECIAL_XII
    if margin_procedure is not None and vat_classification is None:
        return TaxRegime.MARGIN
    return TaxRegime.STANDARD


def _classification_from_schema(
    code: TstawkaPodatku | None,
) -> VatClassification | None:
    if code is None:
        return None
    return VatClassification.from_schema_code(code.value)


def _parse_schema_date(value: str | date | datetime | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value)
    if "T" in text:
        return to_aware_datetime(text).date()
    return date.fromisoformat(text)


@overload
def from_spec(
    schema: FakturaFaFaWiersz,
    *,
    margin_procedure: MarginProcedure | None = None,
) -> InvoiceRow: ...


@overload
def from_spec(
    schema: FakturaFaZamowienieZamowienieWiersz,
) -> AdvanceOrderLine: ...


@overload
def from_spec(
    schema: object,
    *,
    margin_procedure: MarginProcedure | None = None,
) -> object: ...


def from_spec(
    schema: object,
    *,
    margin_procedure: MarginProcedure | None = None,
) -> object:
    """Convert FA(3) line schema models into domain rows."""
    if isinstance(schema, FakturaFaZamowienieZamowienieWiersz):
        return _from_spec(schema)
    return _from_spec(schema, margin_procedure=margin_procedure)


@singledispatch
def _from_spec(
    schema: object,
    *,
    margin_procedure: MarginProcedure | None = None,
) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        "Expected FakturaFaFaWiersz or FakturaFaZamowienieZamowienieWiersz."
    )


@_from_spec.register
def _(
    schema: FakturaFaFaWiersz,
    *,
    margin_procedure: MarginProcedure | None = None,
) -> InvoiceRow:
    vat_classification = _classification_from_schema(schema.p_12)
    tax_regime = _tax_regime_for_line(
        margin_procedure=margin_procedure,
        vat_classification=vat_classification,
        vat_rate_xii=schema.p_12_xii,
    )

    return InvoiceRow(
        name=schema.p_7,
        quantity=_to_decimal(schema.p_8_b),
        unit_of_measure=schema.p_8_a or "szt",
        unit_price_net=_to_decimal(schema.p_9_a),
        vat_classification=vat_classification,
        sale_category=vat_classification.sale_category if vat_classification else None,
        vat_rate=vat_classification.vat_rate if vat_classification else None,
        tax_regime=tax_regime,
        supply_date=_parse_schema_date(schema.p_6_a),
        discount_amount=_to_decimal(schema.p_10),
        net_amount=_to_decimal(schema.p_11),
        gross_amount=_to_decimal(schema.p_11_a),
        vat_amount=_to_decimal(schema.p_11_vat),
        unit_price_gross=_to_decimal(schema.p_9_b),
        vat_rate_xii=schema.p_12_xii,
        annex_15_marker=schema.p_12_zal_15 in {Twybor1.VALUE_1, Twybor12.VALUE_1},
        excise_amount=_to_decimal(schema.kwota_akcyzy),
        unique_id=schema.uu_id,
        sku=schema.indeks,
        gtin=schema.gtin,
        pkwiu=schema.pkwi_u,
        cn=schema.cn,
        pkob=schema.pkob,
        gtu_code=schema.gtu.name if schema.gtu is not None else None,
        procedure=schema.procedura.name if schema.procedura is not None else None,
        currency_exchange_rate=_to_decimal(schema.kurs_waluty),
        before_correction=schema.stan_przed in {Twybor1.VALUE_1, Twybor12.VALUE_1},
    )


@_from_spec.register
def _(
    schema: FakturaFaZamowienieZamowienieWiersz,
) -> AdvanceOrderLine:
    vat_classification = _classification_from_schema(schema.p_12_z)
    tax_regime = _tax_regime_for_line(vat_rate_xii=schema.p_12_z_xii)

    return AdvanceOrderLine(
        name=schema.p_7_z,
        quantity=_to_decimal(schema.p_8_bz),
        unit_of_measure=schema.p_8_az,
        gross_amount=None,
        vat_classification=vat_classification,
        vat_rate=vat_classification.vat_rate if vat_classification else None,
        sale_category=vat_classification.sale_category if vat_classification else None,
        tax_regime=tax_regime,
        unit_price_net=_to_decimal(schema.p_9_az),
        net_amount=_to_decimal(schema.p_11_netto_z),
        vat_amount=_to_decimal(schema.p_11_vat_z),
        vat_rate_xii=schema.p_12_z_xii,
        annex_15_marker=schema.p_12_z_zal_15 in {Twybor1.VALUE_1, Twybor12.VALUE_1},
        unique_id=schema.uu_idz,
        sku=schema.indeks_z,
        gtin=schema.gtinz,
        pkwiu=schema.pkwi_uz,
        cn=schema.cnz,
        pkob=schema.pkobz,
        gtu_code=schema.gtuz.name if schema.gtuz is not None else None,
        procedure=schema.procedura_z.name if schema.procedura_z is not None else None,
        excise_amount=_to_decimal(schema.kwota_akcyzy_z),
        before_correction=schema.stan_przed_z in {Twybor1.VALUE_1, Twybor12.VALUE_1},
    )


__all__ = ["from_spec"]
