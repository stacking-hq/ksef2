"""Unit tests for the seven FA(3) invoice-body builders reached from the public builder."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from ksef2.fa3 import FA3InvoiceBuilder, VatRate
from ksef2._domain.models.fa3.body import (
    AdditionalDescriptionEntry,
    InvoiceSummaryOverrides,
    InvoiceType,
)
from ksef2._services.builders.fa3.body.advance import AdvanceBodyBuilder
from ksef2._services.builders.fa3.body.correction import CorrectionBodyBuilder
from ksef2._services.builders.fa3.body.correction_advance import (
    CorrectionAdvanceBodyBuilder,
)
from ksef2._services.builders.fa3.body.correction_settlement import (
    CorrectionSettlementBodyBuilder,
)
from ksef2._services.builders.fa3.body.settlement import SettlementBodyBuilder
from ksef2._services.builders.fa3.body.simplified import SimplifiedBodyBuilder
from ksef2._services.builders.fa3.body.standard import StandardBodyBuilder

KSEF_ID = "20260315-1234567890-ABCDEF1234567890"


def started_invoice() -> FA3InvoiceBuilder:
    builder = FA3InvoiceBuilder()
    _ = builder.header(system_info="billing-service")
    _ = builder.seller(
        name="ACME S.A.",
        tax_id="1234567890",
        country_code="PL",
        address_line_1="ul. Przykladowa 123",
    )
    _ = builder.buyer(
        name="XYZ GmbH",
        country_code="PL",
        address_line_1="Unter den Linden 1",
    )
    return builder


def add_rows(body: Any) -> None:
    _ = (
        body.rows()
        .add_line(
            name="Consulting service",
            unit_of_measure="h",
            quantity=Decimal("1"),
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
    )


def add_order(body: Any) -> None:
    _ = (
        body.order()
        .total_value(Decimal("123.00"))
        .add_line(
            name="Prepayment for consulting service",
            gross_amount=Decimal("123.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
    )


def add_correction(body: Any) -> None:
    _ = (
        body.correction()
        .reason("Price reduction after complaint")
        .effect_type("correction_issue_date")
        .corrected_invoice_period("2026-03")
        .add_corrected_invoice(
            issue_date=date(2026, 3, 15),
            invoice_number="FV/2026/03/0015",
            ksef_id=KSEF_ID,
        )
        .done()
    )


def add_advance_reference(body: Any) -> None:
    _ = (
        body.advance()
        .add_invoice_reference(
            ksef_id=KSEF_ID,
            deduction_amount=Decimal("500.00"),
            deduction_reason="Advance already settled",
        )
        .done()
    )


def prepared_body(builder: FA3InvoiceBuilder, entry: str) -> Any:
    """Open one body builder and fill in whatever that invoice type requires."""
    body = getattr(builder, entry)()
    if entry in {"standard", "simplified", "correction_settlement"}:
        add_rows(body)
    elif entry == "correction":
        add_correction(body)
        add_rows(body)
    elif entry == "advance":
        add_order(body)
    elif entry == "correction_advance":
        add_correction(body)
        add_order(body)
    else:
        add_advance_reference(body)
        add_rows(body)
    return body


BodyCase = tuple[str, Any, InvoiceType]
BODY_CASES: list[BodyCase] = [
    ("standard", StandardBodyBuilder, InvoiceType.VAT),
    ("simplified", SimplifiedBodyBuilder, InvoiceType.UPR),
    ("correction", CorrectionBodyBuilder, InvoiceType.CORRECTING),
    ("advance", AdvanceBodyBuilder, InvoiceType.ZAL),
    ("settlement", SettlementBodyBuilder, InvoiceType.ROZ),
    ("correction_advance", CorrectionAdvanceBodyBuilder, InvoiceType.CORRECTING_ZAL),
    (
        "correction_settlement",
        CorrectionSettlementBodyBuilder,
        InvoiceType.CORRECTING_ROZ,
    ),
]


@pytest.mark.parametrize(
    ("entry", "builder_class", "expected_type"),
    BODY_CASES,
    ids=[case[0] for case in BODY_CASES],
)
def test_body_builder_marks_the_invoice_type(
    entry: str,
    builder_class: Any,
    expected_type: InvoiceType,
) -> None:
    builder = started_invoice()

    body = prepared_body(builder, entry)

    assert isinstance(body, builder_class)
    assert body.build().invoice_type is expected_type
    draft = builder.dump_state()
    assert draft.body is None


@pytest.mark.parametrize(
    ("entry", "builder_class", "expected_type"),
    BODY_CASES,
    ids=[case[0] for case in BODY_CASES],
)
def test_body_builder_done_attaches_the_body_to_the_invoice(
    entry: str,
    builder_class: Any,
    expected_type: InvoiceType,
) -> None:
    builder = started_invoice()
    body = prepared_body(builder, entry)
    prepared = body.build()

    parent = body.done()

    assert isinstance(parent, FA3InvoiceBuilder)
    draft = builder.dump_state()
    assert draft.body == prepared
    assert draft.body is not None
    assert draft.body.invoice_type is expected_type


@pytest.mark.parametrize(
    ("entry", "builder_class", "expected_type"),
    BODY_CASES,
    ids=[case[0] for case in BODY_CASES],
)
def test_body_builder_without_a_parent_cannot_be_finished(
    entry: str,
    builder_class: Any,
    expected_type: InvoiceType,
) -> None:
    with pytest.raises(ValueError, match=f"{builder_class.__name__} requires a parent"):
        builder_class().done()


@pytest.mark.parametrize(
    ("entry", "builder_class", "expected_type"),
    BODY_CASES,
    ids=[case[0] for case in BODY_CASES],
)
def test_body_builder_restores_a_domain_model(
    entry: str,
    builder_class: Any,
    expected_type: InvoiceType,
) -> None:
    prepared = prepared_body(started_invoice(), entry).build()

    restored = builder_class().from_model(prepared).build()

    assert restored == prepared


@pytest.mark.parametrize(
    ("entry", "builder_class", "expected_type"),
    BODY_CASES,
    ids=[case[0] for case in BODY_CASES],
)
def test_body_builder_starts_from_an_existing_model(
    entry: str,
    builder_class: Any,
    expected_type: InvoiceType,
) -> None:
    prepared = prepared_body(started_invoice(), entry).build()

    copied = builder_class(existing_state=prepared).build()

    assert copied == prepared


def test_base_body_fields_land_in_the_built_body() -> None:
    builder = started_invoice()
    body = builder.standard()

    _ = (
        body.currency("EUR")
        .issue_date(date(2026, 3, 29))
        .issue_place("Warszawa")
        .invoice_number("FV/2026/03/0001")
        .add_warehouse_document("WZ/2026/0001")
        .replace_warehouse_documents(["WZ/2026/0002"])
        .billing_period(period_start=date(2026, 3, 1), period_end=date(2026, 3, 31))
        .vat_currency_exchange_rate(Decimal("4.2500"))
        .mark_fp()
        .related_party_transaction(True)
        .add_description(key="campaign", value="spring-2026", row_number=1)
        .return_of_excise(True)
        .summary_overrides(InvoiceSummaryOverrides(total_gross=Decimal("123.00")))
    )
    add_rows(body)
    built = body.build()

    assert built.currency == "EUR"
    assert built.issue_date == date(2026, 3, 29)
    assert built.issue_place == "Warszawa"
    assert built.invoice_number == "FV/2026/03/0001"
    assert built.warehouse_documents == ["WZ/2026/0002"]
    assert built.period_start == date(2026, 3, 1)
    assert built.period_end == date(2026, 3, 31)
    assert built.vat_currency_exchange_rate == Decimal("4.2500")
    assert built.fp_invoice is True
    assert built.related_party_transaction is True
    assert built.return_of_excise is True
    assert [(e.key, e.value, e.row_number) for e in built.additional_description] == [
        ("campaign", "spring-2026", 1)
    ]
    assert built.summary_overrides is not None
    assert built.summary_overrides.total_gross == Decimal("123.00")
    assert len(built.rows) == 1


def test_supply_date_and_billing_period_are_alternatives() -> None:
    builder = started_invoice()
    body = builder.standard()

    _ = body.date_of_supply(date(2026, 3, 28))
    add_rows(body)

    built = body.build()
    assert built.date_of_supply == date(2026, 3, 28)
    assert built.period_start is None

    with pytest.raises(ValueError, match="cannot be combined with period_start"):
        _ = body.billing_period(
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
        ).build()


def test_base_body_collections_can_be_cleared_and_replaced_by_models() -> None:
    builder = started_invoice()
    body = builder.standard()

    _ = (
        body.add_warehouse_document("WZ/2026/0001")
        .clear_warehouse_documents()
        .add_description(key="dropped", value="x")
        .clear_descriptions()
        .add_description_model(
            AdditionalDescriptionEntry(key="contract", value="A-2026", row_number=1)
        )
        .mark_fp(False)
        .related_party_transaction(False)
        .return_of_excise(None)
        .summary_overrides(None)
    )
    add_rows(body)
    built = body.build()

    assert built.warehouse_documents == []
    assert [entry.key for entry in built.additional_description] == ["contract"]
    assert built.fp_invoice is False
    assert built.related_party_transaction is False
    assert built.return_of_excise is None
    assert built.summary_overrides is None


def test_body_from_model_replaces_the_previous_state() -> None:
    prepared = prepared_body(started_invoice(), "standard").build()

    body = StandardBodyBuilder()
    _ = body.invoice_number("OLD")
    restored = body.from_model(prepared).build()

    assert restored.invoice_number == prepared.invoice_number
    assert restored == prepared
