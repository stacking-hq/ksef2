"""Mappings from FA(3) invoice aggregates to generated root schema models."""

from decimal import Decimal
from functools import singledispatch
from typing import overload, assert_never

from pydantic import BaseModel
from ksef2.domain.models.fa3.drafts import MarginProcedure
from ksef2.domain.models.fa3.body import (
    KsefInvoiceBody,
    InvoiceType,
)
from ksef2.domain.models.fa3 import KsefInvoice
from ksef2.infra.mappers.invoices.fa3.buyer import to_spec as buyer_to_spec
from ksef2.infra.mappers.invoices.fa3.header import to_spec as header_to_spec
from ksef2.infra.mappers.invoices.fa3.lines import to_spec as line_to_spec
from ksef2.infra.mappers.invoices.fa3.payment import to_spec as payment_to_spec
from ksef2.infra.mappers.invoices.fa3.seller import to_spec as seller_to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import (
    Faktura,
    FakturaFa,
    FakturaFaOkresFa,
    FakturaFaAdnotacje,
    FakturaFaAdnotacjeNoweSrodkiTransportu,
    FakturaFaAdnotacjePmarzy,
    FakturaFaAdnotacjeZwolnienie,
    FakturaFaDaneFaKorygowanej,
    FakturaFaFakturaZaliczkowa,
    FakturaFaRozliczenie,
    FakturaFaRozliczenieObciazenia,
    FakturaFaRozliczenieOdliczenia,
    FakturaFaZamowienie,
    TkodWaluty,
    TrodzajFaktury,
)


def _format_decimal(value: Decimal) -> str:
    """Formats Decimal to string for XML serialization."""
    return format(value, "f")


def _opt_dec(value: Decimal) -> str | None:
    """Returns formatted decimal, or None if zero, to keep XML clean by omitting empty tax buckets."""
    if value.is_zero():
        return None
    return _format_decimal(value)


def _map_currency(value: str) -> TkodWaluty:
    try:
        return TkodWaluty(value.upper())
    except ValueError:
        raise ValueError(f"Unsupported FA(3) currency code: {value}") from None


def _map_margin_adnotacje(
    margin_procedure: MarginProcedure | None,
) -> FakturaFaAdnotacjePmarzy:
    if margin_procedure is None:
        return FakturaFaAdnotacjePmarzy(p_pmarzy_n=Twybor1.VALUE_1)

    if margin_procedure == MarginProcedure.TRAVEL_AGENCY:
        return FakturaFaAdnotacjePmarzy(
            p_pmarzy=Twybor1.VALUE_1,
            p_pmarzy_2=Twybor1.VALUE_1,
        )
    if margin_procedure == MarginProcedure.USED_GOODS:
        return FakturaFaAdnotacjePmarzy(
            p_pmarzy=Twybor1.VALUE_1,
            p_pmarzy_3_1=Twybor1.VALUE_1,
        )
    if margin_procedure == MarginProcedure.ARTWORKS:
        return FakturaFaAdnotacjePmarzy(
            p_pmarzy=Twybor1.VALUE_1,
            p_pmarzy_3_2=Twybor1.VALUE_1,
        )
    return FakturaFaAdnotacjePmarzy(
        p_pmarzy=Twybor1.VALUE_1,
        p_pmarzy_3_3=Twybor1.VALUE_1,
    )


def _map_adnotacje(
    margin_procedure: MarginProcedure | None = None,
) -> FakturaFaAdnotacje:
    return FakturaFaAdnotacje(
        p_16=Twybor12.VALUE_2,
        p_17=Twybor12.VALUE_2,
        p_18=Twybor12.VALUE_2,
        p_18_a=Twybor12.VALUE_2,
        zwolnienie=FakturaFaAdnotacjeZwolnienie(p_19_n=Twybor1.VALUE_1),
        nowe_srodki_transportu=FakturaFaAdnotacjeNoweSrodkiTransportu(
            p_22_n=Twybor1.VALUE_1
        ),
        p_23=Twybor12.VALUE_2,
        pmarzy=_map_margin_adnotacje(margin_procedure),
    )


def _map_corrected_invoice_reference(
    issue_date: str, invoice_number: str, ksef_id: str | None, outside_ksef: bool
) -> FakturaFaDaneFaKorygowanej:
    return FakturaFaDaneFaKorygowanej(
        data_wyst_fa_korygowanej=issue_date,
        nr_fa_korygowanej=invoice_number,
        nr_kse_f=Twybor1.VALUE_1 if ksef_id is not None else None,
        nr_kse_ffa_korygowanej=ksef_id,
        nr_kse_fn=Twybor1.VALUE_1 if outside_ksef else None,
    )


def _map_advance_invoice_reference(
    *, ksef_id: str | None, invoice_number: str | None, outside_ksef: bool
) -> FakturaFaFakturaZaliczkowa:
    return FakturaFaFakturaZaliczkowa(
        nr_kse_fzn=Twybor1.VALUE_1 if outside_ksef else None,
        nr_fa_zaliczkowej=invoice_number,
        nr_kse_ffa_zaliczkowej=ksef_id,
    )


def _map_rozliczenie(request: KsefInvoiceBody) -> FakturaFaRozliczenie | None:
    charges = [
        FakturaFaRozliczenieObciazenia(
            kwota=_format_decimal(charge.amount),
            powod=charge.reason,
        )
        for charge in request.settlement_charges
    ]
    deductions = [
        FakturaFaRozliczenieOdliczenia(
            kwota=_format_decimal(deduction.amount),
            powod=deduction.reason,
        )
        for deduction in request.settlement_deductions
    ]
    deductions.extend(
        FakturaFaRozliczenieOdliczenia(
            kwota=_format_decimal(reference.deduction_amount),
            powod=reference.deduction_reason,
        )
        for reference in request.advance_invoice_references
        if reference.deduction_amount is not None
        and reference.deduction_reason is not None
    )

    if not charges and not deductions:
        return None

    balance = request.settlement_balance
    return FakturaFaRozliczenie(
        obciazenia=charges,
        suma_obciazen=_opt_dec(request.settlement_charges_total),
        odliczenia=deductions,
        suma_odliczen=_opt_dec(request.settlement_deductions_total),
        do_zaplaty=_format_decimal(balance) if balance >= Decimal("0.00") else None,
        do_rozliczenia=_format_decimal(abs(balance))
        if balance < Decimal("0.00")
        else None,
    )


def map_invoice_type(invoice_type: InvoiceType) -> TrodzajFaktury:
    match invoice_type:
        case InvoiceType.VAT:
            return TrodzajFaktury.VAT
        case InvoiceType.CORRECTING:
            return TrodzajFaktury.KOR
        case InvoiceType.ZAL:
            return TrodzajFaktury.ZAL
        case InvoiceType.ROZ:
            return TrodzajFaktury.ROZ
        case InvoiceType.UPR:
            return TrodzajFaktury.UPR
        case InvoiceType.CORRECTING_ZAL:
            return TrodzajFaktury.KOR_ZAL
        case InvoiceType.CORRECTING_ROZ:
            return TrodzajFaktury.KOR_ROZ
        case _ as unreachable:
            assert_never(unreachable)


@overload
def to_spec(request: KsefInvoice) -> Faktura: ...


@overload
def to_spec(request: KsefInvoiceBody) -> FakturaFa: ...


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
def _(request: KsefInvoiceBody) -> FakturaFa:
    faktura_fa_okres_fa = None
    if request.period_start and request.period_end:
        faktura_fa_okres_fa = FakturaFaOkresFa(
            p_6_od=request.period_start.isoformat(),
            p_6_do=request.period_end.isoformat(),
        )

    zamowienie = None
    if request.order_lines:
        zamowienie = FakturaFaZamowienie(
            wartosc_zamowienia=_format_decimal(request.total_gross),
            zamowienie_wiersz=[
                line_to_spec(line, row_number)
                for row_number, line in enumerate(request.order_lines, start=1)
            ],
        )

    return FakturaFa(
        kod_waluty=_map_currency(request.currency),
        p_1=request.issue_date.isoformat(),
        p_1_m=request.issue_place,
        p_2=request.invoice_number,
        wz=request.warehouse_documents if request.warehouse_documents else [],
        p_6=request.date_of_supply.isoformat() if request.date_of_supply else None,
        okres_fa=faktura_fa_okres_fa,
        # Mapped strictly to the SaleCategory tax buckets using _opt_dec to omit empty buckets
        p_13_1=_opt_dec(request.base_rate_net_total),
        p_14_1=_opt_dec(request.base_rate_vat_total),
        p_13_2=_opt_dec(request.first_reduced_rate_net_total),
        p_14_2=_opt_dec(request.first_reduced_rate_vat_total),
        p_13_3=_opt_dec(request.second_reduced_rate_net_total),
        p_14_3=_opt_dec(request.second_reduced_rate_vat_total),
        p_13_4=_opt_dec(request.taxi_flat_rate_net_total),
        p_14_4=_opt_dec(request.taxi_flat_rate_vat_total),
        p_13_5=_opt_dec(request.special_procedure_xii_net_total),
        p_14_5=_opt_dec(request.special_procedure_xii_vat_total),
        p_13_6_1=_opt_dec(request.zero_rate_domestic_total),
        p_13_6_2=_opt_dec(request.zero_rate_wdt_total),
        p_13_6_3=_opt_dec(request.zero_rate_export_total),
        p_13_7=_opt_dec(request.exempt_total),
        p_13_8=_opt_dec(request.out_of_territory_total),
        p_13_9=_opt_dec(request.article_100_services_total),
        p_13_10=_opt_dec(request.reverse_charge_total),
        p_13_11=_opt_dec(request.margin_total),
        # Total Gross is mandatory, always format to string even if 0.00
        p_15=_format_decimal(request.total_gross),
        # TODO: Implement p_14_1_w etc. when foreign currency to PLN conversion is added to the domain model
        kurs_waluty_z=None,
        adnotacje=_map_adnotacje(request.margin_procedure),
        rodzaj_faktury=map_invoice_type(request.invoice_type),
        przyczyna_korekty=request.correction_reason,
        dane_fa_korygowanej=[
            _map_corrected_invoice_reference(
                issue_date=reference.issue_date.isoformat(),
                invoice_number=reference.invoice_number,
                ksef_id=reference.ksef_id,
                outside_ksef=reference.outside_ksef,
            )
            for reference in request.corrected_invoices
        ],
        faktura_zaliczkowa=[
            _map_advance_invoice_reference(
                ksef_id=reference.ksef_id,
                invoice_number=reference.invoice_number,
                outside_ksef=reference.outside_ksef,
            )
            for reference in request.advance_invoice_references
        ],
        # Finally, build the actual invoice lines
        fa_wiersz=[
            line_to_spec(line, row_number)
            for row_number, line in enumerate(request.lines, start=1)
        ],
        rozliczenie=_map_rozliczenie(request),
        platnosc=payment_to_spec(request.payment) if request.payment else None,
        zamowienie=zamowienie,
    )


@_to_spec.register
def _(request: KsefInvoice) -> Faktura:
    return Faktura(
        naglowek=header_to_spec(request.invoice_header),
        podmiot1=seller_to_spec(request.seller),
        podmiot2=buyer_to_spec(request.buyer),
        fa=to_spec(request.body),  # Assuming request.details holds the KsefInvoiceBody
    )
