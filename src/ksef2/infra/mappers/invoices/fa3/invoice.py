"""Mappings from FA(3) invoice aggregates to generated root schema models."""

from decimal import Decimal
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import InvoiceLine, KsefInvoice
from ksef2.infra.mappers.invoices.fa3.buyer import to_spec as buyer_to_spec
from ksef2.infra.mappers.invoices.fa3.header import to_spec as header_to_spec
from ksef2.infra.mappers.invoices.fa3.seller import to_spec as seller_to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import (
    Faktura,
    FakturaFa,
    FakturaFaAdnotacje,
    FakturaFaAdnotacjeNoweSrodkiTransportu,
    FakturaFaAdnotacjePmarzy,
    FakturaFaAdnotacjeZwolnienie,
    FakturaFaFaWiersz,
    TkodWaluty,
    TrodzajFaktury,
    TstawkaPodatku,
)


def _format_decimal(value: Decimal) -> str:
    return format(value, "f")


def _map_currency(value: str) -> TkodWaluty:
    try:
        return TkodWaluty(value.upper())
    except ValueError:
        raise ValueError(f"Unsupported FA(3) currency code: {value}") from None


def _map_vat_rate(value: str) -> TstawkaPodatku:
    try:
        return TstawkaPodatku(value)
    except ValueError:
        raise ValueError(f"Unsupported FA(3) VAT rate: {value}") from None


def _map_line(line: InvoiceLine, row_number: int) -> FakturaFaFaWiersz:
    return FakturaFaFaWiersz(
        # Sequential row number.
        nr_wiersza_fa=row_number,
        # Name of good/service.
        p_7=line.name,
        # Unit of measure.
        p_8_a=line.unit_of_measure,
        # Quantity.
        p_8_b=_format_decimal(line.quantity),
        # Net unit price.
        p_9_a=_format_decimal(line.unit_price_net),
        # Net value of the line.
        p_11=_format_decimal(line.net_amount),
        # VAT amount of the line.
        p_11_vat=_format_decimal(line.vat_amount),
        # VAT rate applied.
        p_12=_map_vat_rate(line.vat_rate),
    )


def _map_adnotacje() -> FakturaFaAdnotacje:
    return FakturaFaAdnotacje(
        # Standard KSeF flag set to "2" meaning cash accounting does not apply.
        p_16=Twybor12.VALUE_2,
        # Standard KSeF flag set to "2" meaning self-billing does not apply.
        p_17=Twybor12.VALUE_2,
        # Standard KSeF flag set to "2" meaning reverse charge does not apply.
        p_18=Twybor12.VALUE_2,
        # Standard KSeF flag set to "2" meaning split-payment obligation does not apply.
        p_18_a=Twybor12.VALUE_2,
        zwolnienie=FakturaFaAdnotacjeZwolnienie(
            # Marker meaning VAT exemption does not apply to this standard invoice.
            p_19_n=Twybor1.VALUE_1,
        ),
        nowe_srodki_transportu=FakturaFaAdnotacjeNoweSrodkiTransportu(
            # Marker meaning intra-EU supply of new means of transport does not apply.
            p_22_n=Twybor1.VALUE_1,
        ),
        # Standard KSeF flag set to "2" meaning simplified triangular procedure does not apply.
        p_23=Twybor12.VALUE_2,
        pmarzy=FakturaFaAdnotacjePmarzy(
            # Marker meaning margin procedure does not apply to this standard invoice.
            p_pmarzy_n=Twybor1.VALUE_1,
        ),
    )


def _map_fa(request: KsefInvoice) -> FakturaFa:
    return FakturaFa(
        # Invoice currency code.
        kod_waluty=_map_currency(request.details.currency),
        # Invoice issue date.
        p_1=request.details.issue_date.isoformat(),
        # Sequential invoice number.
        p_2=request.details.invoice_number,
        # Total net amount for the basic VAT rate in the MVP mapping.
        p_13_1=_format_decimal(request.total_net),
        # Total VAT amount for the basic VAT rate in the MVP mapping.
        p_14_1=_format_decimal(request.total_vat),
        # Total gross amount of the invoice.
        p_15=_format_decimal(request.total_gross),
        adnotacje=_map_adnotacje(),
        # Standard VAT invoice type.
        rodzaj_faktury=TrodzajFaktury.VAT,
        fa_wiersz=[
            _map_line(line, row_number)
            for row_number, line in enumerate(request.lines, start=1)
        ],
    )


@overload
def to_spec(request: KsefInvoice) -> Faktura: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a root invoice aggregate into the FA(3) Faktura schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: KsefInvoice) -> Faktura:
    return Faktura(
        naglowek=header_to_spec(request.invoice_header),
        podmiot1=seller_to_spec(request.seller),
        podmiot2=buyer_to_spec(request.buyer),
        fa=_map_fa(request),
    )
