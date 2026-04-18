from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3.body import InvoiceSummaryOverrides, VatRate
from ksef2.infra.mappers.invoices.fa3.spec.invoice import from_spec as invoice_from_spec
from ksef2.infra.schema.fa3.models.schemat import Faktura
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder
from tests.integration.builders.helpers import load_sample, sample_path


@pytest.mark.integration
def test_new_fa3_standard_builder_sample_1_matches_loaded_sample() -> None:
    parser = XmlParser()
    expected_spec = load_sample(sample_path("FA_3_Przykład_1.xml"))
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
        builder.standard()
        .issue_date(date(2026, 2, 15))
        .issue_place("Warszawa")
        .invoice_number("FV2026/02/150")
        .date_of_supply(date(2026, 1, 27))
        .mark_fp()
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("1666.66"),
                base_rate_vat_total=Decimal("383.33"),
                second_reduced_rate_net_total=Decimal("0.95"),
                second_reduced_rate_vat_total=Decimal("0.05"),
                total_gross=Decimal("2051.00"),
            )
        )
        .add_description(
            key="preferowane godziny dowozu",
            value="dni robocze 17:00 - 20:00",
        )
        .rows()
        .add_line(
            name="lodówka Zimnotech mk1",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("1626.01"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339990",
        )
        .add_line(
            name="wniesienie sprzętu",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("40.65"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339991",
        )
        .add_line(
            name="promocja lodówka pełna mleka",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("0.95"),
            vat_rate=VatRate.VAT_5,
            unique_id="aaaa111133339992",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .already_paid(date(2026, 1, 27))
        .done()
        .transaction()
        .add_order(order_date=date(2026, 1, 26), order_number="4354343")
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
    assert actual_spec.fa.fa_wiersz[0].p_7 == expected_spec.fa.fa_wiersz[0].p_7
    assert len(actual_spec.fa.fa_wiersz) == len(expected_spec.fa.fa_wiersz)

    assert actual_invoice == expected_invoice
    assert xml_invoice == expected_invoice
