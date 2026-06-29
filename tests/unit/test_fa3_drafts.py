from datetime import date, datetime, timezone
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, KsefInvoiceDraft, VatRate


def test_fa3_builder_can_roundtrip_partial_draft_json() -> None:
    draft_json = (
        FA3InvoiceBuilder()
        .header(
            generation_timestamp=datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
            system_info="draft json test",
        )
        .seller(
            name="ACME S.A.",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="ul. Przykladowa 123",
        )
        .dump_state_json(indent=2)
    )

    restored_draft = KsefInvoiceDraft.model_validate_json(draft_json)
    restored_builder = FA3InvoiceBuilder.from_state_json(draft_json)

    assert restored_draft.buyer is None
    assert restored_draft.body is None
    assert restored_draft.seller is not None
    assert restored_draft.seller.tax_id == "1234567890"

    invoice = (
        restored_builder.buyer(
            name="XYZ GmbH",
            country_code="DE",
            address_line_1="Unter den Linden 1",
        )
        .standard()
        .issue_date(date(2026, 4, 8))
        .invoice_number("FV/2026/04/0001")
        .rows()
        .add_line(
            name="Consulting service",
            quantity=Decimal("1"),
            unit_of_measure="h",
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
        .build()
    )

    assert invoice.body.invoice_number == "FV/2026/04/0001"
    assert invoice.body.rows[0].vat_rate is VatRate.VAT_23


def test_fa3_builder_can_reload_existing_sections_and_continue_editing() -> None:
    builder = FA3InvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
            system_info="draft reload test",
        )
        .seller(
            name="ACME S.A.",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="ul. Przykladowa 123",
        )
        .buyer(
            name="XYZ GmbH",
            country_code="DE",
            address_line_1="Unter den Linden 1",
        )
    )
    _ = builder.footer().add_information("Original footer note").done()
    _ = (
        builder.standard()
        .issue_date(date(2026, 4, 8))
        .invoice_number("FV/2026/04/0002")
        .rows()
        .add_line(
            name="Initial line",
            quantity=Decimal("1"),
            unit_of_measure="h",
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .payment()
        .via("bank_transfer")
        .bank_account("PL10101010101010101010101010")
        .done()
        .done()
    )

    restored_builder = FA3InvoiceBuilder.from_state(builder.dump_state())
    _ = restored_builder.footer().add_information("Updated footer note").done()
    _ = (
        restored_builder.standard()
        .rows()
        .add_line(
            name="Follow-up line",
            quantity=Decimal("2"),
            unit_of_measure="h",
            unit_price_net=Decimal("50.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .payment()
        .due_on(date(2026, 4, 15))
        .done()
        .done()
    )

    invoice = restored_builder.build()

    assert invoice.footer is not None
    assert invoice.footer.additional_informations == [
        "Original footer note",
        "Updated footer note",
    ]
    assert len(invoice.body.rows) == 2
    assert invoice.body.payment is not None
    assert invoice.body.payment.payment_form == "bank_transfer"
    assert invoice.body.payment.payment_terms[0].due_date == date(2026, 4, 15)


def test_fa3_draft_can_be_created_from_built_invoice() -> None:
    invoice = (
        FA3InvoiceBuilder()
        .header(
            generation_timestamp=datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
            system_info="invoice snapshot test",
        )
        .seller(
            name="ACME S.A.",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="ul. Przykladowa 123",
        )
        .buyer(
            name="XYZ GmbH",
            country_code="DE",
            address_line_1="Unter den Linden 1",
        )
        .standard()
        .issue_date(date(2026, 4, 8))
        .invoice_number("FV/2026/04/0003")
        .rows()
        .add_line(
            name="Consulting service",
            quantity=Decimal("1"),
            unit_of_measure="h",
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
        .build()
    )

    draft = KsefInvoiceDraft.from_invoice(invoice)
    restored_builder = FA3InvoiceBuilder.from_state(draft)

    assert restored_builder.build() == invoice
