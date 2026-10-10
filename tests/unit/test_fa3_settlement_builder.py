"""Unit tests for the FA(3) settlement sub-builder reached from the public builder."""

from decimal import Decimal
from typing import Any

import pytest

from ksef2.fa3 import FA3InvoiceBuilder, VatRate
from ksef2._domain.models.fa3.body import (
    InvoiceSettlement,
    SettlementCharge,
    SettlementDeduction,
)
from ksef2._services.builders.fa3.sub.settlement import SettlementBuilder


def started_standard_body() -> Any:
    """Open a standard body on an invoice whose header, seller and buyer are set."""
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
    return builder.standard()


def with_one_line(body: Any) -> None:
    """Close the rows and body sub-builders so the draft holds a complete body."""
    rows = body.rows().add_line(
        name="Consulting service",
        unit_of_measure="h",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        vat_rate=VatRate.VAT_23,
    )
    rows.done().done()


def test_settlement_starts_empty() -> None:
    body = started_standard_body()
    with_one_line(body)

    settlement = body.settlement().build()

    assert settlement.charges == []
    assert settlement.charges_total == Decimal("0.00")
    assert settlement.deductions == []
    assert settlement.deductions_total == Decimal("0.00")
    assert settlement.amount_due is None
    assert settlement.amount_to_settle is None


def test_add_charge_appends_rounded_charge() -> None:
    settlement = (
        started_standard_body()
        .settlement()
        .add_charge(amount=Decimal("50.004"), reason="Delivery surcharge")
        .add_charge(amount=Decimal("12.50"), reason="Packaging")
        .build()
    )

    assert [charge.amount for charge in settlement.charges] == [
        Decimal("50.00"),
        Decimal("12.50"),
    ]
    assert [charge.reason for charge in settlement.charges] == [
        "Delivery surcharge",
        "Packaging",
    ]
    assert settlement.charges_total == Decimal("62.50")


def test_add_deduction_appends_rounded_deduction() -> None:
    settlement = (
        started_standard_body()
        .settlement()
        .add_deduction(amount=Decimal("100"), reason="Advance paid earlier")
        .build()
    )

    assert settlement.deductions == [
        SettlementDeduction(amount=Decimal("100.00"), reason="Advance paid earlier")
    ]
    assert settlement.deductions_total == Decimal("100.00")


def test_add_charge_model_adds_an_existing_model() -> None:
    charge = SettlementCharge(amount=Decimal("30.00"), reason="Freight")

    settlement = started_standard_body().settlement().add_charge_model(charge).build()

    assert settlement.charges == [charge]


def test_add_deduction_model_adds_an_existing_model() -> None:
    deduction = SettlementDeduction(amount=Decimal("7.50"), reason="Discount")

    settlement = (
        started_standard_body().settlement().add_deduction_model(deduction).build()
    )

    assert settlement.deductions == [deduction]


def test_clear_charges_removes_charges_and_their_total() -> None:
    settlement = (
        started_standard_body()
        .settlement()
        .add_charge(amount=Decimal("50.00"), reason="Freight")
        .charges_total(Decimal("50.00"))
        .add_deduction(amount=Decimal("10.00"), reason="Discount")
        .clear_charges()
        .build()
    )

    assert settlement.charges == []
    assert settlement.deductions_total == Decimal("10.00")


def test_clear_deductions_removes_deductions_and_their_total() -> None:
    settlement = (
        started_standard_body()
        .settlement()
        .add_deduction(amount=Decimal("10.00"), reason="Discount")
        .deductions_total(Decimal("10.00"))
        .add_charge(amount=Decimal("50.00"), reason="Freight")
        .clear_deductions()
        .build()
    )

    assert settlement.deductions == []
    assert settlement.charges_total == Decimal("50.00")


def test_explicit_totals_are_kept_when_they_match_the_entries() -> None:
    settlement = (
        started_standard_body()
        .settlement()
        .add_charge(amount=Decimal("50.00"), reason="Freight")
        .charges_total(Decimal("50.00"))
        .add_deduction(amount=Decimal("10.00"), reason="Discount")
        .deductions_total(Decimal("10.00"))
        .build()
    )

    assert settlement.charges_total == Decimal("50.00")
    assert settlement.deductions_total == Decimal("10.00")


def test_amount_due_and_amount_to_settle_are_separate_overrides() -> None:
    due = started_standard_body().settlement().amount_due(Decimal("950.00")).build()
    to_settle = (
        started_standard_body().settlement().amount_to_settle(Decimal("450")).build()
    )

    assert due.amount_due == Decimal("950.00")
    assert due.amount_to_settle is None
    assert to_settle.amount_to_settle == Decimal("450.00")
    assert to_settle.amount_due is None


def test_setting_both_balances_is_rejected_on_build() -> None:
    with pytest.raises(ValueError, match="cannot be provided together"):
        _ = (
            started_standard_body()
            .settlement()
            .amount_due(Decimal("950.00"))
            .amount_to_settle(Decimal("450.00"))
            .build()
        )


def test_from_model_replaces_the_whole_state() -> None:
    existing = InvoiceSettlement(
        charges=[SettlementCharge(amount=Decimal("20.00"), reason="Old freight")],
        deductions=[SettlementDeduction(amount=Decimal("5.00"), reason="Old discount")],
        amount_due=Decimal("15.00"),
    )

    settlement = started_standard_body().settlement().from_model(existing).build()

    assert settlement == existing


def test_from_model_replaces_previously_built_entries() -> None:
    existing = InvoiceSettlement(
        charges=[SettlementCharge(amount=Decimal("20.00"), reason="Old freight")]
    )

    settlement = (
        started_standard_body()
        .settlement()
        .add_charge(amount=Decimal("99.00"), reason="New freight")
        .from_model(existing)
        .build()
    )

    assert [charge.reason for charge in settlement.charges] == ["Old freight"]


def test_builder_does_not_mutate_the_model_it_was_seeded_from() -> None:
    existing = InvoiceSettlement(
        charges=[SettlementCharge(amount=Decimal("20.00"), reason="Old freight")]
    )

    rebuilt = started_standard_body().settlement().from_model(existing).build()
    _ = (
        started_standard_body()
        .settlement()
        .from_model(existing)
        .clear_charges()
        .add_charge(amount=Decimal("5.00"), reason="Extra")
        .build()
    )

    assert rebuilt == existing
    assert len(existing.charges) == 1


def test_reopening_after_done_replays_the_loaded_totals_and_rejects_new_entries() -> (
    None
):
    """A re-opened settlement carries its computed totals in, so plain ``add_*`` fails.

    Documents current behaviour: the totals the model fills in on ``build()`` come
    back as explicit overrides, so any entry added afterwards contradicts them and
    ``build()`` is rejected. Passing ``None`` clears an override, which is the only
    way to append. Production code is unchanged; see the bug report in the task
    notes.
    """
    body = started_standard_body()
    with_one_line(body)
    _ = body.settlement().add_charge(amount=Decimal("50.00"), reason="Freight").done()

    reopened = body.settlement()
    assert [charge.reason for charge in reopened.build().charges] == ["Freight"]

    with pytest.raises(ValueError, match="charges_total must equal the sum of charges"):
        _ = reopened.add_charge(amount=Decimal("10.00"), reason="More freight").build()

    appended = (
        body.settlement()
        .charges_total(None)
        .add_charge(amount=Decimal("10.00"), reason="More freight")
        .build()
    )

    assert [charge.reason for charge in appended.charges] == [
        "Freight",
        "More freight",
    ]
    assert appended.charges_total == Decimal("60.00")


def test_done_attaches_the_settlement_to_the_body() -> None:
    body = started_standard_body()
    with_one_line(body)

    returned = (
        body.settlement().add_charge(amount=Decimal("50.00"), reason="Freight").done()
    )

    assert returned is body
    assert body.build().settlement is not None
    assert body.build().settlement.charges_total == Decimal("50.00")


def test_done_on_an_empty_settlement_is_rejected() -> None:
    with pytest.raises(ValueError, match="Settlement details are empty"):
        _ = started_standard_body().settlement().done()


def test_done_is_rejected_when_clearing_empties_the_settlement() -> None:
    with pytest.raises(ValueError, match="Settlement details are empty"):
        _ = (
            started_standard_body()
            .settlement()
            .add_charge(amount=Decimal("50.00"), reason="Freight")
            .clear_charges()
            .done()
        )


def test_reopening_the_sub_builder_keeps_the_attached_settlement() -> None:
    body = started_standard_body()
    with_one_line(body)
    _ = body.settlement().add_charge(amount=Decimal("50.00"), reason="Freight").done()

    settlement = body.settlement().build()

    assert [charge.reason for charge in settlement.charges] == ["Freight"]
    assert settlement.deductions == []
    assert settlement.amount_due is None


def test_standalone_builder_can_be_used_without_a_parent() -> None:
    built: list[InvoiceSettlement] = []
    builder: SettlementBuilder[None] = SettlementBuilder(None, built.append)

    returned = builder.add_charge(amount=Decimal("5.00"), reason="Freight").done()

    assert returned is None
    assert [settlement.charges_total for settlement in built] == [Decimal("5.00")]


def test_existing_state_seeds_the_constructor_directly() -> None:
    existing = InvoiceSettlement(
        deductions=[SettlementDeduction(amount=Decimal("3.00"), reason="Prepaid")]
    )

    builder: SettlementBuilder[None] = SettlementBuilder(
        None, lambda _value: None, existing
    )

    assert builder.build() == existing
