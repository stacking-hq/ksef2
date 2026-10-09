"""Unit tests for FA(3) schema-to-domain mapping of the invoice aggregate.

These cover the read path: the generated FA(3) schema models, as parsed from
invoice XML, mapped back into the ``KsefInvoice`` domain aggregate.
"""

from datetime import date
from decimal import Decimal
from typing import Any
from pathlib import Path

import pytest
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2._domain.models.fa3 import KsefInvoice
from ksef2._domain.models.fa3.body import (
    InvoiceType,
    MarginProcedure,
)
from ksef2._domain.models.fa3.body.root import get_placeholder_invoice_number
from ksef2._infra.mappers.invoices.fa3.spec.correction_party import (
    from_spec as correction_party_from_spec,
)
from ksef2._infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2._infra.mappers.invoices.fa3.spec.subject import (
    from_spec as address_from_spec,
)
from ksef2._infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2._infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2._infra.schema.fa3.models.schemat import (
    Faktura,
    FakturaFaPodmiot1K,
    FakturaFaRozliczenie,
    FakturaFaRozliczenieObciazenia,
    Tadres,
    Tpodmiot1,
)

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "schemas" / "FA3" / "samples"

# Some FA(3) elements are mandatory in the generated models while the mapper
# reads a missing element as absent; UNSET stands in for those.
UNSET: Any = None


def load_sample(name: str) -> Faktura:
    parser = XmlParser()
    return parser.from_bytes((SAMPLES_DIR / name).read_bytes(), Faktura)


def sample_names() -> list[str]:
    return sorted(path.name for path in SAMPLES_DIR.glob("*.xml"))


def test_shipped_sample_directory_is_not_empty() -> None:
    assert len(sample_names()) >= 30


@pytest.mark.parametrize("sample_name", sample_names())
def test_shipped_sample_maps_to_the_domain_aggregate(sample_name: str) -> None:
    invoice = invoice_from_spec(load_sample(sample_name))

    assert isinstance(invoice, KsefInvoice)
    assert invoice.header.system_info
    assert invoice.header.generation_timestamp is not None
    assert invoice.seller.name
    assert invoice.buyer is not None
    assert invoice.body.invoice_number
    assert isinstance(invoice.body.rows, list)
    assert all(row.name for row in invoice.body.rows)


@pytest.mark.parametrize(
    ("sample_name", "expected_type"),
    [
        ("KSEF_01_VAT_STANDARD.xml", InvoiceType.VAT),
        ("KSEF_02_KOR.xml", InvoiceType.CORRECTING),
        ("KSEF_03_ZAL.xml", InvoiceType.ZAL),
        ("KSEF_04_UPR.xml", InvoiceType.UPR),
        ("KSEF_09_ROZ_A.xml", InvoiceType.ROZ),
        ("KSEF_07_KOR_ZAL_A.xml", InvoiceType.CORRECTING_ZAL),
        ("KSEF_11_KOR_ROZ_A.xml", InvoiceType.CORRECTING_ROZ),
    ],
)
def test_invoice_type_maps_from_rodzaj_faktury(
    sample_name: str,
    expected_type: InvoiceType,
) -> None:
    invoice = invoice_from_spec(load_sample(sample_name))

    assert invoice.body.invoice_type is expected_type


def test_maps_header_seller_buyer_and_footer() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_01_VAT_STANDARD.xml"))

    assert (
        invoice.header.generation_timestamp.isoformat() == "2025-12-15T10:30:00+00:00"
    )
    assert invoice.header.system_info == "KSEF_TEST_SUITE"

    assert invoice.seller.tax_id == "9999999999"
    assert invoice.seller.name == "TECH-SOLUTIONS sp. z o.o."
    seller_address = invoice.seller.address
    assert seller_address is not None
    assert seller_address.address_line_1 == "ul. Marszalkowska 100"
    assert seller_address.country_code == "PL"
    assert invoice.seller.contact is not None
    assert invoice.seller.contact.email == "biuro@tech-solutions.pl"
    assert invoice.seller.vat_group_member is False

    assert invoice.buyer.tax_id == "1111111111"
    assert invoice.buyer.customer_number == "ABC-001"
    buyer_address = invoice.buyer.address
    assert buyer_address is not None
    assert buyer_address.address_line_2 == "60-001 Poznan"

    assert invoice.footer is not None
    assert invoice.footer.additional_informations == [
        "TECH-SOLUTIONS sp. z o.o. - Kapital zakladowy: 500 000 PLN"
    ]
    assert invoice.footer.registries is not None
    assert invoice.footer.registries[0].krs == "0000123456"
    assert invoice.footer.registries[0].regon == "146025969"


def test_maps_rows_and_summary_overrides() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_01_VAT_STANDARD.xml"))
    row = invoice.body.rows[0]

    assert len(invoice.body.rows) == 1
    assert row.name == "Laptop Dell XPS 15"
    assert row.quantity == Decimal("2")
    assert row.unit_of_measure == "szt."
    assert row.unit_price_net == Decimal("2032.52")
    assert row.net_amount == Decimal("4065.04")
    assert row.vat_amount == Decimal("934.96")
    assert row.gross_amount == Decimal("5000.00")
    assert row.vat_rate is not None
    assert Decimal(row.vat_rate.value) == Decimal("23")
    assert row.unique_id == "KSEF01-LINE001"

    overrides = invoice.body.summary_overrides
    assert overrides is not None
    assert overrides.base_rate_net_total == Decimal("4065.04")
    assert overrides.base_rate_vat_total == Decimal("934.96")
    assert overrides.total_gross == Decimal("5000.00")
    assert overrides.zero_rate_wdt_total is None


def test_maps_payment_forms_terms_and_bank_accounts() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_01_VAT_STANDARD.xml"))
    payment = invoice.body.payment

    assert payment is not None
    assert payment.paid is False
    assert payment.payment_form == "bank_transfer"
    assert payment.payment_terms is not None
    assert payment.payment_terms[0].due_date == date(2026, 1, 15)
    assert payment.bank_accounts is not None
    assert payment.bank_accounts[0].account_number == ("PL61109010140000071219812874")
    assert payment.bank_accounts[0].bank_name == "Santander Bank Polska S.A."


def test_maps_advance_payment_received_on_a_zal_invoice() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_03_ZAL.xml"))

    assert invoice.body.payment is not None
    assert invoice.body.payment.paid is True
    assert invoice.body.payment.payment_date == date(2025, 10, 1)
    assert [
        (entry.key, entry.value.replace("/", "-"))
        for entry in invoice.body.additional_description
    ] == [
        ("Wysokosc wplaconego zadatku", "50 000 PLN"),
        ("Umowa przedwstepna", "UP-2025-09-0001 z dnia 2025-09-15"),
    ]


def test_maps_order_block_into_order_lines() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_03_ZAL.xml"))
    order = invoice.body.order

    assert order is not None
    assert order.total_value == Decimal("500000.00")
    assert invoice.body.rows == []
    assert len(order.order_lines) == 1
    assert order.order_lines[0].name is not None
    assert order.order_lines[0].name.startswith("Mieszkanie 60m2")
    assert order.order_lines[0].net_amount == Decimal("406504.07")
    assert order.order_lines[0].gross_amount == Decimal("500000.00")


def test_maps_advance_invoice_references_on_a_final_invoice() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_10_ROZ_B.xml"))
    advance = invoice.body.advance

    assert advance is not None
    assert advance.advance_partial_payments == []
    assert len(advance.advance_invoice_references) == 2
    assert advance.advance_invoice_references[0].ksef_id == (
        "9999999999-20251001-A1B2C3-D4E5F6-AB"
    )
    assert advance.advance_invoice_references[0].outside_ksef is False


def test_maps_transaction_conditions_and_carrier() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_05_WDT.xml"))
    conditions = invoice.body.transaction_conditions

    assert conditions is not None
    assert conditions.delivery_terms == "DAP Berlin"
    assert conditions.transports is not None
    transport = conditions.transports[0]
    assert transport.transport_type == "road"
    assert transport.cargo_type == "parcel"
    assert transport.carrier_identity is not None
    assert transport.carrier_identity.tax_id == "6666666666"
    assert transport.shipping_from is not None
    assert transport.shipping_from.country_code == "PL"
    assert transport.shipping_to is not None
    assert transport.shipping_to.country_code == "DE"

    overrides = invoice.body.summary_overrides
    assert overrides is not None
    assert overrides.zero_rate_wdt_total == Decimal("10000.00")


def test_maps_warehouse_documents_and_transaction_orders() -> None:
    invoice = invoice_from_spec(load_sample("FA_3_Przykład_4.xml"))

    assert invoice.body.warehouse_documents == ["44343434/2026"]
    conditions = invoice.body.transaction_conditions
    assert conditions is not None
    assert conditions.orders is not None
    assert conditions.orders[0].order_number == "4354343"
    assert conditions.orders[0].order_date == date(2026, 1, 26)
    assert conditions.lot_numbers == ["2312323/2026"]
    assert conditions.transports is not None
    assert conditions.transports[0].packaging_unit == "a"

    payment = invoice.body.payment
    assert payment is not None
    assert payment.factor_bank_accounts is not None
    assert payment.factor_bank_accounts[0].own_bank_account_type == (
        "factor_collection"
    )


def test_maps_settlement_charges_and_deductions() -> None:
    invoice = invoice_from_spec(load_sample("FA_3_Przykład_24.xml"))
    settlement = invoice.body.settlement

    assert settlement is not None
    assert settlement.charges is not None
    assert settlement.charges[0].amount == Decimal("0.00")
    assert settlement.charges[0].reason == "Odsetki"
    assert settlement.deductions is not None
    assert settlement.deductions[0].reason == "Nadpłata"
    assert settlement.amount_due == Decimal("53.63")
    assert invoice.body.period_start == date(2026, 1, 1)
    assert invoice.body.period_end == date(2026, 2, 28)


def test_maps_attachment_data_blocks_and_tables() -> None:
    invoice = invoice_from_spec(load_sample("FA_3_Przykład_24.xml"))

    assert invoice.attachment is not None
    assert len(invoice.attachment.data_blocks) == 1
    block = invoice.attachment.data_blocks[0]
    assert block.tables is not None
    assert len(block.tables) == 3
    assert block.tables[0].description == "Odczyty"
    assert block.tables[0].columns_format is not None
    assert block.tables[0].columns_format[:3] == ["txt", "date", "integer"]
    assert block.tables[0].rows is not None
    assert block.tables[0].rows[1] == [
        "całodobowa",
        "2026-02-28",
        "1020",
        "1000",
        "1",
        "20",
        "Fizyczny",
        "0",
        "20",
    ]
    assert block.tables[1].summary is not None
    assert block.tables[1].summary[0] == "Ogółem wartość - sprzedaż energii:"


def test_maps_margin_procedure_annotation() -> None:
    invoice = invoice_from_spec(load_sample("FA_3_Przykład_8.xml"))
    annotations = invoice.body.annotations

    assert annotations is not None
    assert annotations.margin_procedure is MarginProcedure.USED_GOODS
    assert invoice.body.fp_invoice is True
    overrides = invoice.body.summary_overrides
    assert overrides is not None
    assert overrides.margin_total == Decimal("15000.00")


def test_maps_third_party_roles() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_09_ROZ_A.xml"))

    assert len(invoice.third_parties) == 2
    assert invoice.third_parties[0].name == "FINANSE PLUS sp. z o.o."
    assert invoice.third_parties[0].role == "additional_buyer"
    assert invoice.third_parties[0].share_percentage == Decimal("100")
    assert invoice.third_parties[1].role == "original_subject"
    assert invoice.third_parties[1].share_percentage is None


def test_maps_upr_invoice_without_buyer_name_or_issue_place() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_04_UPR.xml"))

    assert invoice.body.issue_place is None
    assert invoice.buyer.name is None
    assert invoice.buyer.tax_id == "1111111111"
    assert [row.name for row in invoice.body.rows] == ["Artykuly biurowe (zestaw)"]
    overrides = invoice.body.summary_overrides
    assert overrides is not None
    assert overrides.total_gross == Decimal("369.00")


@pytest.mark.parametrize(
    ("sample_name", "expected_effect"),
    [
        ("FA_3_Przykład_12.xml", "original_entry_date"),
        ("FA_3_Przykład_6.xml", "correction_issue_date"),
        ("KSEF_02_KOR.xml", "other_date"),
    ],
)
def test_correction_effect_type_maps_from_typ_korekty(
    sample_name: str,
    expected_effect: str,
) -> None:
    invoice = invoice_from_spec(load_sample(sample_name))
    correction = invoice.body.correction

    assert correction is not None
    assert correction.correction_effect_type == expected_effect
    assert correction.corrected_invoices


def test_maps_correction_reference_period_and_before_correction_rows() -> None:
    invoice = invoice_from_spec(load_sample("FA_3_Przykład_6.xml"))
    correction = invoice.body.correction

    assert correction is not None
    assert correction.corrected_invoice_period == "pierwsze półrocze 2026"
    assert len(correction.corrected_invoices) == 6
    assert correction.corrected_invoices[0].invoice_number.replace("/", "-") == (
        "FV2026-01-134"
    )
    assert correction.corrected_invoices[0].issue_date == date(2026, 1, 15)


def test_maps_before_correction_row_marker() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_02_KOR.xml"))

    assert [row.before_correction for row in invoice.body.rows] == [True, False]


def test_maps_corrected_buyer_from_podmiot2_k() -> None:
    invoice = invoice_from_spec(load_sample("FA_3_Przykład_5.xml"))
    correction = invoice.body.correction

    assert correction is not None
    assert len(correction.corrected_buyers) == 1
    buyer = correction.corrected_buyers[0]
    assert buyer.name == "CDE sp. j."
    assert buyer.tax_id == "1111111111"
    assert buyer.buyer_id == "0001"
    assert buyer.address is not None
    assert buyer.address.country_code == "PL"


def test_maps_string_amounts_and_dates_from_a_loosely_typed_spec() -> None:
    spec = load_sample("KSEF_01_VAT_STANDARD.xml")
    spec.fa.p_1 = "2025-12-15"
    spec.fa.p_13_1 = "4065.04"
    spec.fa.p_15 = "5000.00"

    invoice = invoice_from_spec(spec)

    assert invoice.body.issue_date == date(2025, 12, 15)
    overrides = invoice.body.summary_overrides
    assert overrides is not None
    assert overrides.base_rate_net_total == Decimal("4065.04")
    assert overrides.total_gross == Decimal("5000.00")


def test_maps_excise_return_and_outside_ksef_correction_reference() -> None:
    spec = load_sample("KSEF_02_KOR.xml")
    spec.fa.zwrot_akcyzy = Twybor1.VALUE_1
    reference = spec.fa.dane_fa_korygowanej[0]
    reference.nr_kse_fn = Twybor1.VALUE_1
    reference.nr_kse_ffa_korygowanej = None

    invoice = invoice_from_spec(spec)

    assert invoice.body.return_of_excise is True
    correction = invoice.body.correction
    assert correction is not None
    assert correction.corrected_invoices[0].outside_ksef is True
    assert correction.corrected_invoices[0].ksef_id is None


def test_absent_excise_return_stays_none() -> None:
    invoice = invoice_from_spec(load_sample("KSEF_01_VAT_STANDARD.xml"))

    assert invoice.body.return_of_excise is None


def test_summary_overrides_is_none_when_the_spec_has_no_totals() -> None:
    spec = load_sample("KSEF_01_VAT_STANDARD.xml")
    for field in (
        "p_13_1",
        "p_14_1",
        "p_14_1_w",
        "p_13_2",
        "p_14_2",
        "p_14_2_w",
        "p_13_3",
        "p_14_3",
        "p_14_3_w",
        "p_13_4",
        "p_14_4",
        "p_14_4_w",
        "p_13_5",
        "p_14_5",
        "p_13_6_1",
        "p_13_6_2",
        "p_13_6_3",
        "p_13_7",
        "p_13_8",
        "p_13_9",
        "p_13_10",
        "p_13_11",
        "p_15",
    ):
        setattr(spec.fa, field, None)

    invoice = invoice_from_spec(spec)

    assert invoice.body.summary_overrides is None


def test_missing_invoice_number_falls_back_to_the_placeholder() -> None:
    spec = load_sample("KSEF_01_VAT_STANDARD.xml")
    setattr(spec.fa, "p_2", None)

    invoice = invoice_from_spec(spec)

    assert invoice.body.invoice_number == get_placeholder_invoice_number()


def test_missing_issue_date_is_rejected() -> None:
    spec = load_sample("KSEF_01_VAT_STANDARD.xml")
    setattr(spec.fa, "p_1", None)

    with pytest.raises(ValueError, match="p_1 is required for FA\\(3\\) mapping"):
        invoice_from_spec(spec)


def test_settlement_charge_without_amount_is_rejected() -> None:
    spec = load_sample("FA_3_Przykład_24.xml")
    spec.fa.rozliczenie = FakturaFaRozliczenie(
        obciazenia=[FakturaFaRozliczenieObciazenia(kwota=UNSET, powod="Odsetki")],
        odliczenia=[],
    )

    with pytest.raises(
        ValueError, match="rozliczenie.kwota is required for FA\\(3\\) mapping"
    ):
        invoice_from_spec(spec)


def test_corrected_seller_maps_from_podmiot1_k() -> None:
    seller = correction_party_from_spec(
        FakturaFaPodmiot1K(
            prefiks_podatnika=None,
            dane_identyfikacyjne=Tpodmiot1(
                nip="1234567890",
                nazwa="Old Seller Sp. z o.o.",
            ),
            adres=Tadres(
                kod_kraju=TkodKraju.PL,
                adres_l1="Marszalkowska 10/5",
                adres_l2="00-001 Warszawa",
                gln=None,
            ),
        )
    )

    assert seller.name == "Old Seller Sp. z o.o."
    assert seller.tax_id == "1234567890"
    assert seller.address is not None
    assert seller.address.address_line_1 == "Marszalkowska 10/5"


def test_corrected_seller_without_name_is_rejected() -> None:
    schema = FakturaFaPodmiot1K(
        dane_identyfikacyjne=Tpodmiot1(nip="1234567890", nazwa=UNSET),
        adres=Tadres(kod_kraju=TkodKraju.PL, adres_l1="Marszalkowska 10/5"),
    )

    with pytest.raises(
        ValueError, match="Corrected seller name is required for FA\\(3\\) mapping"
    ):
        correction_party_from_spec(schema)


def test_address_maps_country_code_and_gln() -> None:
    address = address_from_spec(
        Tadres(
            kod_kraju=TkodKraju.DE,
            adres_l1="Unter den Linden 1",
            adres_l2=None,
            gln="5900000000001",
        )
    )

    assert address.country_code == "DE"
    assert address.address_line_1 == "Unter den Linden 1"
    assert address.gln == "5900000000001"
