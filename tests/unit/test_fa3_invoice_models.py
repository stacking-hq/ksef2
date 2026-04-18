from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3 import (
    AdvanceOrderLine,
    InvoiceOrder,
    ContactInfo,
    InvoiceAddress,
    InvoiceEntity,
    InvoiceHeader,
    InvoiceTaxExemption,
    KsefInvoiceBody,
    KsefInvoice,
)
from ksef2.domain.models.fa3.body import InvoiceRow, InvoiceType
from ksef2.domain.models.fa3.body import (
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
    VatTreatment,
)


def make_polish_address() -> InvoiceAddress:
    return InvoiceAddress(
        country_code="PL",
        address_line_1="Marszalkowska 10/5",
        address_line_2="00-001 Warszawa",
    )


def make_invoice_line() -> InvoiceRow:
    return InvoiceRow(
        name="Consulting service",
        quantity=Decimal("10"),
        unit_price_net=Decimal("100.00"),
        net_amount=Decimal("1000.00"),
        vat_rate=VatRate.VAT_23,
        vat_amount=Decimal("230.00"),
    )


def test_invoice_entity_accepts_valid_polish_nip() -> None:
    entity = InvoiceEntity(
        tax_id="1234567890",
        name="ACME Sp. z o.o.",
        address=make_polish_address(),
    )

    assert entity.tax_id == "1234567890"


def test_invoice_entity_rejects_invalid_polish_nip() -> None:
    with pytest.raises(ValidationError, match="exactly 10 digits"):
        InvoiceEntity(
            tax_id="12345",
            name="ACME Sp. z o.o.",
            address=make_polish_address(),
        )


def test_foreign_entity_may_omit_tax_id() -> None:
    entity = InvoiceEntity(
        name="Globex GmbH",
        address=InvoiceAddress(
            country_code="de",
            address_line_1="Unter den Linden 1",
            address_line_2="10115 Berlin",
        ),
    )

    assert entity.tax_id is None
    assert entity.address is not None
    assert entity.address.country_code == "DE"


def test_foreign_entity_accepts_other_identifier() -> None:
    entity = InvoiceEntity(
        other_id="US-TAX-9988",
        name="Globex Inc.",
        address=InvoiceAddress(
            country_code="US",
            address_line_1="1 Infinite Loop",
        ),
    )

    assert entity.other_id == "US-TAX-9988"


def test_foreign_entity_accepts_tax_id_when_eu_vat_id_is_provided() -> None:
    entity = InvoiceEntity(
        tax_id="DE123456789",
        eu_vat_id="de123456789",
        name="Globex GmbH",
        address=InvoiceAddress(
            country_code="DE",
            address_line_1="Unter den Linden 1",
        ),
    )

    assert entity.tax_id == "DE123456789"
    assert entity.eu_vat_id == "DE123456789"


def test_foreign_entity_rejects_tax_id_without_eu_vat_id() -> None:
    with pytest.raises(ValidationError, match="eu_vat_id is required"):
        InvoiceEntity(
            tax_id="DE123456789",
            name="Globex GmbH",
            address=InvoiceAddress(
                country_code="DE",
                address_line_1="Unter den Linden 1",
            ),
        )


def test_ksef_invoice_rejects_seller_without_tax_id() -> None:
    with pytest.raises(ValidationError, match="seller tax_id is required"):
        KsefInvoice(
            header=InvoiceHeader(
                generation_timestamp=datetime(2026, 2, 1, 12, 30, 45),
                system_info="ACME ERP",
            ),
            seller=InvoiceEntity(
                name="Seller Sp. z o.o.",
                address=make_polish_address(),
            ),
            buyer=InvoiceEntity(
                name="Buyer Sp. z o.o.",
                address=make_polish_address(),
            ),
            body=KsefInvoiceBody(
                issue_date=date(2026, 3, 29),
                issue_place=None,
                invoice_number="FV/1/2026",
                rows=[make_invoice_line()],
            ),
        )


def test_invoice_body_defaults_currency_to_pln() -> None:
    body = KsefInvoiceBody(
        issue_date=date(2026, 3, 29),
        issue_place=None,
        invoice_number="FV/1/2026",
        rows=[make_invoice_line()],
    )

    assert body.currency == "PLN"


def test_invoice_system_context_accepts_valid_values() -> None:
    context = InvoiceHeader(
        generation_timestamp=datetime(2026, 2, 1, 12, 30, 45),
        system_info="ACME ERP",
    )

    assert context.generation_timestamp == datetime(2026, 2, 1, 12, 30, 45)
    assert context.system_info == "ACME ERP"


def test_invoice_system_context_rejects_too_long_system_info() -> None:
    InvoiceHeader(
        generation_timestamp=datetime(2026, 2, 1, 12, 30, 45),
        system_info="X" * 256,
    )

    with pytest.raises(ValidationError, match="at most 256"):
        InvoiceHeader(
            generation_timestamp=datetime(2026, 2, 1, 12, 30, 45),
            system_info="X" * 257,
        )


def test_invoice_line_accepts_full_fa3_shape() -> None:
    line = InvoiceRow(
        name="Laptop",
        quantity=Decimal("2"),
        unit_price_net=Decimal("3500.12345678"),
        net_amount=Decimal("7000.25"),
        vat_rate=VatRate.VAT_23,
        vat_amount=Decimal("1600.55"),
        unique_id="line-001",
        supply_date=date(2026, 3, 29),
        sku="SKU-001",
        gtin="05901234567890",
        pkwiu="62.01.11.0",
        cn="84713000",
        pkob="1122",
        unit_price_gross=Decimal("4305.15"),
        discount_amount=Decimal("100.25"),
        gross_amount=Decimal("8600.80"),
        vat_rate_xii=Decimal("23"),
        annex_15_marker=True,
        excise_amount=Decimal("0.00"),
        gtu_code="GTU_06",
        procedure="TT_D",
        currency_exchange_rate=Decimal("4.123456"),
        before_correction=False,
    )

    assert line.pkwiu == "62.01.11.0"
    assert line.cn == "84713000"
    assert line.annex_15_marker is True
    assert line.before_correction is False


def test_invoice_line_derives_structured_vat_classification_from_legacy_inputs() -> (
    None
):
    line = InvoiceRow(
        name="WDT service",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        net_amount=Decimal("100.00"),
        vat_rate=VatRate.VAT_0,
        sale_category=SaleCategory.ZERO_WDT,
    )

    assert line.vat_classification is not None
    assert line.vat_classification.treatment is VatTreatment.ZERO_WDT
    assert line.vat_classification.rate == Decimal("0")
    assert line.tax_regime is TaxRegime.STANDARD


def test_invoice_line_derives_legacy_fields_from_structured_vat_classification() -> (
    None
):
    line = InvoiceRow(
        name="Consulting service",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        net_amount=Decimal("100.00"),
        vat_classification=VatClassification(
            treatment=VatTreatment.TAXABLE,
            rate=Decimal("23"),
        ),
    )

    assert line.sale_category is SaleCategory.RATE_23
    assert line.vat_rate is VatRate.VAT_23


def test_invoice_entity_accepts_contact_and_customer_number() -> None:
    entity = InvoiceEntity(
        tax_id="1234567890",
        customer_number="CUST-001",
        name="ACME Sp. z o.o.",
        address=make_polish_address(),
        contact=ContactInfo(email="billing@example.com", phone="+48123456789"),
    )

    assert entity.customer_number == "CUST-001"
    assert entity.contact == ContactInfo(
        email="billing@example.com", phone="+48123456789"
    )


def test_ksef_invoice_accepts_lines_collection() -> None:
    invoice = KsefInvoice(
        header=InvoiceHeader(
            generation_timestamp=datetime(2026, 2, 1, 12, 30, 45),
            system_info="ACME ERP",
        ),
        seller=InvoiceEntity(
            tax_id="1234567890",
            name="Seller Sp. z o.o.",
            address=make_polish_address(),
        ),
        buyer=InvoiceEntity(
            name="Buyer GmbH",
            address=InvoiceAddress(
                country_code="DE",
                address_line_1="Unter den Linden 1",
            ),
        ),
        body=KsefInvoiceBody(
            issue_date=date(2026, 3, 29),
            issue_place=None,
            invoice_number="FV/1/2026",
            rows=[make_invoice_line()],
        ),
    )

    assert len(invoice.body.rows) == 1
    assert invoice.body.rows[0].name == "Consulting service"
    assert invoice.total_net == Decimal("1000.00")
    assert invoice.total_vat == Decimal("230.00")
    assert invoice.total_gross == Decimal("1230.00")


def test_ksef_invoice_rejects_empty_lines_collection() -> None:
    with pytest.raises(
        ValidationError, match="At least one invoice line or order is required"
    ):
        KsefInvoice(
            header=InvoiceHeader(
                generation_timestamp=datetime(2026, 2, 1, 12, 30, 45),
                system_info="ACME ERP",
            ),
            seller=InvoiceEntity(
                tax_id="1234567890",
                name="Seller Sp. z o.o.",
                address=make_polish_address(),
            ),
            buyer=InvoiceEntity(
                name="Buyer GmbH",
                address=InvoiceAddress(
                    country_code="DE",
                    address_line_1="Unter den Linden 1",
                ),
            ),
            body=KsefInvoiceBody(
                issue_date=date(2026, 3, 29),
                issue_place=None,
                invoice_number="FV/1/2026",
                rows=[],
            ),
        )


def test_advance_invoice_body_accepts_order_without_fa_wiersz() -> None:
    body = KsefInvoiceBody(
        issue_date=date(2026, 3, 29),
        issue_place=None,
        invoice_number="FZ/1/2026",
        invoice_type=InvoiceType.ZAL,
        order=InvoiceOrder(
            order_lines=[
                AdvanceOrderLine(
                    name="Projekt",
                    gross_amount=Decimal("1230.00"),
                    vat_rate=VatRate.VAT_23,
                )
            ],
        ),
    )

    assert body.rows == []
    assert len(body.order_lines) == 1
    assert body.total_net == Decimal("1000.00")
    assert body.total_vat == Decimal("230.00")
    assert body.total_gross == Decimal("1230.00")


def test_invoice_address_normalizes_country_code() -> None:
    entity = InvoiceEntity(
        tax_id="1234567890",
        name="ACME Sp. z o.o.",
        address=InvoiceAddress(
            country_code="PL",
            address_line_1="Marszalkowska 10/5",
            address_line_2="00-001 Warszawa",
        ),
    )

    assert entity.address is not None
    assert entity.address.country_code == "PL"


def test_invoice_address_accepts_foreign_shape() -> None:
    entity = InvoiceEntity(
        name="Globex GmbH",
        address=InvoiceAddress(
            country_code="DE",
            address_line_1="Unter den Linden 1",
            address_line_2="10115 Berlin",
        ),
    )

    assert entity.address is not None
    assert entity.address.address_line_1 == "Unter den Linden 1"


def test_invoice_tax_exemption_requires_exactly_one_basis() -> None:
    with pytest.raises(ValidationError, match="Exactly one exemption legal basis"):
        InvoiceTaxExemption(
            legal_basis_act="art. 43 ust. 1 pkt 2 ustawy",
            legal_basis_other="other basis",
        )


def test_invoice_body_rejects_pln_vat_exchange_rate() -> None:
    with pytest.raises(
        ValidationError,
        match="vat_currency_exchange_rate is only valid for non-PLN invoices",
    ):
        KsefInvoiceBody(
            issue_date=date(2026, 3, 29),
            issue_place=None,
            invoice_number="FV/1/2026",
            vat_currency_exchange_rate=Decimal("4.500000"),
            rows=[make_invoice_line()],
        )
