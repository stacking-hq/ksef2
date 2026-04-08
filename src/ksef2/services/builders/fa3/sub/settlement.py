from decimal import Decimal
from typing import Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import (
    InvoiceSettlement,
    SettlementCharge,
    SettlementDeduction,
)


class SettlementState(TypedDict):
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
        self._state = adapter.validate_python(settlement.model_dump())
        return self

    def add_charge(self, *, amount: Decimal, reason: str) -> Self:
        self._state["charges"].append(SettlementCharge(amount=amount, reason=reason))
        return self

    def add_charge_model(self, charge: SettlementCharge) -> Self:
        self._state["charges"].append(charge)
        return self

    def clear_charges(self) -> Self:
        self._state["charges"].clear()
        self._state["charges_total"] = None
        return self

    def charges_total(self, amount: Decimal | None) -> Self:
        self._state["charges_total"] = amount
        return self

    def add_deduction(self, *, amount: Decimal, reason: str) -> Self:
        self._state["deductions"].append(
            SettlementDeduction(amount=amount, reason=reason)
        )
        return self

    def add_deduction_model(self, deduction: SettlementDeduction) -> Self:
        self._state["deductions"].append(deduction)
        return self

    def clear_deductions(self) -> Self:
        self._state["deductions"].clear()
        self._state["deductions_total"] = None
        return self

    def deductions_total(self, amount: Decimal | None) -> Self:
        self._state["deductions_total"] = amount
        return self

    def amount_due(self, amount: Decimal | None) -> Self:
        self._state["amount_due"] = amount
        return self

    def amount_to_settle(self, amount: Decimal | None) -> Self:
        self._state["amount_to_settle"] = amount
        return self

    def build(self) -> InvoiceSettlement:
        return InvoiceSettlement(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Settlement details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class SettlementBuilderMixin:
    _settlement: InvoiceSettlement | None = None

    def settlement(self) -> SettlementBuilder[Self]:
        return SettlementBuilder(self, self._set_settlement, self._settlement)

    def _set_settlement(self, value: InvoiceSettlement) -> None:
        if self._settlement is not None:
            raise ValueError("Settlement has already been set")
        self._settlement = value
