"""Mappings from FA(3) invoice schema models to domain objects."""

from datetime import date, datetime
from decimal import Decimal
from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3 import KsefInvoice
from ksef2.domain.models.fa3.body import (
    KsefInvoiceBody,
    InvoiceType,
    InvoiceSummaryOverrides,
)
from ksef2.domain.models.fa3.body.root import get_placeholder_invoice_number
from ksef2.domain.models.fa3.body.advance_payment import (
    AdvancePaymentInvoiceContext,
    PartialAdvancePayment,
)
from ksef2.domain.models.fa3.body.correction import CorrectionInvoiceContext
from ksef2.domain.models.fa3.body.description import AdditionalDescriptionEntry
from ksef2.domain.models.fa3.body.order import InvoiceOrder
from ksef2.domain.models.fa3.body.settlement import (
    InvoiceSettlement,
    SettlementCharge,
    SettlementDeduction,
)
from ksef2.domain.models.fa3.references import (
    AdvanceInvoiceReference,
    CorrectedInvoiceReference,
)
from ksef2.infra.mappers.invoices.fa3.spec.attachment import (
    from_spec as attachment_from_spec,
)
from ksef2.infra.mappers.invoices.fa3.spec.annotations import (
    from_spec as annotations_from_spec,
)
from ksef2.infra.mappers.invoices.fa3.spec.buyer import from_spec as buyer_from_spec
from ksef2.infra.mappers.invoices.fa3.spec.correction_party import (
    from_spec as correction_party_from_spec,
)
from ksef2.infra.mappers.invoices.fa3.spec.footer import from_spec as footer_from_spec
from ksef2.infra.mappers.invoices.fa3.spec.header import from_spec as header_from_spec
from ksef2.infra.mappers.invoices.fa3.spec.lines import from_spec as line_from_spec
from ksef2.infra.mappers.invoices.fa3.spec.payment import from_spec as payment_from_spec
from ksef2.infra.mappers.invoices.fa3.spec.seller import from_spec as seller_from_spec
from ksef2.infra.mappers.invoices.fa3.spec.third_party import (
    from_spec as third_party_from_spec,
)
from ksef2.infra.mappers.invoices.fa3.spec.transaction import (
    from_spec as transaction_from_spec,
)
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import (
    Faktura,
    FakturaFa,
    TrodzajFaktury,
)


@overload
def from_spec(schema: Faktura) -> KsefInvoice: ...


@overload
def from_spec(schema: FakturaFa) -> KsefInvoiceBody: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert FA(3) invoice schema models into the domain aggregate."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


def _to_decimal(value: Decimal | str | None) -> Decimal | None:
    if value is None or isinstance(value, Decimal):
        return value
    return Decimal(value)


def _to_required_decimal(value: Decimal | str | None, *, field_name: str) -> Decimal:
    parsed = _to_decimal(value)
    if parsed is None:
        raise ValueError(f"{field_name} is required for FA(3) mapping")
    return parsed


def _to_date(value: date | datetime | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _to_required_date(
    value: date | datetime | str | None,
    *,
    field_name: str,
) -> date:
    parsed = _to_date(value)
    if parsed is None:
        raise ValueError(f"{field_name} is required for FA(3) mapping")
    return parsed


def _enum_value(value: object, *, field_name: str) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        raise ValueError(f"{field_name} must be a string-compatible schema value")
    return raw


def _summary_overrides_from_schema(
    schema: FakturaFa,
) -> InvoiceSummaryOverrides | None:
    overrides = InvoiceSummaryOverrides(
        base_rate_net_total=_to_decimal(schema.p_13_1),
        base_rate_vat_total=_to_decimal(schema.p_14_1),
        base_rate_vat_total_pln=_to_decimal(schema.p_14_1_w),
        first_reduced_rate_net_total=_to_decimal(schema.p_13_2),
        first_reduced_rate_vat_total=_to_decimal(schema.p_14_2),
        first_reduced_rate_vat_total_pln=_to_decimal(schema.p_14_2_w),
        second_reduced_rate_net_total=_to_decimal(schema.p_13_3),
        second_reduced_rate_vat_total=_to_decimal(schema.p_14_3),
        second_reduced_rate_vat_total_pln=_to_decimal(schema.p_14_3_w),
        taxi_flat_rate_net_total=_to_decimal(schema.p_13_4),
        taxi_flat_rate_vat_total=_to_decimal(schema.p_14_4),
        taxi_flat_rate_vat_total_pln=_to_decimal(schema.p_14_4_w),
        special_procedure_xii_net_total=_to_decimal(schema.p_13_5),
        special_procedure_xii_vat_total=_to_decimal(schema.p_14_5),
        zero_rate_domestic_total=_to_decimal(schema.p_13_6_1),
        zero_rate_wdt_total=_to_decimal(schema.p_13_6_2),
        zero_rate_export_total=_to_decimal(schema.p_13_6_3),
        exempt_total=_to_decimal(schema.p_13_7),
        out_of_territory_total=_to_decimal(schema.p_13_8),
        article_100_services_total=_to_decimal(schema.p_13_9),
        reverse_charge_total=_to_decimal(schema.p_13_10),
        margin_total=_to_decimal(schema.p_13_11),
        total_gross=_to_decimal(schema.p_15),
    )
    if not any(
        value is not None for value in overrides.model_dump(mode="python").values()
    ):
        return None
    return overrides


@_from_spec.register
def _(schema: FakturaFa) -> KsefInvoiceBody:
    def flag(value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return value in {Twybor1.VALUE_1, Twybor12.VALUE_1}

    invoice_type = InvoiceType.VAT
    if schema.rodzaj_faktury == TrodzajFaktury.KOR:
        invoice_type = InvoiceType.CORRECTING
    elif schema.rodzaj_faktury == TrodzajFaktury.ZAL:
        invoice_type = InvoiceType.ZAL
    elif schema.rodzaj_faktury == TrodzajFaktury.ROZ:
        invoice_type = InvoiceType.ROZ
    elif schema.rodzaj_faktury == TrodzajFaktury.UPR:
        invoice_type = InvoiceType.UPR
    elif schema.rodzaj_faktury == TrodzajFaktury.KOR_ZAL:
        invoice_type = InvoiceType.CORRECTING_ZAL
    elif schema.rodzaj_faktury == TrodzajFaktury.KOR_ROZ:
        invoice_type = InvoiceType.CORRECTING_ROZ

    annotations = annotations_from_spec(schema.adnotacje)
    margin_procedure = annotations.margin_procedure if annotations else None
    rows_spec = list(schema.fa_wiersz or [])
    rows = [
        line_from_spec(
            row,
            margin_procedure=margin_procedure,
        )
        for row in rows_spec
    ]

    period_start = schema.okres_fa.p_6_od if schema.okres_fa else None
    period_end = schema.okres_fa.p_6_do if schema.okres_fa else None

    settlement = None
    if schema.rozliczenie is not None:
        charges = [
            SettlementCharge(
                amount=_to_required_decimal(item.kwota, field_name="rozliczenie.kwota"),
                reason=item.powod,
            )
            for item in schema.rozliczenie.obciazenia
        ]
        deductions = [
            SettlementDeduction(
                amount=_to_required_decimal(item.kwota, field_name="rozliczenie.kwota"),
                reason=item.powod,
            )
            for item in schema.rozliczenie.odliczenia
        ]
        settlement = InvoiceSettlement(
            charges=charges,
            charges_total=_to_decimal(schema.rozliczenie.suma_obciazen),
            deductions=deductions,
            deductions_total=_to_decimal(schema.rozliczenie.suma_odliczen),
            amount_due=_to_decimal(schema.rozliczenie.do_zaplaty),
            amount_to_settle=_to_decimal(schema.rozliczenie.do_rozliczenia),
        )

    correction = None
    has_correction = (
        schema.przyczyna_korekty is not None
        or schema.typ_korekty is not None
        or schema.dane_fa_korygowanej
        or schema.okres_fa_korygowanej is not None
        or schema.nr_fa_korygowany is not None
        or schema.podmiot1_k is not None
        or schema.podmiot2_k
    )
    if has_correction:
        corrected_invoices = [
            CorrectedInvoiceReference(
                issue_date=_to_required_date(
                    item.data_wyst_fa_korygowanej,
                    field_name="dane_fa_korygowanej.data_wyst_fa_korygowanej",
                ),
                invoice_number=item.nr_fa_korygowanej,
                ksef_id=item.nr_kse_ffa_korygowanej,
                outside_ksef=flag(item.nr_kse_fn),
            )
            for item in schema.dane_fa_korygowanej
        ]
        correction_effect = None
        if schema.typ_korekty is not None:
            if schema.typ_korekty.name == "VALUE_1":
                correction_effect = "original_entry_date"
            elif schema.typ_korekty.name == "VALUE_2":
                correction_effect = "correction_issue_date"
            else:
                correction_effect = "other_date"
        correction = CorrectionInvoiceContext(
            correction_reason=schema.przyczyna_korekty,
            correction_effect_type=correction_effect,
            corrected_invoices=corrected_invoices,
            corrected_invoice_period=schema.okres_fa_korygowanej,
            corrected_invoice_number_override=schema.nr_fa_korygowany,
            corrected_seller=correction_party_from_spec(schema.podmiot1_k)
            if schema.podmiot1_k
            else None,
            corrected_buyers=[
                correction_party_from_spec(buyer) for buyer in schema.podmiot2_k
            ],
        )

    advance = None
    has_advance = (
        schema.p_15_zk is not None
        or schema.kurs_waluty_zk is not None
        or schema.zaliczka_czesciowa
        or schema.faktura_zaliczkowa
    )
    if has_advance:
        partial_payments = [
            PartialAdvancePayment(
                payment_date=_to_required_date(
                    item.p_6_z,
                    field_name="zaliczka_czesciowa.p_6_z",
                ),
                amount=_to_required_decimal(
                    item.p_15_z,
                    field_name="zaliczka_czesciowa.p_15_z",
                ),
                currency_exchange_rate=_to_decimal(item.kurs_waluty_zw),
            )
            for item in schema.zaliczka_czesciowa
        ]
        references = [
            AdvanceInvoiceReference(
                ksef_id=item.nr_kse_ffa_zaliczkowej,
                invoice_number=item.nr_fa_zaliczkowej,
                outside_ksef=flag(item.nr_kse_fzn),
            )
            for item in schema.faktura_zaliczkowa
        ]
        advance = AdvancePaymentInvoiceContext(
            amount_before_correction=_to_decimal(schema.p_15_zk),
            currency_exchange_rate_before_correction=_to_decimal(schema.kurs_waluty_zk),
            advance_partial_payments=partial_payments,
            advance_invoice_references=references,
        )

    order = None
    if schema.zamowienie is not None:
        order_lines = [
            line_from_spec(row) for row in schema.zamowienie.zamowienie_wiersz
        ]
        order = InvoiceOrder(
            total_value=_to_decimal(schema.zamowienie.wartosc_zamowienia),
            order_lines=order_lines,
        )
    return KsefInvoiceBody(
        currency=_enum_value(schema.kod_waluty, field_name="kod_waluty"),
        issue_date=_to_required_date(schema.p_1, field_name="p_1"),
        issue_place=schema.p_1_m,
        invoice_number=schema.p_2 or get_placeholder_invoice_number(),
        warehouse_documents=list(schema.wz or []),
        date_of_supply=_to_date(schema.p_6),
        period_start=_to_date(period_start),
        period_end=_to_date(period_end),
        vat_currency_exchange_rate=_to_decimal(schema.kurs_waluty_z),
        annotations=annotations,
        invoice_type=invoice_type,
        correction=correction,
        advance=advance,
        fp_invoice=schema.fp == Twybor1.VALUE_1 if schema.fp is not None else False,
        related_party_transaction=schema.tp == Twybor1.VALUE_1
        if schema.tp is not None
        else False,
        additional_description=[
            AdditionalDescriptionEntry(
                row_number=item.nr_wiersza,
                key=item.klucz,
                value=item.wartosc,
            )
            for item in schema.dodatkowy_opis
        ],
        return_of_excise=None
        if schema.zwrot_akcyzy is None
        else schema.zwrot_akcyzy == Twybor1.VALUE_1,
        rows=rows,
        settlement=settlement,
        payment=payment_from_spec(schema.platnosc) if schema.platnosc else None,
        transaction_conditions=transaction_from_spec(schema.warunki_transakcji)
        if schema.warunki_transakcji
        else None,
        order=order,
        summary_overrides=_summary_overrides_from_schema(schema),
    )


@_from_spec.register
def _(schema: Faktura) -> KsefInvoice:
    header = header_from_spec(schema.naglowek)
    seller = seller_from_spec(schema.podmiot1)
    buyer = buyer_from_spec(schema.podmiot2)
    third_parties = [third_party_from_spec(item) for item in (schema.podmiot3 or [])]
    body = from_spec(schema.fa)
    footer = footer_from_spec(schema.stopka) if schema.stopka else None
    attachment = attachment_from_spec(schema.zalacznik) if schema.zalacznik else None

    return KsefInvoice(
        header=header,
        seller=seller,
        buyer=buyer,
        third_parties=third_parties,
        body=body,
        footer=footer,
        attachment=attachment,
    )


__all__ = ["from_spec"]
