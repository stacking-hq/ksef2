"""Mappings from FA(3) invoice line domain models to generated schema row models."""

from decimal import Decimal
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import InvoiceLine
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaFaWiersz,
    Tgtu,
    ToznaczenieProcedury,
    TstawkaPodatku,
)


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def _map_vat_rate(value: str) -> TstawkaPodatku:
    try:
        return TstawkaPodatku(value)
    except ValueError:
        raise ValueError(f"Unsupported FA(3) VAT rate: {value}") from None


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


def _map_checkbox(value: bool | None) -> Twybor1 | None:
    if value:
        return Twybor1.VALUE_1
    return None


@overload
def to_spec(request: InvoiceLine, row_number: int) -> FakturaFaFaWiersz: ...


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
def _(request: InvoiceLine, row_number: int) -> FakturaFaFaWiersz:
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
        p_10=_format_decimal(request.discount_amount),
        # Total net value of the line item.
        p_11=_format_decimal(request.net_amount),
        # Total gross value of the line item for gross-pricing scenarios.
        p_11_a=_format_decimal(request.gross_amount),
        # Total VAT tax amount for this line item.
        p_11_vat=_format_decimal(request.vat_amount),
        # VAT rate applied, e.g. "23" or "zw".
        p_12=_map_vat_rate(request.vat_rate),
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
