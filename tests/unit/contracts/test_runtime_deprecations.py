import warnings
from datetime import date
from decimal import Decimal

from ksef2.fa3 import InvoiceBuilder, VatRate


def test_fa3_xml_serialization_emits_no_deprecation_warnings() -> None:
    builder = (
        InvoiceBuilder()
        .header(system_info="deprecation gate")
        .seller(
            name="Seller",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="Seller Street 1",
        )
        .buyer(
            name="Buyer",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="Buyer Street 1",
        )
        .standard()
        .issue_date(date(2026, 7, 10))
        .invoice_number("FV/2026/07/001")
        .rows()
        .add_line(
            name="Service",
            quantity=Decimal("1"),
            unit_price_net=Decimal("100"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        xml = builder.to_xml()

    assert "FV/2026/07/001" in xml
