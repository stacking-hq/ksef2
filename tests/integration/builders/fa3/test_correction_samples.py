from datetime import date, datetime, timezone
import pytest
from decimal import Decimal
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3.body import InvoiceRow, InvoiceSummaryOverrides, VatRate
from ksef2.infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2.infra.schema.fa3.models.schemat import Faktura
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder
from tests.integration.builders.helpers import load_sample, sample_path


@pytest.mark.integration
def test_new_fa3_correction_builder_sample_2_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_2.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

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
        .buyer(
            name="F.H.U. Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Polna 1",
            address_line_2="00-001 Warszawa",
            customer_number="fdfd778343",
            email="jan@kowalski.pl",
            phone="555777999",
        )
    )

    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    _ = (
        builder.correction()
        .issue_date(date(2026, 3, 15))
        .issue_place("Warszawa")
        .invoice_number("FK2026/03/200")
        .date_of_supply(date(2026, 1, 27))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-162.60"),
                base_rate_vat_total=Decimal("-37.40"),
                total_gross=Decimal("-200.00"),
            )
        )
        .rows()
        .add_line(
            name="lodówka Zimnotech mk1",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("1626.01"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339990",
            before_correction=True,
        )
        .add_line(
            name="lodówka Zimnotech mk1",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("1463.41"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339990",
        )
        .done()
        .correction()
        .reason("obniżka ceny o 200 zł z uwagi na uszkodzenia estetyczne")
        .effect_type("other_date")
        .add_corrected_invoice(
            issue_date=date(2026, 2, 15),
            invoice_number="FV2026/02/150",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .done()
        .done()
    )

    actual_spec = builder.to_spec()
    actual_invoice = invoice_from_spec(actual_spec)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual_spec.fa.p_2 == expected_spec.fa.p_2
    assert len(actual_spec.fa.fa_wiersz) == len(expected_spec.fa.fa_wiersz)
    assert Decimal(actual_spec.fa.p_15) == Decimal(expected_spec.fa.p_15)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice


@pytest.mark.integration
def test_new_fa3_correction_samples_3() -> None:
    """FA_3_Przykład_3.xml - correction sample (identical to sample 2)"""
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_3.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

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
        .buyer(
            name="F.H.U. Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Polna 1",
            address_line_2="00-001 Warszawa",
            customer_number="fdfd778343",
            email="jan@kowalski.pl",
            phone="555777999",
        )
    )

    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    _ = (
        builder.correction()
        .issue_date(date(2026, 3, 15))
        .issue_place("Warszawa")
        .invoice_number("FK2026/03/200")
        .date_of_supply(date(2026, 1, 27))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-162.60"),
                base_rate_vat_total=Decimal("-37.40"),
                total_gross=Decimal("-200.00"),
            )
        )
        .rows()
        .add_line(
            name="lodówka Zimnotech mk1",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("-162.60"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339990",
        )
        .done()
        .correction()
        .reason("obniżka ceny o 200 zł z uwagi na uszkodzenia estetyczne")
        .effect_type("other_date")
        .add_corrected_invoice(
            issue_date=date(2026, 2, 15),
            invoice_number="FV2026/02/150",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .done()
        .done()
    )

    actual_spec = builder.to_spec()
    actual_invoice = invoice_from_spec(actual_spec)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual_spec.fa.p_2 == expected_spec.fa.p_2
    assert len(actual_spec.fa.fa_wiersz) == len(expected_spec.fa.fa_wiersz)
    assert Decimal(actual_spec.fa.p_15) == Decimal(expected_spec.fa.p_15)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice


@pytest.mark.integration
def test_new_fa3_correction_samples_5() -> None:
    """FA_3_Przykład_5.xml - correction with corrected buyer"""
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_5.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
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
        .buyer(
            name="CeDeE s.c.",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Sadowa 1 lok. 3",
            address_line_2="00-002 Kraków",
            customer_number="fdfd778343",
            buyer_id="0001",
            email="cde@cde.pl",
            phone="555777999",
        )
    )

    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    _ = (
        builder.correction()
        .issue_date(date(2026, 4, 1))
        .issue_place("Warszawa")
        .invoice_number("FK2026/04/23")
        .summary_overrides(InvoiceSummaryOverrides(total_gross=Decimal("0.00")))
        .correction()
        .reason("błędna nazwa nabywcy")
        .effect_type("original_entry_date")
        .add_corrected_invoice(
            issue_date=date(2026, 2, 15),
            invoice_number="FV2026/02/150",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .add_corrected_buyer(
            name="CDE sp. j.",
            tax_id="1111111111",
            address_country_code="PL",
            address_line_1="ul. Sadowa 1 lok. 3",
            address_line_2="00-002 Kraków",
            buyer_id="0001",
        )
        .done()
        .done()
    )

    actual_spec = builder.to_spec()
    actual_invoice = invoice_from_spec(actual_spec)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual_spec.fa.p_2 == expected_spec.fa.p_2
    assert Decimal(actual_spec.fa.p_15) == Decimal(expected_spec.fa.p_15)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice


@pytest.mark.integration
def test_new_fa3_correction_samples_6() -> None:
    """FA_3_Przykład_6.xml - correction with multiple corrected invoices and period"""
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_6.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 7, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
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
        .buyer(
            name="CeDeE s.c.",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Sadowa 1 lok. 3",
            address_line_2="00-002 Kraków",
            customer_number="fdfd778343",
            email="cde@cde.pl",
            phone="555777999",
        )
    )

    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    _ = (
        builder.correction()
        .issue_date(date(2026, 7, 15))
        .issue_place("Warszawa")
        .invoice_number("FK2026/07/243")
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-40650.41"),
                base_rate_vat_total=Decimal("-9349.59"),
                total_gross=Decimal("-50000.00"),
            )
        )
        .correction()
        .reason("rabat 50000 z uwagi na poziom zakupów pierwszym półroczu 2026")
        .effect_type("correction_issue_date")
        .corrected_invoice_period("pierwsze półrocze 2026")
        .add_corrected_invoice(
            issue_date=date(2026, 1, 15),
            invoice_number="FV2026/01/134",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 2, 15),
            invoice_number="FV2026/02/150",
            ksef_id="9999999999-20230908-76B2B580D4DC-80",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 3, 15),
            invoice_number="FV2026/03/143",
            ksef_id="9999999999-20230908-4191312C0E57-09",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 4, 15),
            invoice_number="FV2026/04/23",
            ksef_id="9999999999-20230908-2B9266CEF3C4-DD",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 5, 15),
            invoice_number="FV2026/05/54",
            ksef_id="9999999999-20230908-16B99491C78B-3D",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 6, 15),
            invoice_number="FV2026/06/15",
            ksef_id="9999999999-20230908-D08FB95950BE-3E",
        )
        .done()
        .done()
    )

    actual_spec = builder.to_spec()
    actual_invoice = invoice_from_spec(actual_spec)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual_spec.fa.p_2 == expected_spec.fa.p_2
    assert Decimal(actual_spec.fa.p_15) == Decimal(expected_spec.fa.p_15)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice


@pytest.mark.integration
def test_new_fa3_correction_samples_7() -> None:
    """FA_3_Przykład_7.xml - correction with multiple corrected invoices, period, and descriptive row"""
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_7.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 7, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
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
        .buyer(
            name="CeDeE s.c.",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Sadowa 1 lok. 3",
            address_line_2="00-002 Kraków",
            customer_number="fdfd778343",
            email="cde@cde.pl",
            phone="555777999",
        )
    )

    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    rows_builder = (
        builder.correction()
        .issue_date(date(2026, 7, 15))
        .issue_place("Warszawa")
        .invoice_number("FK2026/07/243")
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-40650.41"),
                base_rate_vat_total=Decimal("-9349.59"),
                total_gross=Decimal("-50000.00"),
            )
        )
        .rows()
    )

    _ = rows_builder.add_line_model(
        InvoiceRow(
            name="lodówka Zimnotech mk1",
            quantity=Decimal("1000"),
            unit_of_measure="szt.",
            cn="8418 21 91",
        )
    )

    _ = (
        rows_builder.done()
        .correction()
        .reason("rabat 50000 z uwagi na poziom zakupów pierwszym półroczu 2026")
        .effect_type("correction_issue_date")
        .corrected_invoice_period("pierwsze półrocze 2026")
        .add_corrected_invoice(
            issue_date=date(2026, 1, 15),
            invoice_number="FV2026/01/134",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 2, 15),
            invoice_number="FV2026/02/150",
            ksef_id="9999999999-20230908-76B2B580D4DC-80",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 3, 15),
            invoice_number="FV2026/03/143",
            ksef_id="9999999999-20230908-4191312C0E57-09",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 4, 15),
            invoice_number="FV2026/04/23",
            ksef_id="9999999999-20230908-2B9266CEF3C4-DD",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 5, 15),
            invoice_number="FV2026/05/54",
            ksef_id="9999999999-20230908-16B99491C78B-3D",
        )
        .add_corrected_invoice(
            issue_date=date(2026, 6, 15),
            invoice_number="FV2026/06/15",
            ksef_id="9999999999-20230908-D08FB95950BE-3E",
        )
        .done()
        .done()
    )

    actual_spec = builder.to_spec()
    actual_invoice = invoice_from_spec(actual_spec)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual_spec.fa.p_2 == expected_spec.fa.p_2
    assert Decimal(actual_spec.fa.p_15) == Decimal(expected_spec.fa.p_15)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice


@pytest.mark.integration
def test_new_fa3_correction_samples_ksef_02_kor() -> None:
    """KSEF_02_KOR.xml - correction with before_correction row"""
    parser = XmlParser()
    expected_spec = load_sample(sample_path("KSEF_02_KOR.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 12, 20, 14, 0, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="TECH-SOLUTIONS sp. z o.o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Marszalkowska 100",
            address_line_2="00-001 Warszawa",
            email="biuro@tech-solutions.pl",
            phone="+48221234567",
        )
        .buyer(
            name="ABC HANDEL sp. z o.o.",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Poznanska 50",
            address_line_2="60-001 Poznan",
            customer_number="ABC-001",
            email="kontakt@abc-handel.pl",
            phone="+48617654321",
        )
    )

    _ = (
        builder.footer()
        .add_information("TECH-SOLUTIONS sp. z o.o. - Kapital zakladowy: 500 000 PLN")
        .add_registry(
            krs="0000123456",
            regon="146025969",
            bdo="000012345",
        )
        .done()
    )

    _ = (
        builder.correction()
        .issue_date(date(2025, 12, 20))
        .issue_place("Warszawa")
        .invoice_number("FK/2025/12/0001")
        .date_of_supply(date(2025, 12, 10))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-406.50"),
                base_rate_vat_total=Decimal("-93.50"),
                total_gross=Decimal("-500"),
            )
        )
        .rows()
        .add_line(
            name="Laptop Dell XPS 15",
            quantity=Decimal("2"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("2032.52"),
            vat_rate=VatRate.VAT_23,
            unique_id="KSEF01-LINE001",
            before_correction=True,
        )
        .add_line(
            name="Laptop Dell XPS 15",
            quantity=Decimal("2"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("1829.27"),
            vat_rate=VatRate.VAT_23,
            unique_id="KSEF01-LINE001",
        )
        .done()
        .correction()
        .reason(
            "Rabat udzielony po dostawie - obnizka ceny o 500 PLN z tytulu promocji"
        )
        .effect_type("other_date")
        .add_corrected_invoice(
            issue_date=date(2025, 12, 15),
            invoice_number="FV/2025/12/0001",
            ksef_id="9999999999-20251215-A1B2C3-D4E5F6-AB",
        )
        .done()
        .done()
    )

    actual_spec = builder.to_spec()
    actual_invoice = invoice_from_spec(actual_spec)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual_spec.fa.p_2 == expected_spec.fa.p_2
    assert len(actual_spec.fa.fa_wiersz) == len(expected_spec.fa.fa_wiersz)
    assert Decimal(actual_spec.fa.p_15) == Decimal(expected_spec.fa.p_15)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice
