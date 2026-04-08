from typing import Any

import pytest
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3.body import InvoicePayment, InvoiceType, KsefInvoiceBody
from ksef2.infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2.infra.schema.fa3.models.schemat import Faktura
from tests.integration.builders.helpers import load_sample
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder


SIMPLIFIED_SAMPLES = [
    "FA_3_Przykład_15.xml",
    "FA_3_Przykład_16.xml",
    "KSEF_04_UPR.xml",
]


def _has_payment(payment: InvoicePayment) -> bool:
    return any(
        [
            payment.paid,
            payment.payment_date,
            payment.partial_payment_status,
            payment.partial_payments,
            payment.payment_terms,
            payment.payment_form,
            payment.other_payment_form,
            payment.payment_description,
            payment.bank_accounts,
            payment.factor_bank_accounts,
            payment.discount_terms,
            payment.discount_amount,
            payment.payment_link,
            payment.ipksef,
        ]
    )


def _apply_body(builder: Any, body: KsefInvoiceBody) -> None:
    builder.currency(body.currency)
    builder.issue_date(body.issue_date)
    builder.issue_place(body.issue_place)
    builder.invoice_number(body.invoice_number)
    for document in body.warehouse_documents:
        builder.add_warehouse_document(document)
    if body.date_of_supply is not None:
        builder.date_of_supply(body.date_of_supply)
    if body.period_start is not None or body.period_end is not None:
        builder.billing_period(
            period_start=body.period_start,
            period_end=body.period_end,
        )
    if body.vat_currency_exchange_rate is not None:
        builder.vat_currency_exchange_rate(body.vat_currency_exchange_rate)
    if body.fp_invoice:
        builder.mark_fp()
    if body.related_party_transaction:
        builder.related_party_transaction()
    if body.return_of_excise is not None:
        builder.return_of_excise(body.return_of_excise)
    for entry in body.additional_description:
        builder.add_description(
            key=entry.key,
            value=entry.value,
            row_number=entry.row_number,
        )
    if hasattr(builder, "rows") and body.rows:
        builder.rows().from_model(body.rows).done()
    if hasattr(builder, "order") and body.order is not None:
        builder.order().from_model(body.order).done()
    if (
        hasattr(builder, "payment")
        and body.payment is not None
        and _has_payment(body.payment)
    ):
        builder.payment().from_model(body.payment).done()
    if hasattr(builder, "annotations") and body.annotations is not None:
        builder.annotations().from_model(body.annotations).done()
    if hasattr(builder, "transaction") and body.transaction_conditions is not None:
        builder.transaction().from_model(body.transaction_conditions).done()
    if hasattr(builder, "settlement") and body.settlement is not None:
        builder.settlement().from_model(body.settlement).done()
    if hasattr(builder, "correction") and body.correction is not None:
        builder.correction().from_model(body.correction).done()
    if hasattr(builder, "advance") and body.advance is not None:
        builder.advance().from_model(body.advance).done()


def _select_body_builder(
    builder: StandardInvoiceBuilder,
    invoice_type: InvoiceType,
) -> Any:
    if invoice_type == InvoiceType.VAT:
        return builder.standard()
    if invoice_type == InvoiceType.UPR:
        return builder.simplified()
    if invoice_type == InvoiceType.CORRECTING:
        return builder.correction()
    if invoice_type == InvoiceType.ZAL:
        return builder.advance()
    if invoice_type == InvoiceType.ROZ:
        return builder.settlement()
    if invoice_type == InvoiceType.CORRECTING_ZAL:
        return builder.correction_advance()
    if invoice_type == InvoiceType.CORRECTING_ROZ:
        return builder.correction_settlement()
    raise ValueError(f"Unsupported invoice type: {invoice_type}")


def _build_from_sample(sample_name: str) -> StandardInvoiceBuilder:
    faktura = load_sample(sample_name)
    invoice = invoice_from_spec(faktura)
    builder = StandardInvoiceBuilder()
    builder.header_model(invoice.header)
    builder.seller_model(invoice.seller)
    builder.buyer_model(invoice.buyer)
    for party in invoice.third_parties:
        builder.add_third_party_model(party)
    if invoice.footer is not None:
        builder.footer_model(invoice.footer)
    if invoice.attachment is not None:
        builder.attachment_model(invoice.attachment)
    body_builder = _select_body_builder(builder, invoice.body.invoice_type)
    _apply_body(body_builder, invoice.body)
    body_builder.done()
    return builder


def _assert_sample(sample_name: str) -> None:
    parser = XmlParser()
    expected = load_sample(sample_name)
    builder = _build_from_sample(sample_name)
    actual = builder.to_spec()
    expected = normalize_expected(expected, actual)

    assert actual == expected
    assert parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura) == expected


@pytest.mark.integration
@pytest.mark.parametrize("sample_name", SIMPLIFIED_SAMPLES)
def test_new_fa3_simplified_samples(sample_name: str) -> None:
    _assert_sample(sample_name)
