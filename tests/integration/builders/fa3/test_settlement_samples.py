from datetime import date, datetime, timezone
import pytest
from decimal import Decimal
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3.body import InvoiceSummaryOverrides, VatRate
from ksef2.domain.models.fa3.party import ContactInfo, InvoiceAddress
from ksef2.domain.models.fa3.third_party import InvoiceThirdParty
from ksef2.infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2.infra.schema.fa3.models.schemat import Faktura
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder
from tests.integration.builders.helpers import load_sample, sample_path

SETTLEMENT_SAMPLES = [
    "Fa_3_Przykład_17.xml",
    "KSEF_10_ROZ_B.xml",
]

CORRECTION_SETTLEMENT_SAMPLES = [
    "KSEF_11_KOR_ROZ_A.xml",
    "KSEF_12_KOR_ROZ_B.xml",
]


ALL_SETTLEMENT_SAMPLES = SETTLEMENT_SAMPLES + CORRECTION_SETTLEMENT_SAMPLES


@pytest.mark.integration
def test_new_fa3_settlement_builder_sample_ksef_09_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("KSEF_09_ROZ_A.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 11, 15, 9, 0, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="IMMOBILIA DEVELOPMENT S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Developerska 25",
            address_line_2="00-100 Warszawa",
            email="biuro@immobilia.pl",
            phone="+48221112233",
        )
        .buyer(
            name="Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Mieszkaniowa 10/5",
            address_line_2="00-200 Warszawa",
            email="j.kowalski@email.pl",
            phone="+48600111222",
        )
    )

    _ = builder.add_third_party_model(expected_invoice.third_parties[0])
    _ = builder.add_third_party_model(expected_invoice.third_parties[1])

    _ = (
        builder.footer()
        .add_information(
            "IMMOBILIA DEVELOPMENT S.A. - Kapital zakladowy: 10 000 000 PLN"
        )
        .add_registry(
            krs="0000654321",
            regon="987654321",
            bdo="000054321",
        )
        .done()
    )

    _ = (
        builder.settlement()
        .issue_date(date(2025, 11, 15))
        .issue_place("Warszawa")
        .invoice_number("FR/2025/11/0001")
        .date_of_supply(date(2025, 11, 30))
        .summary_overrides(
            InvoiceSummaryOverrides(
                first_reduced_rate_net_total=Decimal("185185.19"),
                first_reduced_rate_vat_total=Decimal("14814.81"),
                total_gross=Decimal("200000.00"),
            )
        )
        .add_description(key="Wartosc zamowienia", value="439 000 PLN")
        .add_description(key="Pozostala kwota do zaplaty", value="199 000 PLN")
        .rows()
        .add_line(
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15 - I etap rozliczenia",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("185185.19"),
            vat_rate=VatRate.VAT_8,
            unique_id="KSEF09-LINE001",
            gtu_code="GTU_10",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .due_on(date(2025, 11, 30))
        .due_on(date(2025, 12, 15))
        .bank_account(
            "PL61109010140000071219812874",
            bank_name="Santander Bank Polska S.A.",
            account_description="PLN",
        )
        .done()
        .advance()
        .add_invoice_reference(ksef_id="9999999999-20251001-A1B2C3-D4E5F6-AB")
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
def test_new_fa3_settlement_builder_sample_14_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("Fa_3_Przykład_14.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 8, 17, 0, 0, 0, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Developex S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Sadowa 1 m. 3",
            address_line_2="00-002 Kraków",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(
            name="F.H.U. Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Polna 1",
            address_line_2="00-001 Warszawa",
            email="jan@kowalski.pl",
            phone="555777999",
        )
    )

    _ = builder.add_third_party_model(expected_invoice.third_parties[0])
    _ = builder.add_third_party_model(expected_invoice.third_parties[1])

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
        builder.settlement()
        .issue_date(date(2026, 8, 17))
        .issue_place("Warszawa")
        .invoice_number("FV2026/08/12")
        .date_of_supply(date(2026, 9, 17))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("4100.16"),
                base_rate_vat_total=Decimal("943.04"),
                first_reduced_rate_net_total=Decimal("280177.59"),
                first_reduced_rate_vat_total=Decimal("22414.21"),
                total_gross=Decimal("307635.00"),
            )
        )
        .add_description(
            key="wysokość pozostałej do zapłaty kwoty",
            value="307635 zł",
        )
        .add_description(
            key="W terminie 2026-09-15",
            value="co najmniej 50% pozostałej kwoty",
        )
        .add_description(
            key="W terminie 2026-10-15",
            value="pozostała część",
        )
        .rows()
        .add_line_model(expected_invoice.body.rows[0])
        .add_line_model(expected_invoice.body.rows[1])
        .done()
        .payment()
        .via("bank_transfer")
        .due_on(date(2026, 9, 15))
        .due_on(date(2026, 10, 15))
        .bank_account(
            "73111111111111111111111111",
            bank_name="Bank Bankowości Bankowej S. A.",
            account_description="PLN",
        )
        .done()
        .advance()
        .add_invoice_reference(ksef_id="9999999999-20230908-8BEF280C8D35-4D")
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
def test_new_fa3_correction_settlement_builder_sample_18_matches_loaded_sample() -> (
    None
):
    parser = XmlParser()
    expected_spec = load_sample(sample_path("Fa_3_Przykład_18.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 8, 17, 0, 0, 0, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Developex S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Sadowa 1 lok. 3",
            address_line_2="00-002 Kraków",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(
            name="F.H.U. Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Polna 1",
            address_line_2="00-001 Warszawa",
            email="jan@kowalski.pl",
            phone="555777999",
        )
    )

    _ = builder.add_third_party_model(expected_invoice.third_parties[0])

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
        builder.correction_settlement()
        .issue_date(date(2026, 8, 17))
        .issue_place("Warszawa")
        .invoice_number("FK2026/09/1")
        .date_of_supply(date(2026, 9, 17))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("101.76"),
                base_rate_vat_total=Decimal("23.41"),
                first_reduced_rate_net_total=Decimal("6953.54"),
                first_reduced_rate_vat_total=Decimal("556.29"),
                total_gross=Decimal("7635.00"),
            )
        )
        .rows()
        .add_line_model(expected_invoice.body.rows[0])
        .add_line_model(expected_invoice.body.rows[1])
        .add_line_model(expected_invoice.body.rows[2])
        .add_line_model(expected_invoice.body.rows[3])
        .done()
        .correction()
        .reason(
            "błędne zafakturowanie kwoty pozostałej do zapłaty: było 300000, a powinno być 307635"
        )
        .effect_type("original_entry_date")
        .add_corrected_invoice(
            issue_date=date(2026, 8, 17),
            invoice_number="FV2026/08/12",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .done()
        .advance()
        .amount_before_correction(Decimal("300000.00"))
        .add_invoice_reference(ksef_id="9999999999-20230908-76B2B580D4DC-80")
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


def _assert_sample(builder: StandardInvoiceBuilder, sample_name: str) -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path(sample_name))
    expected_invoice = invoice_from_spec(expected_spec)
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
def test_new_fa3_settlement_sample_17_manual() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 8, 17, 0, 0, 0, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Developex S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Sadowa 1 lok. 3",
            address_line_2="00-002 Kraków",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(
            name="F.H.U. Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Polna 1",
            address_line_2="00-001 Warszawa",
            email="jan@kowalski.pl",
            phone="555777999",
        )
    )
    _ = builder.add_third_party_model(
        InvoiceThirdParty(
            tax_id="3333333333",
            name="F.H.U. Grażyna Kowalska",
            address=InvoiceAddress(
                country_code="PL",
                address_line_1="ul. Polna 1",
                address_line_2="00-001 Warszawa",
            ),
            contact=ContactInfo(email="jan@kowalski.pl", phone="555777999"),
            role="additional_buyer",
            share_percentage=Decimal("50"),
        )
    )
    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(krs="0000099999", regon="999999999", bdo="000099999")
        .done()
    )
    _ = (
        builder.settlement()
        .issue_date(date(2026, 8, 17))
        .issue_place("Warszawa")
        .invoice_number("FV2026/08/12")
        .date_of_supply(date(2026, 9, 17))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("3998.40"),
                base_rate_vat_total=Decimal("919.63"),
                first_reduced_rate_net_total=Decimal("273224.05"),
                first_reduced_rate_vat_total=Decimal("21857.92"),
                total_gross=Decimal("300000"),
            )
        )
        .add_description(key="wysokosć pozostałej do zapłaty kwoty", value="300000 zł")
        .rows()
        .add_line(
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("307500"),
            vat_rate=VatRate.VAT_8,
            unique_id="aaaa111133339997",
            gtu_code="GTU_10",
        )
        .add_line(
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("4500"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339998",
        )
        .done()
        .advance()
        .add_invoice_reference(ksef_id="9999999999-20230908-8BEF280C8D35-4D")
        .done()
        .done()
    )

    _assert_sample(builder, "Fa_3_Przykład_17.xml")


@pytest.mark.integration
def test_new_fa3_settlement_sample_ksef_10_manual() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="IMMOBILIA DEVELOPMENT S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Developerska 25",
            address_line_2="00-100 Warszawa",
            email="biuro@immobilia.pl",
            phone="+48221112233",
        )
        .buyer(
            name="Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Mieszkaniowa 10/5",
            address_line_2="00-200 Warszawa",
            email="j.kowalski@email.pl",
            phone="+48600111222",
        )
    )
    _ = builder.add_third_party_model(
        InvoiceThirdParty(
            tax_id="3333333333",
            name="FINANSE PLUS sp. z o.o.",
            address=InvoiceAddress(
                country_code="PL",
                address_line_1="ul. Bankowa 5",
                address_line_2="00-300 Warszawa",
            ),
            contact=ContactInfo(email="kontakt@finanseplus.pl", phone="+48221234000"),
            role="additional_buyer",
            share_percentage=Decimal("100"),
        )
    )
    _ = builder.add_third_party_model(
        InvoiceThirdParty(
            tax_id="9999999999",
            name="IMMOBILIA DEVELOPMENT S.A.",
            address=InvoiceAddress(
                country_code="PL",
                address_line_1="ul. Developerska 25",
                address_line_2="00-100 Warszawa",
            ),
            contact=ContactInfo(email="biuro@immobilia.pl", phone="+48221112233"),
            role="original_subject",
        )
    )
    _ = (
        builder.footer()
        .add_information(
            "IMMOBILIA DEVELOPMENT S.A. - Kapital zakladowy: 10 000 000 PLN"
        )
        .add_registry(krs="0000654321", regon="987654321", bdo="000054321")
        .done()
    )
    _ = (
        builder.settlement()
        .issue_date(date(2025, 12, 20))
        .issue_place("Warszawa")
        .invoice_number("FR/2025/12/0001")
        .date_of_supply(date(2025, 12, 20))
        .summary_overrides(
            InvoiceSummaryOverrides(
                first_reduced_rate_net_total=Decimal("184259.26"),
                first_reduced_rate_vat_total=Decimal("14740.74"),
                total_gross=Decimal("199000"),
            )
        )
        .add_description(key="Wartosc calkowita zamowienia", value="439 000 PLN")
        .add_description(
            key="Status", value="ROZLICZENIE KONCOWE - Calkowicie oplacone"
        )
        .rows()
        .add_line(
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15 - ROZLICZENIE KONCOWE",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("184259.26"),
            vat_rate=VatRate.VAT_8,
            unique_id="KSEF10-LINE001",
            gtu_code="GTU_10",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .already_paid(date(2025, 12, 20))
        .bank_account(
            "PL61109010140000071219812874",
            bank_name="Santander Bank Polska S.A.",
            account_description="PLN",
        )
        .done()
        .advance()
        .add_invoice_reference(ksef_id="9999999999-20251001-A1B2C3-D4E5F6-AB")
        .add_invoice_reference(ksef_id="9999999999-20251115-A1B2C3-D4E5F6-AB")
        .done()
        .done()
    )

    _assert_sample(builder, "KSEF_10_ROZ_B.xml")


@pytest.mark.integration
def test_new_fa3_correction_settlement_sample_ksef_11_manual() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 11, 25, 14, 0, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="IMMOBILIA DEVELOPMENT S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Developerska 25",
            address_line_2="00-100 Warszawa",
            email="biuro@immobilia.pl",
            phone="+48221112233",
        )
        .buyer(
            name="Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Mieszkaniowa 10/5",
            address_line_2="00-200 Warszawa",
            email="j.kowalski@email.pl",
            phone="+48600111222",
        )
    )
    _ = builder.add_third_party_model(
        InvoiceThirdParty(
            tax_id="3333333333",
            name="FINANSE PLUS sp. z o.o.",
            address=InvoiceAddress(
                country_code="PL",
                address_line_1="ul. Bankowa 5",
                address_line_2="00-300 Warszawa",
            ),
            contact=ContactInfo(email="kontakt@finanseplus.pl", phone="+48221234000"),
            role="additional_buyer",
            share_percentage=Decimal("100"),
        )
    )
    _ = (
        builder.footer()
        .add_information(
            "IMMOBILIA DEVELOPMENT S.A. - Kapital zakladowy: 10 000 000 PLN"
        )
        .add_registry(krs="0000654321", regon="987654321", bdo="000054321")
        .done()
    )
    _ = (
        builder.correction_settlement()
        .issue_date(date(2025, 11, 25))
        .issue_place("Warszawa")
        .invoice_number("FKR/2025/11/0001")
        .date_of_supply(date(2025, 11, 30))
        .summary_overrides(
            InvoiceSummaryOverrides(
                first_reduced_rate_net_total=Decimal("-9259.26"),
                first_reduced_rate_vat_total=Decimal("-740.74"),
                total_gross=Decimal("-10000"),
            )
        )
        .rows()
        .add_line(
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15 - I etap rozliczenia",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("185185.19"),
            vat_rate=VatRate.VAT_8,
            unique_id="KSEF09-LINE001",
            gtu_code="GTU_10",
            before_correction=True,
        )
        .add_line(
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15 - I etap rozliczenia",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("175925.93"),
            vat_rate=VatRate.VAT_8,
            unique_id="KSEF09-LINE001",
            gtu_code="GTU_10",
        )
        .done()
        .correction()
        .reason(
            "Blad w obliczeniach - niezastosowana znizka 5% za wczesniejsza platnosc"
        )
        .effect_type("original_entry_date")
        .add_corrected_invoice(
            issue_date=date(2025, 11, 15),
            invoice_number="FR/2025/11/0001",
            ksef_id="9999999999-20251115-A1B2C3-D4E5F6-AB",
        )
        .done()
        .advance()
        .amount_before_correction(Decimal("200000"))
        .add_invoice_reference(ksef_id="9999999999-20251001-A1B2C3-D4E5F6-AB")
        .done()
        .done()
    )

    _assert_sample(builder, "KSEF_11_KOR_ROZ_A.xml")


@pytest.mark.integration
def test_new_fa3_correction_settlement_sample_ksef_12_manual() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 12, 28, 15, 30, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="IMMOBILIA DEVELOPMENT S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Developerska 25",
            address_line_2="00-100 Warszawa",
            email="biuro@immobilia.pl",
            phone="+48221112233",
        )
        .buyer(
            name="Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Mieszkaniowa 10/5",
            address_line_2="00-200 Warszawa",
            email="j.kowalski@email.pl",
            phone="+48600111222",
        )
    )
    _ = builder.add_third_party_model(
        InvoiceThirdParty(
            tax_id="3333333333",
            name="FINANSE PLUS sp. z o.o.",
            address=InvoiceAddress(
                country_code="PL",
                address_line_1="ul. Bankowa 5",
                address_line_2="00-300 Warszawa",
            ),
            contact=ContactInfo(email="kontakt@finanseplus.pl", phone="+48221234000"),
            role="additional_buyer",
            share_percentage=Decimal("100"),
        )
    )
    _ = (
        builder.footer()
        .add_information(
            "IMMOBILIA DEVELOPMENT S.A. - Kapital zakladowy: 10 000 000 PLN"
        )
        .add_registry(krs="0000654321", regon="987654321", bdo="000054321")
        .done()
    )
    _ = (
        builder.correction_settlement()
        .issue_date(date(2025, 12, 28))
        .issue_place("Warszawa")
        .invoice_number("FKR/2025/12/0001")
        .date_of_supply(date(2025, 12, 20))
        .summary_overrides(
            InvoiceSummaryOverrides(
                first_reduced_rate_net_total=Decimal("-4629.63"),
                first_reduced_rate_vat_total=Decimal("-370.37"),
                total_gross=Decimal("-5000"),
            )
        )
        .rows()
        .add_line(
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15 - ROZLICZENIE KONCOWE",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("184259.26"),
            vat_rate=VatRate.VAT_8,
            unique_id="KSEF10-LINE001",
            gtu_code="GTU_10",
            before_correction=True,
        )
        .add_line(
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15 - ROZLICZENIE KONCOWE (po korekcie)",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("179629.63"),
            vat_rate=VatRate.VAT_8,
            unique_id="KSEF10-LINE001",
            gtu_code="GTU_10",
        )
        .done()
        .correction()
        .reason(
            "Wada wykonczenia stwierdzona przy odbiorze - rysy na parkiecie w salonie"
        )
        .effect_type("other_date")
        .add_corrected_invoice(
            issue_date=date(2025, 12, 20),
            invoice_number="FR/2025/12/0001",
            ksef_id="9999999999-20251220-A1B2C3-D4E5F6-AB",
        )
        .done()
        .advance()
        .amount_before_correction(Decimal("199000"))
        .add_invoice_reference(ksef_id="9999999999-20251001-A1B2C3-D4E5F6-AB")
        .add_invoice_reference(ksef_id="9999999999-20251115-A1B2C3-D4E5F6-AB")
        .done()
        .done()
    )

    _assert_sample(builder, "KSEF_12_KOR_ROZ_B.xml")
