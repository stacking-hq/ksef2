import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3.body import InvoiceRow, InvoiceSummaryOverrides, VatRate
from ksef2.infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2.infra.schema.fa3.models.schemat import Faktura
from tests.integration.builders.helpers import load_sample, sample_path
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder


def _assert_sample(builder: StandardInvoiceBuilder, sample_name: str) -> None:
    parser = XmlParser()
    expected = load_sample(sample_path(sample_name))
    actual = builder.to_spec()
    actual_invoice = invoice_from_spec(actual)
    expected_invoice = invoice_from_spec(expected)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual.fa.p_2 == expected.fa.p_2
    assert Decimal(actual.fa.p_15) == Decimal(expected.fa.p_15)
    assert len(actual.fa.fa_wiersz) == len(expected.fa.fa_wiersz)
    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice


@pytest.mark.integration
def test_new_fa3_simplified_sample_15() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
            system_info="SamploFaktur",
        )
        .seller(
            name="ABC AGD sp. z o. o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Kwiatowa 1 m. 2",
            address_line_2="00-001 Warszawa",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(name=None, tax_id="1111111111", country_code=None, address_line_1=None)
    )
    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(krs="0000099999", regon="999999999", bdo="000099999")
        .done()
    )
    _ = (
        builder.simplified()
        .issue_date(date(2026, 2, 15))
        .invoice_number("FV2026/02/150")
        .date_of_supply(date(2026, 1, 3))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("365.85"),
                base_rate_vat_total=Decimal("84.15"),
                total_gross=Decimal("450"),
            )
        )
        .rows()
        .add_line_model(InvoiceRow(name="wiertarka Wiertex mk5"))
        .done()
        .done()
    )

    _assert_sample(builder, "FA_3_Przykład_15.xml")


@pytest.mark.integration
def test_new_fa3_simplified_sample_16() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
            system_info="SamploFaktur",
        )
        .seller(
            name="ABC AGD sp. z o. o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Kwiatowa 1 m. 2",
            address_line_2="00-001 Warszawa",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(name=None, tax_id="1111111111", country_code=None, address_line_1=None)
    )
    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(krs="0000099999", regon="999999999", bdo="000099999")
        .done()
    )
    _ = (
        builder.simplified()
        .issue_date(date(2026, 2, 15))
        .invoice_number("FV2026/02/150")
        .date_of_supply(date(2026, 1, 3))
        .summary_overrides(InvoiceSummaryOverrides(total_gross=Decimal("450")))
        .rows()
        .add_line_model(
            InvoiceRow(name="wiertarka Wiertex mk5", vat_rate=VatRate.VAT_23)
        )
        .done()
        .done()
    )

    _assert_sample(builder, "FA_3_Przykład_16.xml")


@pytest.mark.integration
def test_new_fa3_simplified_sample_ksef_04_upr() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 12, 5, 11, 30, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="SKLEP NAROZNY sp. z o.o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Handlowa 15",
            address_line_2="00-400 Warszawa",
            email="sklep@narozny.pl",
            phone="+48223334455",
        )
        .buyer(name=None, tax_id="1111111111", country_code=None, address_line_1=None)
    )
    _ = (
        builder.footer()
        .add_information("SKLEP NAROZNY sp. z o.o.")
        .add_registry(regon="111222333")
        .done()
    )
    _ = (
        builder.simplified()
        .issue_date(date(2025, 12, 5))
        .invoice_number("FU/2025/12/0001")
        .date_of_supply(date(2025, 12, 5))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("300.00"),
                base_rate_vat_total=Decimal("69.00"),
                total_gross=Decimal("369"),
            )
        )
        .rows()
        .add_line_model(InvoiceRow(name="Artykuly biurowe (zestaw)"))
        .done()
        .done()
    )

    _assert_sample(builder, "KSEF_04_UPR.xml")
