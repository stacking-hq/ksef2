"""Mappings from FA(3) invoice line domain models to generated schema row models."""

from decimal import Decimal
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import AdvanceOrderLine
from ksef2.domain.models.fa3.body import InvoiceRow
from ksef2.domain.models.fa3.body.order import InvoiceOrderLine
from ksef2.domain.models.fa3.body.tax import TaxRegime, VatClassification, VatTreatment
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaFaWiersz,
    FakturaFaZamowienieZamowienieWiersz,
    Tgtu,
    ToznaczenieProcedury,
    ToznaczenieProceduryZ,
    TstawkaPodatku,
)


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def _format_line_vat_amount(
    amount: Decimal | None,
    *,
    vat_classification: VatClassification | None,
    tax_regime: TaxRegime,
) -> str | None:
    if amount is None:
        return None
    if tax_regime is TaxRegime.MARGIN:
        return None
    if vat_classification is not None and vat_classification.treatment in {
        VatTreatment.EXEMPT,
        VatTreatment.OUT_OF_SCOPE_OUTSIDE_TERRITORY,
        VatTreatment.OUT_OF_SCOPE_ARTICLE_100,
        VatTreatment.REVERSE_CHARGE,
    }:
        return None
    return _format_decimal(amount)


def _map_vat_rate(
    vat_classification: VatClassification | None,
    tax_regime: TaxRegime,
) -> TstawkaPodatku | None:
    if tax_regime in {TaxRegime.MARGIN, TaxRegime.SPECIAL_XII}:
        return None
    if vat_classification is None:
        return None
    return TstawkaPodatku(vat_classification.to_schema_code())


def _map_gtu(value: str | None) -> Tgtu | None:
    if value is None:
        return None
    try:
        return Tgtu(value.upper())
    except ValueError:
        raise ValueError(f"Unsupported FA(3) GTU code: {value}") from None


def _map_procedure(value: str | None) -> ToznaczenieProcedury | None:
    if value is None:
        return None
    try:
        return ToznaczenieProcedury(value.upper())
    except ValueError:
        raise ValueError(f"Unsupported FA(3) procedure code: {value}") from None


def _map_order_procedure(value: str | None) -> ToznaczenieProceduryZ | None:
    if value is None:
        return None
    try:
        return ToznaczenieProceduryZ(value.upper())
    except ValueError:
        raise ValueError(f"Unsupported FA(3) order procedure code: {value}") from None


def _map_checkbox(value: bool | None) -> Twybor1 | None:
    if value:
        return Twybor1.VALUE_1
    return None


def _was_explicitly_set(request: InvoiceRow, field_name: str) -> bool:
    return field_name in request.model_fields_set


@overload
def to_spec(request: InvoiceRow, row_number: int) -> FakturaFaFaWiersz: ...


@overload
def to_spec(
    request: InvoiceOrderLine, row_number: int
) -> FakturaFaZamowienieZamowienieWiersz: ...


@overload
def to_spec(request: BaseModel, row_number: int) -> object: ...


def to_spec(request: BaseModel, row_number: int) -> object:
    """Convert an invoice line domain model into the FA(3) row schema."""
    return _to_spec(request, row_number)


@singledispatch
def _to_spec(request: BaseModel, row_number: int) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: InvoiceRow, row_number: int) -> FakturaFaFaWiersz:
    return FakturaFaFaWiersz(
        nr_wiersza_fa=row_number,
        uu_id=request.unique_id,
        p_6_a=request.supply_date.isoformat()
        if request.supply_date is not None
        else None,
        p_7=request.name,
        indeks=request.sku,
        gtin=request.gtin,
        pkwi_u=request.pkwiu,
        cn=request.cn,
        pkob=request.pkob,
        p_8_a=request.unit_of_measure,
        p_8_b=_format_decimal(request.quantity),
        p_9_a=_format_decimal(request.unit_price_net),
        p_9_b=_format_decimal(request.unit_price_gross),
        p_10=_format_decimal(request.discount_amount)
        if request.discount_amount not in {None, Decimal("0.00")}
        else None,
        p_11=_format_decimal(request.net_amount),
        p_11_a=_format_decimal(request.gross_amount)
        if _was_explicitly_set(request, "gross_amount")
        else None,
        p_11_vat=_format_line_vat_amount(
            request.vat_amount,
            vat_classification=request.vat_classification,
            tax_regime=request.tax_regime,
        )
        if _was_explicitly_set(request, "vat_amount")
        else None,
        p_12=_map_vat_rate(request.vat_classification, request.tax_regime),
        p_12_xii=request.vat_rate_xii,
        p_12_zal_15=_map_checkbox(request.annex_15_marker),
        kwota_akcyzy=_format_decimal(request.excise_amount),
        gtu=_map_gtu(request.gtu_code),
        procedura=_map_procedure(request.procedure),
        kurs_waluty=_format_decimal(request.currency_exchange_rate),
        stan_przed=_map_checkbox(request.before_correction),
    )


@_to_spec.register
def _(
    request: AdvanceOrderLine, row_number: int
) -> FakturaFaZamowienieZamowienieWiersz:
    return FakturaFaZamowienieZamowienieWiersz(
        nr_wiersza_zam=row_number,
        uu_idz=request.unique_id,
        p_7_z=request.name,
        indeks_z=request.sku,
        gtinz=request.gtin,
        pkwi_uz=request.pkwiu,
        cnz=request.cn,
        pkobz=request.pkob,
        p_8_az=request.unit_of_measure,
        p_8_bz=_format_decimal(request.quantity),
        p_9_az=_format_decimal(request.unit_price_net),
        p_11_netto_z=_format_decimal(request.net_amount),
        p_11_vat_z=_format_line_vat_amount(
            request.vat_amount,
            vat_classification=request.vat_classification,
            tax_regime=request.tax_regime,
        ),
        p_12_z=_map_vat_rate(request.vat_classification, request.tax_regime),
        p_12_z_xii=request.vat_rate_xii,
        p_12_z_zal_15=_map_checkbox(request.annex_15_marker),
        gtuz=_map_gtu(request.gtu_code),
        procedura_z=_map_order_procedure(request.procedure),
        kwota_akcyzy_z=_format_decimal(request.excise_amount),
        stan_przed_z=_map_checkbox(request.before_correction),
    )
