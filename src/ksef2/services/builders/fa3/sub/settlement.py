"""Fluent builder for FA(3) settlement blocks."""

from decimal import Decimal
from typing import Annotated, Self, TypedDict
from collections.abc import Callable

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import (
    InvoiceSettlement,
    SettlementCharge,
    SettlementDeduction,
)
from ksef2.services.builders.fa3.metadata import builder_param


class SettlementState(TypedDict):
    """Typed state for Settlement fields."""

    charges: list[SettlementCharge]
    charges_total: Decimal | None
    deductions: list[SettlementDeduction]
    deductions_total: Decimal | None
    amount_due: Decimal | None
    amount_to_settle: Decimal | None


adapter = TypeAdapter(SettlementState)


def _default_state() -> SettlementState:
    return {
        "charges": [],
        "charges_total": None,
        "deductions": [],
        "deductions_total": None,
        "amount_due": None,
        "amount_to_settle": None,
    }


class SettlementBuilder[TParent]:
    """Fluent builder for FA(3) settlement details."""

    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[InvoiceSettlement], None],
        existing_state: InvoiceSettlement | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._state: SettlementState = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, settlement: InvoiceSettlement) -> Self:
        """Replace the builder state from an existing domain model."""
        self._state = adapter.validate_python(settlement.model_dump())
        return self

    def add_charge(
        self,
        *,
        amount: Annotated[
            Decimal,
            builder_param(
                "Additional charge amount included in the settlement.",
                examples=["50.00"],
                format="decimal-string",
            ),
        ],
        reason: Annotated[
            str,
            builder_param(
                "Reason for the settlement charge.",
                examples=["Delivery surcharge"],
            ),
        ],
    ) -> Self:
        """Add a charge entry."""
        self._state["charges"].append(SettlementCharge(amount=amount, reason=reason))
        return self

    def add_charge_model(self, charge: SettlementCharge) -> Self:
        """Add an existing settlement charge model."""
        self._state["charges"].append(charge)
        return self

    def clear_charges(self) -> Self:
        """Remove all settlement charges."""
        self._state["charges"].clear()
        self._state["charges_total"] = None
        return self

    def charges_total(
        self,
        amount: Annotated[
            Decimal | None,
            builder_param(
                "Explicit total of settlement charges when it should be preserved instead of recomputed.",
                examples=["50.00"],
                format="decimal-string",
                priority="override",
            ),
        ],
    ) -> Self:
        """Set the charges total value."""
        self._state["charges_total"] = amount
        return self

    def add_deduction(
        self,
        *,
        amount: Annotated[
            Decimal,
            builder_param(
                "Deduction amount included in the settlement.",
                examples=["100.00"],
                format="decimal-string",
            ),
        ],
        reason: Annotated[
            str,
            builder_param(
                "Reason for the settlement deduction.",
                examples=["Advance paid earlier"],
            ),
        ],
    ) -> Self:
        """Add a deduction entry."""
        self._state["deductions"].append(
            SettlementDeduction(amount=amount, reason=reason)
        )
        return self

    def add_deduction_model(self, deduction: SettlementDeduction) -> Self:
        """Add an existing settlement deduction model."""
        self._state["deductions"].append(deduction)
        return self

    def clear_deductions(self) -> Self:
        """Remove all settlement deductions."""
        self._state["deductions"].clear()
        self._state["deductions_total"] = None
        return self

    def deductions_total(
        self,
        amount: Annotated[
            Decimal | None,
            builder_param(
                "Explicit total of settlement deductions when it should be preserved instead of recomputed.",
                examples=["100.00"],
                format="decimal-string",
                priority="override",
            ),
        ],
    ) -> Self:
        """Set the deductions total value."""
        self._state["deductions_total"] = amount
        return self

    def amount_due(
        self,
        amount: Annotated[
            Decimal | None,
            builder_param(
                "Amount due after charges and deductions are applied.",
                examples=["950.00"],
                format="decimal-string",
                priority="override",
            ),
        ],
    ) -> Self:
        """Set the amount due value."""
        self._state["amount_due"] = amount
        return self

    def amount_to_settle(
        self,
        amount: Annotated[
            Decimal | None,
            builder_param(
                "Remaining amount to settle after taking the settlement context into account.",
                examples=["450.00"],
                format="decimal-string",
                priority="override",
            ),
        ],
    ) -> Self:
        """Set the amount to settle value."""
        self._state["amount_to_settle"] = amount
        return self

    def build(self) -> InvoiceSettlement:
        """Build the corresponding FA(3) domain model."""
        return InvoiceSettlement(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        """Attach the built settlement details to the parent builder and return it.

        Raises:
            ValueError: If settlement details are empty.
        """
        if self._is_empty():
            raise ValueError(
                "Settlement details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class SettlementBuilderMixin:
    """Mixin exposing the Settlement sub-builder."""

    _settlement: InvoiceSettlement | None = None

    def settlement(self) -> SettlementBuilder[Self]:
        """Start a settlement invoice body builder or sub-builder."""
        return SettlementBuilder(self, self._set_settlement, self._settlement)

    def _set_settlement(self, value: InvoiceSettlement) -> None:
        self._settlement = value
