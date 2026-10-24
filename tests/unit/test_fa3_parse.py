from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from lxml import etree

from ksef2.fa3 import (
    InvoiceBuilder,
    InvoiceSummaryOverrides,
    VatRate,
    parse_invoice_xml,
)

SAMPLES = Path(__file__).parents[2] / "schemas" / "FA3" / "samples"


@pytest.mark.parametrize(
    "filename",
    ["FA_3_Przykład_1.xml", "FA_3_Przykład_4.xml", "FA_3_Przykład_8.xml"],
)
def test_parse_and_rebuild_public_invoice(filename: str) -> None:
    invoice = parse_invoice_xml((SAMPLES / filename).read_bytes())
    xml = InvoiceBuilder.from_invoice(invoice).to_xml()
    assert parse_invoice_xml(xml.encode("utf-8")) == invoice
    assert invoice.seller.tax_id
    assert invoice.body.invoice_number


@pytest.mark.parametrize(
    "xml, message",
    [
        (b"<broken>", "Failed to parse"),
        (b"<Faktura/>", "FA\\(3\\) namespace"),
        (
            b"<Faktura xmlns='http://crd.gov.pl/wzor/2023/06/29/12648/'/>",
            "FA\\(3\\) namespace",
        ),
        (
            b"<!DOCTYPE Faktura [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><Faktura>&test;</Faktura>",
            "DTD",
        ),
    ],
)
def test_parse_rejects_invalid_xml(xml: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message) as error:
        _ = parse_invoice_xml(xml)
    assert error.value.__cause__ is not None


def test_parse_preserves_xml_declared_encoding() -> None:
    xml = (SAMPLES / "FA_3_Przykład_1.xml").read_bytes()
    text = xml.decode("utf-8").replace('encoding="UTF-8"', 'encoding="ISO-8859-2"')
    assert parse_invoice_xml(text.encode("iso-8859-2")) == parse_invoice_xml(xml)


@pytest.mark.parametrize("vat_rate", [VatRate.VAT_23, VatRate.VAT_8, VatRate.VAT_5])
def test_builder_emits_zero_vat_bucket_for_small_line(vat_rate: VatRate) -> None:
    builder = (
        InvoiceBuilder()
        .header(system_info="small VAT bucket")
        .seller(
            name="Seller",
            tax_id="5261040828",
            country_code="PL",
            address_line_1="a",
            address_line_2="b",
        )
        .buyer(
            name="Buyer",
            tax_id="5250001009",
            country_code="PL",
            address_line_1="a",
            address_line_2="b",
        )
        .standard()
        .issue_date(date(2026, 10, 24))
        .issue_place("X")
        .invoice_number("SMALL/1")
        .rows()
        .add_line(
            name="Small line",
            quantity=Decimal("1"),
            unit_price_net=Decimal("0.01"),
            vat_rate=vat_rate,
        )
        .done()
        .done()
    )

    xml = builder.to_xml()
    document = etree.fromstring(xml.encode("utf-8"))
    bucket_number = {
        VatRate.VAT_23: "1",
        VatRate.VAT_8: "2",
        VatRate.VAT_5: "3",
    }[vat_rate]
    assert document.xpath(f"//*[local-name()='P_13_{bucket_number}']/text()") == [
        "0.01"
    ]
    assert document.xpath(f"//*[local-name()='P_14_{bucket_number}']/text()") == [
        "0.00"
    ]


def test_builder_emits_zero_bucket_for_correction_rows_that_net_to_zero() -> None:
    builder = (
        InvoiceBuilder()
        .header(system_info="zero correction bucket")
        .seller(
            name="Seller",
            tax_id="5261040828",
            country_code="PL",
            address_line_1="a",
            address_line_2="b",
        )
        .buyer(
            name="Buyer",
            tax_id="5250001009",
            country_code="PL",
            address_line_1="a",
            address_line_2="b",
        )
        .correction()
        .issue_date(date(2026, 10, 24))
        .issue_place("X")
        .invoice_number("CORR/1")
        .summary_overrides(
            InvoiceSummaryOverrides(
                total_gross=Decimal("0.00"),
            )
        )
        .rows()
        .add_line(
            name="Before correction",
            quantity=Decimal("1"),
            unit_price_net=Decimal("0.01"),
            vat_rate=VatRate.VAT_23,
            before_correction=True,
        )
        .add_line(
            name="After correction",
            quantity=Decimal("1"),
            unit_price_net=Decimal("0.01"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .correction()
        .reason("Net-zero correction test")
        .effect_type("other_date")
        .add_corrected_invoice(
            issue_date=date(2026, 10, 1),
            invoice_number="INV/1",
            outside_ksef=True,
        )
        .done()
        .done()
    )

    xml = builder.to_xml()
    document = etree.fromstring(xml.encode("utf-8"))
    assert document.xpath("//*[local-name()='P_13_1']/text()") == ["0.00"]
    assert document.xpath("//*[local-name()='P_14_1']/text()") == ["0.00"]


def _foreign_currency_invoice_builder() -> InvoiceBuilder:
    return (
        InvoiceBuilder()
        .header(system_info="foreign currency")
        .seller(
            name="Seller",
            tax_id="5261040828",
            country_code="PL",
            address_line_1="a",
        )
        .buyer(
            name="Buyer",
            tax_id="5250001009",
            country_code="PL",
            address_line_1="a",
        )
    )


def test_builder_requires_exchange_rate_for_foreign_currency_without_alternatives() -> (
    None
):
    builder = (
        _foreign_currency_invoice_builder()
        .standard()
        .currency("EUR")
        .rows()
        .add_line(
            name="Line",
            quantity=Decimal("1"),
            unit_price_net=Decimal("1.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
    )
    with pytest.raises(
        ValueError,
        match="Foreign-currency invoices require a body or row exchange rate",
    ):
        _ = builder.build()


def test_builder_accepts_foreign_currency_with_per_row_exchange_rate() -> None:
    builder = (
        _foreign_currency_invoice_builder()
        .standard()
        .currency("EUR")
        .rows()
        .add_line(
            name="Line",
            quantity=Decimal("1"),
            unit_price_net=Decimal("1.00"),
            vat_rate=VatRate.VAT_23,
            currency_exchange_rate=Decimal("4.5000"),
        )
        .done()
        .done()
    )

    xml = builder.to_xml()
    document = etree.fromstring(xml.encode("utf-8"))
    assert document.xpath("//*[local-name()='P_14_1W']/text()") == ["1.04"]


def test_builder_accepts_foreign_currency_with_pln_vat_summary_override() -> None:
    builder = (
        _foreign_currency_invoice_builder()
        .standard()
        .currency("EUR")
        .summary_overrides(
            InvoiceSummaryOverrides(base_rate_vat_total_pln=Decimal("1.04"))
        )
        .rows()
        .add_line(
            name="Line",
            quantity=Decimal("1"),
            unit_price_net=Decimal("1.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
    )

    xml = builder.to_xml()
    document = etree.fromstring(xml.encode("utf-8"))
    assert document.xpath("//*[local-name()='P_14_1W']/text()") == ["1.04"]


@pytest.mark.parametrize("kind", ["correction_advance", "correction_settlement"])
def test_public_builder_serializes_rowless_corrections(kind: str) -> None:
    invoice = parse_invoice_xml((SAMPLES / "FA_3_Przykład_1.xml").read_bytes())
    builder = (
        InvoiceBuilder()
        .header_model(invoice.header)
        .seller_model(invoice.seller)
        .buyer_model(invoice.buyer)
    )
    body = (
        builder.correction_advance()
        if kind == "correction_advance"
        else builder.correction_settlement()
    )
    _ = (
        body.issue_date(date(2026, 2, 1))
        .invoice_number("KOR/1")
        .summary_overrides(InvoiceSummaryOverrides(total_gross=Decimal("-123.00")))
    )
    _ = (
        body.correction()
        .add_corrected_invoice(
            issue_date=date(2026, 1, 1), invoice_number="ZAL/1", outside_ksef=True
        )
        .done()
    )
    _ = body.done()
    xml = builder.to_xml()
    parsed = parse_invoice_xml(xml.encode("utf-8"))
    assert parsed.body.rows == []
    assert parsed.total_gross == Decimal("-123.00")
    assert parsed.body.correction is not None
    assert parsed.body.correction.corrected_invoices[0].invoice_number == "ZAL/1"
    expected_type = "KOR_ZAL" if kind == "correction_advance" else "KOR_ROZ"
    assert expected_type in xml


@pytest.mark.parametrize("value", [True, False, None])
def test_public_builder_serializes_return_of_excise(value: bool | None) -> None:
    invoice = parse_invoice_xml((SAMPLES / "FA_3_Przykład_1.xml").read_bytes())
    builder = InvoiceBuilder.from_invoice(invoice)
    _ = builder.standard().from_model(invoice.body).return_of_excise(value).done()
    xml = builder.to_xml()
    document = etree.fromstring(xml.encode("utf-8"))
    assert document.xpath("//*[local-name()='ZwrotAkcyzy']/text()") == (
        ["1"] if value else []
    )
    assert parse_invoice_xml(xml.encode("utf-8")).body.return_of_excise is (
        True if value else None
    )
