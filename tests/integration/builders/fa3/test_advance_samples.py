from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3.body import InvoiceSummaryOverrides
from ksef2.domain.models.fa3.party import ContactInfo, InvoiceAddress
from ksef2.domain.models.fa3.third_party import InvoiceThirdParty
from ksef2.infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2.infra.schema.fa3.models.schemat import Faktura
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder
from tests.integration.builders.helpers import load_sample, sample_path


def _assert_advance_sample(sample_name: str, builder: StandardInvoiceBuilder) -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path(sample_name))
    expected_invoice = invoice_from_spec(expected_spec)
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
def test_new_fa3_advance_builder_sample_10_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_10.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Developex sp. z o. o.",
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
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    _ = (
        builder.advance()
        .currency("PLN")
        .issue_date(date(2026, 2, 15))
        .issue_place("Warszawa")
        .invoice_number("FZ2026/02/150")
        .date_of_supply(date(2026, 2, 15))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("16260.16"),
                base_rate_vat_total=Decimal("3739.84"),
                total_gross=Decimal("20000.00"),
            )
        )
        .add_description(key="wysokosć wpłaconego zadatku", value="20000 zł")
        .order(declared_total=Decimal("375150.00"))
        .add_line(
            gross_amount=Decimal("369000.00"),
            vat_rate="23",
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("300000.00"),
            unique_id="aaaa111133339990",
        )
        .add_line(
            gross_amount=Decimal("6150.00"),
            vat_rate="23",
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("5000.00"),
            unique_id="aaaa111133339991",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .already_paid(date(2026, 2, 15))
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
def test_new_fa3_correction_advance_builder_sample_12_matches_loaded_sample() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Developex sp. z o. o.",
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
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    body_builder = (
        builder.correction_advance()
        .currency("PLN")
        .issue_date(date(2026, 3, 17))
        .issue_place("Warszawa")
        .invoice_number("FK2026/03/7")
        .date_of_supply(date(2026, 2, 15))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("133.28"),
                base_rate_vat_total=Decimal("30.65"),
                first_reduced_rate_net_total=Decimal("9107.47"),
                first_reduced_rate_vat_total=Decimal("728.60"),
                total_gross=Decimal("10000.00"),
            )
        )
        .order(declared_total=Decimal("375150.00"))
        .add_line(
            gross_amount=Decimal("369000.00"),
            vat_rate="8",
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("341666.67"),
            unique_id="aaaa111133339990",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("369000.00"),
            vat_rate="8",
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("341666.67"),
            unique_id="aaaa111133339990",
        )
        .add_line(
            gross_amount=Decimal("6150.00"),
            vat_rate="23",
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("5000.00"),
            unique_id="aaaa111133339991",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("6150.00"),
            vat_rate="23",
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("5000.00"),
            unique_id="aaaa111133339991",
        )
        .done()
    )

    _ = (
        body_builder.correction()
        .reason("błędne zafakturowanie zaniżonej kwoty zadatku 20000 powinno być 30000")
        .effect_type("original_entry_date")
        .add_corrected_invoice(
            issue_date=date(2026, 2, 15),
            invoice_number="FZ2026/02/150",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .done()
    )

    _ = body_builder.advance().amount_before_correction(Decimal("20000.00")).done()
    _ = body_builder.done()

    _assert_advance_sample("FA_3_Przykład_12.xml", builder)


@pytest.mark.integration
def test_new_fa3_correction_advance_builder_sample_13_matches_loaded_sample() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Developex sp. z o. o.",
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
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    body_builder = (
        builder.correction_advance()
        .currency("PLN")
        .issue_date(date(2026, 3, 17))
        .issue_place("Warszawa")
        .invoice_number("FK2026/03/7")
        .date_of_supply(date(2026, 2, 15))
        .summary_overrides(InvoiceSummaryOverrides(total_gross=Decimal("0.00")))
        .order(declared_total=Decimal("337635.00"))
        .add_line(
            gross_amount=Decimal("369000.00"),
            vat_rate="8",
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("341666.67"),
            unique_id="aaaa111133339990",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("332100.00"),
            vat_rate="8",
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("307500"),
            unique_id="aaaa111133339990",
        )
        .add_line(
            gross_amount=Decimal("6150.00"),
            vat_rate="23",
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("5000.00"),
            unique_id="aaaa111133339991",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("5535.00"),
            vat_rate="23",
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("4500"),
            unique_id="aaaa111133339991",
        )
        .done()
    )

    _ = (
        body_builder.correction()
        .reason("korekta wartości zamówienia o -10%")
        .effect_type("other_date")
        .add_corrected_invoice(
            issue_date=date(2026, 2, 15),
            invoice_number="FZ2026/02/150",
            ksef_id="9999999999-20230908-8BEF280C8D35-4D",
        )
        .done()
    )

    _ = body_builder.advance().amount_before_correction(Decimal("30000.00")).done()
    _ = body_builder.done()

    _assert_advance_sample("FA_3_Przykład_13.xml", builder)


@pytest.mark.integration
def test_new_fa3_correction_advance_builder_sample_ksef_07_matches_loaded_sample() -> (
    None
):
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc),
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
        .add_registry(
            krs="0000654321",
            regon="987654321",
            bdo="000054321",
        )
        .done()
    )

    body_builder = (
        builder.correction_advance()
        .currency("PLN")
        .issue_date(date(2025, 10, 15))
        .issue_place("Warszawa")
        .invoice_number("FKZ/2025/10/0001")
        .date_of_supply(date(2025, 10, 1))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-8130.08"),
                base_rate_vat_total=Decimal("-1869.92"),
                total_gross=Decimal("-10000.00"),
            )
        )
        .order(declared_total=Decimal("406504.07"))
        .add_line(
            gross_amount=Decimal("500000.00"),
            vat_rate="23",
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("406504.07"),
            unique_id="KSEF03-ZAM001",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("500000.00"),
            vat_rate="23",
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("406504.07"),
            unique_id="KSEF03-ZAM001",
        )
        .done()
    )

    _ = (
        body_builder.correction()
        .reason(
            "Czesciowe odstapienie od umowy - zmniejszenie zamowienia o uslugi dodatkowe"
        )
        .effect_type("other_date")
        .add_corrected_invoice(
            issue_date=date(2025, 10, 1),
            invoice_number="FZ/2025/10/0001",
            ksef_id="9999999999-20251001-A1B2C3-D4E5F6-AB",
        )
        .done()
    )

    _ = body_builder.advance().amount_before_correction(Decimal("50000.00")).done()
    _ = body_builder.done()

    _assert_advance_sample("KSEF_07_KOR_ZAL_A.xml", builder)


@pytest.mark.integration
def test_new_fa3_correction_advance_builder_sample_ksef_08_matches_loaded_sample() -> (
    None
):
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 10, 20, 11, 0, 0, tzinfo=timezone.utc),
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
        .add_registry(
            krs="0000654321",
            regon="987654321",
            bdo="000054321",
        )
        .done()
    )

    body_builder = (
        builder.correction_advance()
        .currency("PLN")
        .issue_date(date(2025, 10, 20))
        .issue_place("Warszawa")
        .invoice_number("FKZ/2025/10/0002")
        .date_of_supply(date(2025, 10, 1))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-32520.33"),
                base_rate_vat_total=Decimal("-7479.67"),
                first_reduced_rate_net_total=Decimal("37037.04"),
                first_reduced_rate_vat_total=Decimal("2962.96"),
                total_gross=Decimal("0.00"),
            )
        )
        .order(declared_total=Decimal("439000.00"))
        .add_line(
            gross_amount=Decimal("500000.00"),
            vat_rate="23",
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("406504.07"),
            unique_id="KSEF03-ZAM001",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("439000.00"),
            vat_rate="8",
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("406481.48"),
            unique_id="KSEF03-ZAM001",
        )
        .done()
    )

    _ = (
        body_builder.correction()
        .reason("Bledna stawka VAT - korekta z 23% na 8% (budownictwo spoleczne)")
        .effect_type("original_entry_date")
        .add_corrected_invoice(
            issue_date=date(2025, 10, 1),
            invoice_number="FZ/2025/10/0001",
            ksef_id="9999999999-20251001-A1B2C3-D4E5F6-AB",
        )
        .add_corrected_invoice(
            issue_date=date(2025, 10, 15),
            invoice_number="FKZ/2025/10/0001",
            ksef_id="9999999999-20251015-A1B2C3-D4E5F6-AB",
        )
        .done()
    )

    _ = body_builder.advance().amount_before_correction(Decimal("40000.00")).done()
    _ = body_builder.done()

    _assert_advance_sample("KSEF_08_KOR_ZAL_B.xml", builder)


@pytest.mark.integration
def test_new_fa3_advance_builder_sample_ksef_03_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("KSEF_03_ZAL.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 10, 1, 9, 0, 0, tzinfo=timezone.utc),
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
            jst_subordinate_unit=False,
            vat_group_member=False,
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
        .add_registry(
            krs="0000654321",
            regon="987654321",
            bdo="000054321",
        )
        .done()
    )

    _ = (
        builder.advance()
        .currency("PLN")
        .issue_date(date(2025, 10, 1))
        .issue_place("Warszawa")
        .invoice_number("FZ/2025/10/0001")
        .date_of_supply(date(2025, 10, 1))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("40650.41"),
                base_rate_vat_total=Decimal("9349.59"),
                total_gross=Decimal("50000.00"),
            )
        )
        .add_description(key="Wysokosc wplaconego zadatku", value="50 000 PLN")
        .add_description(
            key="Umowa przedwstepna",
            value="UP/2025/09/0001 z dnia 2025-09-15",
        )
        .order(declared_total=Decimal("500000.00"))
        .add_line(
            gross_amount=Decimal("500000.00"),
            vat_rate="23",
            name="Mieszkanie 60m2 - Osiedle Sloneczne, budynek A, lokal 15",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("406504.07"),
            unique_id="KSEF03-ZAM001",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .already_paid(date(2025, 10, 1))
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
def test_new_fa3_correction_advance_builder_sample_11_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_11.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Developex sp. z o. o.",
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
            jst_subordinate_unit=False,
            vat_group_member=False,
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
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    body_builder = (
        builder.correction_advance()
        .currency("PLN")
        .issue_date(date(2026, 3, 15))
        .issue_place("Warszawa")
        .invoice_number("FK2026/03/5")
        .date_of_supply(date(2026, 2, 15))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("-15993.60"),
                base_rate_vat_total=Decimal("-3678.53"),
                first_reduced_rate_net_total=Decimal("18214.94"),
                first_reduced_rate_vat_total=Decimal("1457.19"),
                total_gross=Decimal("0.00"),
            )
        )
        .order(declared_total=Decimal("375150.00"))
        .add_line(
            gross_amount=Decimal("369000.00"),
            vat_rate="23",
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("300000.00"),
            unique_id="aaaa111133339990",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("369000.00"),
            vat_rate="8",
            name="mieszkanie 50m^2",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("341666.67"),
            unique_id="aaaa111133339990",
        )
        .add_line(
            gross_amount=Decimal("6150.00"),
            vat_rate="23",
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("5000.00"),
            unique_id="aaaa111133339991",
            before_correction=True,
        )
        .add_line(
            gross_amount=Decimal("6150.00"),
            vat_rate="23",
            name="usługi dodatkowe",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("5000.00"),
            unique_id="aaaa111133339991",
        )
        .done()
    )

    correction_builder = body_builder.correction()
    _ = correction_builder.reason("błędna stawka VAT")
    _ = correction_builder.effect_type("other_date")
    _ = correction_builder.add_corrected_invoice(
        issue_date=date(2026, 2, 15),
        invoice_number="FZ2026/02/150",
        ksef_id="9999999999-20230908-8BEF280C8D35-4D",
    )
    _ = correction_builder.done()

    advance_builder = body_builder.advance()
    _ = advance_builder.amount_before_correction(Decimal("20000.00"))
    _ = advance_builder.done()
    _ = body_builder.done()

    actual_spec = builder.to_spec()
    actual_invoice = invoice_from_spec(actual_spec)
    xml_invoice = invoice_from_spec(
        parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura)
    )

    assert actual_spec.fa.p_2 == expected_spec.fa.p_2
    assert Decimal(actual_spec.fa.p_15) == Decimal(expected_spec.fa.p_15)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice
