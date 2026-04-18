"""Mappings from FA(3) invoice aggregates to generated root schema models."""

from decimal import Decimal
from functools import singledispatch
from typing import overload, assert_never

from pydantic import BaseModel
from ksef2.domain.models.fa3.body import (
    InvoiceAnnotationsContext,
    InvoiceTaxExemption,
    KsefInvoiceBody,
    InvoiceType,
    NewTransportSupply,
)
from ksef2.domain.models.fa3 import KsefInvoice
from ksef2.infra.mappers.invoices.fa3.domain.attachment import (
    to_spec as attachment_to_spec,
)
from ksef2.infra.mappers.invoices.fa3.domain.buyer import to_spec as buyer_to_spec
from ksef2.infra.mappers.invoices.fa3.domain.correction_party import (
    to_spec as correction_party_to_spec,
)
from ksef2.infra.mappers.invoices.fa3.domain.footer import to_spec as footer_to_spec
from ksef2.infra.mappers.invoices.fa3.domain.header import to_spec as header_to_spec
from ksef2.infra.mappers.invoices.fa3.domain.lines import to_spec as line_to_spec
from ksef2.infra.mappers.invoices.fa3.domain.payment import to_spec as payment_to_spec
from ksef2.infra.mappers.invoices.fa3.domain.seller import to_spec as seller_to_spec
from ksef2.infra.mappers.invoices.fa3.domain.third_party import (
    to_spec as third_party_to_spec,
)
from ksef2.infra.mappers.invoices.fa3.domain.transaction import (
    to_spec as transaction_to_spec,
)
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
    FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu,
    FakturaFaAdnotacjePmarzy,
    FakturaFaAdnotacjeZwolnienie,
    FakturaFaDaneFaKorygowanej,
    FakturaFaFakturaZaliczkowa,
    FakturaFaRozliczenie,
    FakturaFaRozliczenieObciazenia,
    FakturaFaRozliczenieOdliczenia,
    FakturaFaZaliczkaCzesciowa,
    FakturaFaZamowienie,
    TkodWaluty,
    TkluczWartosc,
    TrodzajFaktury,
    TtypKorekty,
)


def _format_decimal(value: Decimal) -> str:
    """Formats Decimal to string for XML serialization."""
    return format(value, "f")


def _opt_dec(value: Decimal) -> str | None:
    """Returns formatted decimal, or None if zero, to keep XML clean by omitting empty tax buckets."""
    if value.is_zero():
        return None
    return _format_decimal(value)


def _opt_optional_dec(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _opt_dec(value)


def _map_currency(value: str) -> TkodWaluty:
    try:
        return TkodWaluty(value.upper())
    except ValueError:
        raise ValueError(f"Unsupported FA(3) currency code: {value}") from None


def _map_margin_adnotacje(
    margin_procedure: str | None,
) -> FakturaFaAdnotacjePmarzy:
    if margin_procedure is None:
        return FakturaFaAdnotacjePmarzy(p_pmarzy_n=Twybor1.VALUE_1)

    if margin_procedure == "travel_agency":
        return FakturaFaAdnotacjePmarzy(
            p_pmarzy=Twybor1.VALUE_1,
            p_pmarzy_2=Twybor1.VALUE_1,
        )
    if margin_procedure == "used_goods":
        return FakturaFaAdnotacjePmarzy(
            p_pmarzy=Twybor1.VALUE_1,
            p_pmarzy_3_1=Twybor1.VALUE_1,
        )
    if margin_procedure == "artworks":
        return FakturaFaAdnotacjePmarzy(
            p_pmarzy=Twybor1.VALUE_1,
            p_pmarzy_3_2=Twybor1.VALUE_1,
        )
    return FakturaFaAdnotacjePmarzy(
        p_pmarzy=Twybor1.VALUE_1,
        p_pmarzy_3_3=Twybor1.VALUE_1,
    )


def _map_adnotacje(
    annotations: InvoiceAnnotationsContext | None,
) -> FakturaFaAdnotacje:
    tax_exemption = annotations.tax_exemption if annotations else None
    new_transport_supply = annotations.new_transport_supply if annotations else None
    zwolnienie = _map_tax_exemption(tax_exemption)
    nowe_srodki_transportu = _map_new_transport_supply(new_transport_supply)

    return FakturaFaAdnotacje(
        p_16=Twybor12.VALUE_1
        if annotations and annotations.cash_accounting
        else Twybor12.VALUE_2,
        p_17=Twybor12.VALUE_1
        if annotations and annotations.self_billing
        else Twybor12.VALUE_2,
        p_18=Twybor12.VALUE_1
        if annotations and annotations.reverse_charge_annotation
        else Twybor12.VALUE_2,
        p_18_a=Twybor12.VALUE_1
        if annotations and annotations.split_payment
        else Twybor12.VALUE_2,
        zwolnienie=zwolnienie,
        nowe_srodki_transportu=nowe_srodki_transportu,
        p_23=Twybor12.VALUE_1
        if annotations and annotations.simplified_procedure
        else Twybor12.VALUE_2,
        pmarzy=_map_margin_adnotacje(
            annotations.margin_procedure if annotations else None
        ),
    )


def _map_tax_exemption(
    tax_exemption: InvoiceTaxExemption | None,
) -> FakturaFaAdnotacjeZwolnienie:
    if tax_exemption is None:
        return FakturaFaAdnotacjeZwolnienie(p_19_n=Twybor1.VALUE_1)

    return FakturaFaAdnotacjeZwolnienie(
        p_19=Twybor1.VALUE_1,
        p_19_a=tax_exemption.legal_basis_act,
        p_19_b=tax_exemption.legal_basis_eu_directive,
        p_19_c=tax_exemption.legal_basis_other,
    )


def _map_new_transport_supply(
    new_transport_supply: NewTransportSupply | None,
) -> FakturaFaAdnotacjeNoweSrodkiTransportu:
    if new_transport_supply is None:
        return FakturaFaAdnotacjeNoweSrodkiTransportu(p_22_n=Twybor1.VALUE_1)

    items = [
        FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu(
            p_22_a=item.available_from.isoformat(),
            p_nr_wiersza_nst=item.row_number,
            p_22_bmk=item.brand,
            p_22_bmd=item.model,
            p_22_bk=item.color,
            p_22_bnr=item.registration_number,
            p_22_brp=item.production_year,
            p_22_b=item.land_vehicle_mileage,
            p_22_b1=item.vin,
            p_22_b2=item.body_number,
            p_22_b3=item.chassis_number,
            p_22_b4=item.frame_number,
            p_22_bt=item.land_vehicle_type,
            p_22_c=item.vessel_working_hours,
            p_22_c1=item.hull_number,
            p_22_d=item.aircraft_working_hours,
            p_22_d1=item.aircraft_serial_number,
        )
        for item in new_transport_supply.items
    ]

    return FakturaFaAdnotacjeNoweSrodkiTransportu(
        p_22=Twybor1.VALUE_1,
        p_42_5=Twybor12.VALUE_1
        if new_transport_supply.article_42_5_required
        else Twybor12.VALUE_2
        if new_transport_supply.article_42_5_required is not None
        else None,
        nowy_srodek_transportu=items,
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


def _map_correction_effect_type(value: str | None) -> TtypKorekty | None:
    if value is None:
        return None
    if value == "original_entry_date":
        return TtypKorekty.VALUE_1
    if value == "correction_issue_date":
        return TtypKorekty.VALUE_2
    return TtypKorekty.VALUE_3


def _map_rozliczenie(request: KsefInvoiceBody) -> FakturaFaRozliczenie | None:
    settlement = request.settlement
    advance = request.advance

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
        for reference in (advance.advance_invoice_references if advance else [])
        if reference.deduction_amount is not None
        and reference.deduction_reason is not None
    )

    has_explicit_settlement_values = settlement is not None and any(
        value is not None
        for value in (
            settlement.charges_total,
            settlement.deductions_total,
            settlement.amount_due,
            settlement.amount_to_settle,
        )
    )

    if not charges and not deductions and not has_explicit_settlement_values:
        return None

    charges_total = request.settlement_charges_total
    deductions_total = request.settlement_deductions_total
    balance = request.settlement_balance
    amount_due = settlement.amount_due if settlement else None
    amount_to_settle = settlement.amount_to_settle if settlement else None
    if amount_due is None and amount_to_settle is None:
        amount_due = balance if balance >= Decimal("0.00") else None
        amount_to_settle = abs(balance) if balance < Decimal("0.00") else None

    return FakturaFaRozliczenie(
        obciazenia=charges,
        suma_obciazen=_format_decimal(charges_total)
        if charges_total is not None
        else None,
        odliczenia=deductions,
        suma_odliczen=_format_decimal(deductions_total)
        if deductions_total is not None
        else None,
        do_zaplaty=_format_decimal(amount_due) if amount_due is not None else None,
        do_rozliczenia=_format_decimal(amount_to_settle)
        if amount_to_settle is not None
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
    correction = request.correction
    advance = request.advance
    annotations = request.annotations

    faktura_fa_okres_fa = None
    if request.period_start and request.period_end:
        faktura_fa_okres_fa = FakturaFaOkresFa(
            p_6_od=request.period_start.isoformat(),
            p_6_do=request.period_end.isoformat(),
        )

    zamowienie = None
    if request.order is not None:
        if request.order.total_value is None:
            raise ValueError("order.total_value must be populated before FA(3) mapping")
        zamowienie = FakturaFaZamowienie(
            wartosc_zamowienia=_format_decimal(request.order.total_value),
            zamowienie_wiersz=[
                line_to_spec(line, row_number)
                for row_number, line in enumerate(request.order.order_lines, start=1)
            ],
        )

    corrected_seller = None
    if correction and correction.corrected_seller is not None:
        corrected_seller = correction_party_to_spec(correction.corrected_seller)

    corrected_buyers = [
        correction_party_to_spec(buyer)
        for buyer in (correction.corrected_buyers if correction else [])
    ]
    partial_advance_payments = [
        FakturaFaZaliczkaCzesciowa(
            p_6_z=payment.payment_date.isoformat(),
            p_15_z=_format_decimal(payment.amount),
            kurs_waluty_zw=_format_decimal(payment.currency_exchange_rate)
            if payment.currency_exchange_rate is not None
            else None,
        )
        for payment in (advance.advance_partial_payments if advance else [])
    ]

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
        p_14_1_w=_opt_optional_dec(request.base_rate_vat_total_pln),
        p_13_2=_opt_dec(request.first_reduced_rate_net_total),
        p_14_2=_opt_dec(request.first_reduced_rate_vat_total),
        p_14_2_w=_opt_optional_dec(request.first_reduced_rate_vat_total_pln),
        p_13_3=_opt_dec(request.second_reduced_rate_net_total),
        p_14_3=_opt_dec(request.second_reduced_rate_vat_total),
        p_14_3_w=_opt_optional_dec(request.second_reduced_rate_vat_total_pln),
        p_13_4=_opt_dec(request.taxi_flat_rate_net_total),
        p_14_4=_opt_dec(request.taxi_flat_rate_vat_total),
        p_14_4_w=_opt_optional_dec(request.taxi_flat_rate_vat_total_pln),
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
        kurs_waluty_z=_format_decimal(request.vat_currency_exchange_rate)
        if request.vat_currency_exchange_rate is not None
        else None,
        adnotacje=_map_adnotacje(annotations),
        rodzaj_faktury=map_invoice_type(request.invoice_type),
        przyczyna_korekty=correction.correction_reason if correction else None,
        typ_korekty=_map_correction_effect_type(
            correction.correction_effect_type if correction else None
        ),
        dane_fa_korygowanej=[
            _map_corrected_invoice_reference(
                issue_date=reference.issue_date.isoformat(),
                invoice_number=reference.invoice_number,
                ksef_id=reference.ksef_id,
                outside_ksef=reference.outside_ksef,
            )
            for reference in (correction.corrected_invoices if correction else [])
        ],
        okres_fa_korygowanej=(
            correction.corrected_invoice_period if correction else None
        ),
        nr_fa_korygowany=(
            correction.corrected_invoice_number_override if correction else None
        ),
        podmiot1_k=corrected_seller,
        podmiot2_k=corrected_buyers,
        p_15_zk=_format_decimal(advance.amount_before_correction)
        if advance and advance.amount_before_correction is not None
        else None,
        kurs_waluty_zk=_format_decimal(advance.currency_exchange_rate_before_correction)
        if advance and advance.currency_exchange_rate_before_correction is not None
        else None,
        zaliczka_czesciowa=partial_advance_payments,
        fp=Twybor1.VALUE_1 if request.fp_invoice else None,
        tp=Twybor1.VALUE_1 if request.related_party_transaction else None,
        dodatkowy_opis=[
            TkluczWartosc(
                nr_wiersza=entry.row_number,
                klucz=entry.key,
                wartosc=entry.value,
            )
            for entry in request.additional_description
        ],
        faktura_zaliczkowa=[
            _map_advance_invoice_reference(
                ksef_id=reference.ksef_id,
                invoice_number=reference.invoice_number,
                outside_ksef=reference.outside_ksef,
            )
            for reference in (advance.advance_invoice_references if advance else [])
        ],
        # Finally, build the actual invoice lines
        fa_wiersz=[
            line_to_spec(line, row_number)
            for row_number, line in enumerate(request.rows, start=1)
        ],
        rozliczenie=_map_rozliczenie(request),
        platnosc=payment_to_spec(request.payment) if request.payment else None,
        warunki_transakcji=transaction_to_spec(request.transaction_conditions)
        if request.transaction_conditions
        else None,
        zamowienie=zamowienie,
    )


@_to_spec.register
def _(request: KsefInvoice) -> Faktura:
    return Faktura(
        naglowek=header_to_spec(request.header),
        podmiot1=seller_to_spec(request.seller),
        podmiot2=buyer_to_spec(request.buyer),
        podmiot3=[third_party_to_spec(subject) for subject in request.third_parties],
        fa=to_spec(request.body),  # Assuming request.details holds the KsefInvoiceBody
        stopka=footer_to_spec(request.footer) if request.footer else None,
        zalacznik=attachment_to_spec(request.attachment)
        if request.attachment
        else None,
    )
