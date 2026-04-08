from decimal import Decimal
from datetime import date, datetime, timezone

import pytest
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3 import (
    ContactInfo,
    InvoiceAddress,
    InvoiceThirdParty,
    MarginProcedure,
)
from ksef2.domain.models.fa3.body import (
    InvoiceRow,
    InvoiceSummaryOverrides,
    SaleCategory,
    TaxRegime,
    TransactionAddress,
    TransactionIdentity,
    VatRate,
)
from ksef2.infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2.infra.schema.fa3.models.schemat import Faktura
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder
from tests.integration.builders.helpers import load_sample, sample_path

VAT_SAMPLES = [
    "FA_3_Przykład_21.xml",
    "FA_3_Przykład_22.xml",
    "FA_3_Przykład_23.xml",
    "FA_3_Przykład_24.xml",
    "FA_3_Przykład_25.xml",
    "FA_3_Przykład_26.xml",
    "FA_3_Przykład_4.xml",
    "Fa_3_Przykład_19.xml",
    "Fa_3_Przykład_20.xml",
]


def _assert_vat_sample(sample_name: str, builder: StandardInvoiceBuilder) -> None:
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
def test_new_fa3_vat_builder_sample_ksef_01_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("KSEF_01_VAT_STANDARD.xml"))
    expected_invoice = invoice_from_spec(expected_spec)

    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 12, 15, 10, 30, 0, tzinfo=timezone.utc),
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
        builder.standard()
        .issue_date(date(2025, 12, 15))
        .issue_place("Warszawa")
        .invoice_number("FV/2025/12/0001")
        .date_of_supply(date(2025, 12, 10))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("4065.04"),
                base_rate_vat_total=Decimal("934.96"),
                total_gross=Decimal("5000.00"),
            )
        )
        .rows()
        .add_line_model(expected_invoice.body.rows[0])
        .done()
        .payment()
        .via("bank_transfer")
        .due_on(date(2026, 1, 15))
        .bank_account(
            "PL61109010140000071219812874",
            bank_name="Santander Bank Polska S.A.",
            account_description="PLN",
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
def test_new_fa3_vat_builder_sample_8_margin_matches_loaded_sample() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="Komis ABC AGD sp. z o. o.",
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
        builder.standard()
        .issue_date(date(2026, 2, 27))
        .issue_place("Warszawa")
        .invoice_number("FM2026/02/150")
        .date_of_supply(date(2026, 1, 27))
        .mark_fp()
        .summary_overrides(
            InvoiceSummaryOverrides(
                margin_total=Decimal("15000.00"),
                total_gross=Decimal("15000.00"),
            )
        )
        .rows()
        .add_line_model(
            InvoiceRow(
                name="samochód używany marki Autex rocznik 2010",
                quantity=Decimal("1"),
                unit_of_measure="szt.",
                unit_price_gross=Decimal("15000"),
                gross_amount=Decimal("15000"),
                net_amount=Decimal("15000"),
                vat_amount=Decimal("0.00"),
                tax_regime=TaxRegime.MARGIN,
                gtu_code="GTU_07",
            )
        )
        .done()
        .annotations()
        .margin_procedure(MarginProcedure.USED_GOODS)
        .done()
        .payment()
        .via("bank_transfer")
        .partial_payment_status("partial")
        .add_partial_payment(
            amount=Decimal("10000"),
            payment_date=date(2026, 1, 27),
            payment_form="cash",
        )
        .due_with_description(
            quantity=30,
            unit="Dzień",
            starting_event="Otrzymanie faktury",
        )
        .bank_account(
            "73111111111111111111111111",
            bank_name="Bank Bankowości Bankowej S. A.",
            account_description="PLN",
        )
        .done()
        .done()
    )

    _assert_vat_sample("FA_3_Przykład_8.xml", builder)


@pytest.mark.integration
def test_new_fa3_vat_builder_sample_9_exempt_mix_matches_loaded_sample() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 15, 9, 30, 47, tzinfo=timezone.utc),
            system_info="Samplofaktur",
        )
        .seller(
            name="ABC Leasing S.A.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Kwiatowa 1 m. 2",
            address_line_2="00-001 Warszawa",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(
            name="Gmina Bzdziszewo",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="Bzdziszewo 1",
            address_line_2="00-007 Bzdziszewo",
            customer_number="fdfd778343",
            jst_subordinate_unit=True,
            email="bzdziszewo@tuwartoinwestowac.pl",
            phone="555777999",
        )
    )

    _ = builder.add_third_party_model(
        InvoiceThirdParty(
            tax_id="2222222222",
            name="Szkoła Podstawowa w Bzdziszewie",
            address=InvoiceAddress(
                country_code="PL",
                address_line_1="ul. Akacjowa 200",
                address_line_2="00-007 Bzdziszewo",
            ),
            contact=ContactInfo(email="sp@bzdziszewo.p", phone="666888999"),
            role="jst_recipient",
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
        builder.standard()
        .issue_date(date(2026, 2, 15))
        .issue_place("Warszawa")
        .invoice_number("FV2026/02/150")
        .billing_period(period_start=date(2026, 1, 1), period_end=date(2026, 1, 1))
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("2000.00"),
                base_rate_vat_total=Decimal("460.00"),
                exempt_total=Decimal("300.00"),
                total_gross=Decimal("2760.00"),
            )
        )
        .add_description(
            key="część odsetkowa raty",
            value="netto 200, vat 46",
        )
        .rows()
        .add_line(
            name="rata leasingowa za 01/2026",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("2000"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339990",
        )
        .add_line(
            name="pakiet ubezpieczeń za 01/2026",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("300"),
            vat_rate=VatRate.EXEMPT,
            unique_id="aaaa111133339991",
        )
        .done()
        .annotations()
        .tax_exemption(legal_basis_act="art. 43 ust. 1 pkt 37 ustawy VAT")
        .done()
        .payment()
        .via("bank_transfer")
        .due_on(date(2026, 3, 15))
        .bank_account(
            "73111111111111111111111111",
            bank_name="Bank Bankowości Bankowej S. A.",
            account_description="PLN",
        )
        .done()
        .done()
    )

    _assert_vat_sample("FA_3_Przykład_9.xml", builder)


@pytest.mark.integration
def test_new_fa3_vat_builder_sample_ksef_05_wdt_matches_loaded_sample() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 12, 10, 8, 0, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="EXPORT-TECH sp. z o.o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Eksportowa 50",
            address_line_2="00-500 Warszawa",
            email="export@export-tech.pl",
            phone="+48225556677",
        )
        .buyer(
            name="GERMAN ELECTRONICS GmbH",
            country_code="DE",
            address_line_1="Industriestrasse 100",
            address_line_2="10117 Berlin",
            eu_vat_id="DE999888777",
            email="kontakt@german-electronics.de",
            phone="+49301234567",
        )
    )

    _ = (
        builder.footer()
        .add_information("EXPORT-TECH sp. z o.o. - Kapital zakladowy: 1 000 000 PLN")
        .add_registry(
            krs="0000777888",
            regon="444555666",
            bdo="000077788",
        )
        .done()
    )

    _ = (
        builder.standard()
        .currency("EUR")
        .issue_date(date(2025, 12, 10))
        .issue_place("Warszawa")
        .invoice_number("FW/2025/12/0001")
        .summary_overrides(
            InvoiceSummaryOverrides(
                zero_rate_wdt_total=Decimal("10000.00"),
                total_gross=Decimal("10000.00"),
            )
        )
        .rows()
        .add_line(
            name="Industrial Control Systems - Model ICS-500",
            quantity=Decimal("20"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("500"),
            supply_date=date(2025, 12, 8),
            vat_rate=VatRate.VAT_0,
            sale_category=SaleCategory.ZERO_WDT,
            unique_id="KSEF05-LINE001",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .due_on(date(2026, 1, 10))
        .bank_account(
            "PL61109010140000071219812874",
            "WBKPPLPP",
            bank_name="Santander Bank Polska S.A.",
            account_description="EUR",
        )
        .done()
        .transaction()
        .delivery_terms("DAP Berlin")
        .add_transport(
            transport_type="road",
            cargo_type="parcel",
            carrier_identity=TransactionIdentity(
                tax_id="6666666666",
                name="EU TRANSPORT sp. z o.o.",
            ),
            carrier_address=TransactionAddress(
                country_code="PL",
                address_line_1="ul. Logistyczna 10",
                address_line_2="00-500 Warszawa",
            ),
            shipping_from=TransactionAddress(
                country_code="PL",
                address_line_1="ul. Eksportowa 50",
                address_line_2="00-500 Warszawa",
            ),
            shipping_to=TransactionAddress(
                country_code="DE",
                address_line_1="Industriestrasse 100",
                address_line_2="10117 Berlin",
            ),
        )
        .done()
        .done()
    )

    _assert_vat_sample("KSEF_05_WDT.xml", builder)


@pytest.mark.integration
def test_new_fa3_vat_builder_sample_ksef_06_export_matches_loaded_sample() -> None:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2025, 12, 12, 12, 0, 0, tzinfo=timezone.utc),
            system_info="KSEF_TEST_SUITE",
        )
        .seller(
            name="GLOBAL EXPORT sp. z o.o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Portowa 100",
            address_line_2="80-001 Gdansk",
            email="export@global-export.pl",
            phone="+48585551234",
        )
        .buyer(
            name="EXPORT PARTNER sp. z o.o.",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Handlowa 25",
            address_line_2="80-001 Gdansk",
            email="export@partner.pl",
            phone="+48585559999",
        )
    )

    _ = (
        builder.footer()
        .add_information("GLOBAL EXPORT sp. z o.o. - Kapital zakladowy: 2 000 000 PLN")
        .add_registry(
            krs="0000888999",
            regon="555666777",
            bdo="000088899",
        )
        .done()
    )

    _ = (
        builder.standard()
        .currency("USD")
        .issue_date(date(2025, 12, 12))
        .issue_place("Gdansk")
        .invoice_number("FE/2025/12/0001")
        .summary_overrides(
            InvoiceSummaryOverrides(
                zero_rate_wdt_total=Decimal("15000.00"),
                total_gross=Decimal("15000.00"),
            )
        )
        .rows()
        .add_line(
            name="Premium Industrial Equipment - Model PIE-2000",
            quantity=Decimal("5"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("3000"),
            supply_date=date(2025, 12, 10),
            vat_rate=VatRate.VAT_0,
            sale_category=SaleCategory.ZERO_EXPORT,
            unique_id="KSEF06-LINE001",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .due_on(date(2026, 1, 12))
        .bank_account(
            "PL61109010140000071219812874",
            "WBKPPLPP",
            bank_name="Santander Bank Polska S.A.",
            account_description="USD",
        )
        .done()
        .transaction()
        .delivery_terms("FOB Gdansk")
        .add_transport(
            transport_type="air",
            cargo_type="parcel",
            carrier_identity=TransactionIdentity(
                tax_id="6666666666",
                name="SEA CARGO sp. z o.o.",
            ),
            carrier_address=TransactionAddress(
                country_code="PL",
                address_line_1="ul. Portowa 1",
                address_line_2="80-001 Gdansk",
            ),
            shipping_from=TransactionAddress(
                country_code="PL",
                address_line_1="ul. Portowa 100",
                address_line_2="80-001 Gdansk",
            ),
            shipping_to=TransactionAddress(
                country_code="US",
                address_line_1="1234 Business Boulevard",
                address_line_2="New York, NY 10001",
            ),
        )
        .done()
        .done()
    )

    _assert_vat_sample("KSEF_06_EXP.xml", builder)


def _build_vat_from_oracle(sample_name: str) -> StandardInvoiceBuilder:
    expected_invoice = invoice_from_spec(load_sample(sample_path(sample_name)))
    builder = StandardInvoiceBuilder()
    _ = builder.header_model(expected_invoice.header)
    _ = builder.seller_model(expected_invoice.seller)
    _ = builder.buyer_model(expected_invoice.buyer)
    for party in expected_invoice.third_parties:
        _ = builder.add_third_party_model(party)
    if expected_invoice.footer is not None:
        _ = builder.footer_model(expected_invoice.footer)
    if expected_invoice.attachment is not None:
        _ = builder.attachment_model(expected_invoice.attachment)
    _ = builder.standard().from_model(expected_invoice.body).done()
    return builder


@pytest.mark.integration
@pytest.mark.parametrize("sample_name", VAT_SAMPLES)
def test_new_fa3_vat_samples(sample_name: str) -> None:
    builder = _build_vat_from_oracle(sample_name)
    _assert_vat_sample(sample_name, builder)
