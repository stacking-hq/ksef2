"""Mappings from FA(3) invoice line domain models to generated schema row models."""

from decimal import Decimal
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import AdvanceOrderLine
from ksef2.domain.models.fa3.body import SaleCategory, VatRate, InvoiceRow
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
    amount: Decimal | None, vat_rate: str | VatRate
) -> str | None:
    raw_vat_rate = vat_rate.value if isinstance(vat_rate, VatRate) else vat_rate
    if raw_vat_rate in {
        VatRate.EXEMPT.value,
        VatRate.NOT_SUBJECT.value,
        VatRate.REVERSE_CHARGE.value,
    }:
        return None
    return _format_decimal(amount)


def _map_vat_rate(
    value: str | VatRate | None, sale_category: str | SaleCategory
) -> TstawkaPodatku | None:
    if value is None:
        return None
    if isinstance(value, VatRate):
        raw_value = value.value
    else:
        raw_value = value
    if isinstance(sale_category, SaleCategory):
        category = sale_category.value
    else:
        category = sale_category

    if raw_value == VatRate.VAT_0.value:
        if category == SaleCategory.ZERO_WDT.value:
            raw_value = TstawkaPodatku.VALUE_0_WDT.value
        elif category == SaleCategory.ZERO_EXPORT.value:
            raw_value = TstawkaPodatku.VALUE_0_EX.value
        else:
            raw_value = TstawkaPodatku.VALUE_0_KR.value
    elif raw_value == VatRate.NOT_SUBJECT.value:
        if category == SaleCategory.ARTICLE_100.value:
            raw_value = TstawkaPodatku.NP_II.value
        else:
            raw_value = TstawkaPodatku.NP_I.value

    try:
        return TstawkaPodatku(raw_value)
    except ValueError:
        raise ValueError(f"Unsupported FA(3) VAT rate: {raw_value}") from None


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


@overload
def to_spec(request: InvoiceRow, row_number: int) -> FakturaFaFaWiersz: ...


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
        # Sequential number identifying the row in the invoice.
        nr_wiersza_fa=row_number,
        # Universal unique identifier assigned to the invoice row.
        uu_id=request.unique_id,
        # Per-line supply/completion date when it differs from the invoice issue date.
        p_6_a=request.supply_date.isoformat()
        if request.supply_date is not None
        else None,
        # Name of the good or service.
        p_7=request.name,
        # Internal commercial index/SKU of the product.
        indeks=request.sku,
        # Global Trade Item Number, usually EAN barcode.
        gtin=request.gtin,
        # PKWiU classification code used for Polish tax classification.
        pkwi_u=request.pkwiu,
        # CN classification code used for EU customs/tax classification.
        cn=request.cn,
        # PKOB construction classification code when relevant for the line.
        pkob=request.pkob,
        # Unit of measure used.
        p_8_a=request.unit_of_measure,
        # Quantity of delivered goods or services.
        p_8_b=_format_decimal(request.quantity),
        # Net unit price of the good or service.
        p_9_a=_format_decimal(request.unit_price_net),
        # Gross unit price used only in special gross-pricing scenarios.
        p_9_b=_format_decimal(request.unit_price_gross),
        # Amount of price reduction/discount applied to the line.
        p_10=_format_decimal(request.discount_amount)
        if request.discount_amount not in {None, Decimal("0.00")}
        else None,
        # Total net value of the line item.
        p_11=_format_decimal(request.net_amount),
        # Total gross value of the line item for gross-pricing scenarios.
        p_11_a=_format_decimal(request.gross_amount),
        # Total VAT tax amount for this line item.
        p_11_vat=_format_line_vat_amount(request.vat_amount, request.vat_rate),
        # VAT rate applied, e.g. "23" or "zw".
        p_12=_map_vat_rate(request.vat_rate, request.sale_category),
        # VAT-on-e-commerce percentage used for the special Title XII regime.
        p_12_xii=request.vat_rate_xii,
        # Annex 15 marker where value "1" means the line belongs to Annex 15.
        p_12_zal_15=_map_checkbox(request.annex_15_marker),
        # Excise tax amount included in the line price.
        kwota_akcyzy=_format_decimal(request.excise_amount),
        # Goods and Services Tax Group marker, e.g. GTU_12 for electronics.
        gtu=_map_gtu(request.gtu_code),
        # Special tax procedure marker for the line.
        procedura=_map_procedure(request.procedure),
        # Exchange rate used to calculate VAT for foreign-currency cases.
        kurs_waluty=_format_decimal(request.currency_exchange_rate),
        # Marker meaning this row shows the state before correction on a correcting invoice.
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
        p_11_vat_z=_format_decimal(request.vat_amount),
        p_12_z=_map_vat_rate(request.vat_rate, request.sale_category),
        p_12_z_xii=request.vat_rate_xii,
        p_12_z_zal_15=_map_checkbox(request.annex_15_marker),
        gtuz=_map_gtu(request.gtu_code),
        procedura_z=_map_order_procedure(request.procedure),
        kwota_akcyzy_z=_format_decimal(request.excise_amount),
        stan_przed_z=_map_checkbox(request.before_correction),
    )
