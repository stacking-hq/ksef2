from datetime import date
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, KsefInvoice, VatRate


def test_fa3_public_builder_builds_invoice() -> None:
    invoice = (
        FA3InvoiceBuilder()
        .header(system_info="public api test")
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
        .issue_date(date(2026, 3, 29))
        .invoice_number("FV/2026/03/0001")
        .rows()
        .add_line(
            name="Consulting service",
            quantity=Decimal("1"),
            unit_of_measure="h",
            unit_price_net=Decimal("100"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
        .build()
    )

    assert isinstance(invoice, KsefInvoice)
    assert invoice.body.invoice_number == "FV/2026/03/0001"
    assert invoice.body.rows[0].vat_rate is VatRate.VAT_23
