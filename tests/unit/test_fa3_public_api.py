from datetime import date
from decimal import Decimal

import pytest

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


def test_fa3_public_builder_builds_gross_priced_line() -> None:
    invoice = (
        FA3InvoiceBuilder()
        .header(system_info="public api gross test")
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
        .invoice_number("FV/2026/03/0002")
        .rows()
        .add_line(
            name="Gross-priced service",
            quantity=Decimal("2"),
            unit_of_measure="h",
            unit_price_gross=Decimal("123.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
        .build()
    )

    row = invoice.body.rows[0]
    assert row.unit_price_net is None
    assert row.unit_price_gross == Decimal("123.00")
    assert row.gross_amount == Decimal("246.00")
    assert row.net_amount == Decimal("200.00")
    assert row.vat_amount == Decimal("46.00")


def test_fa3_public_builder_rejects_ambiguous_unit_price_inputs() -> None:
    rows = FA3InvoiceBuilder().standard().rows()

    with pytest.raises(ValueError, match="unit_price_net or unit_price_gross"):
        rows.add_line(
            name="Ambiguous service",
            quantity=Decimal("1"),
            unit_price_net=Decimal("100.00"),
            unit_price_gross=Decimal("123.00"),
            vat_rate=VatRate.VAT_23,
        )


def test_fa3_public_builder_requires_one_unit_price_input() -> None:
    rows = FA3InvoiceBuilder().standard().rows()

    with pytest.raises(ValueError, match="unit_price_net or unit_price_gross"):
        rows.add_line(
            name="Unpriced service",
            quantity=Decimal("1"),
            vat_rate=VatRate.VAT_23,
        )


def test_services_builders_exports_only_canonical_builder() -> None:
    import ksef2.services.builders as builders

    assert builders.__all__ == ["FA3InvoiceBuilder"]
    assert builders.FA3InvoiceBuilder is FA3InvoiceBuilder
