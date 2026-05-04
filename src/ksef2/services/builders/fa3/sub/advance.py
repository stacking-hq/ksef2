from datetime import date
from decimal import Decimal
from typing import Annotated, Self, TypedDict
from collections.abc import Callable

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import (
    AdvanceInvoiceReference,
    AdvancePaymentInvoiceContext,
    PartialAdvancePayment,
)
from ksef2.services.builders.fa3.metadata import builder_param


class AdvanceState(TypedDict):
    amount_before_correction: Decimal | None
    currency_exchange_rate_before_correction: Decimal | None
    advance_partial_payments: list[PartialAdvancePayment]
    advance_invoice_references: list[AdvanceInvoiceReference]


adapter = TypeAdapter(AdvanceState)


def _default_state() -> AdvanceState:
    return {
        "amount_before_correction": None,
        "currency_exchange_rate_before_correction": None,
        "advance_partial_payments": [],
        "advance_invoice_references": [],
    }


class AdvanceBuilder[TParent]:
    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[AdvancePaymentInvoiceContext], None],
        existing_state: AdvancePaymentInvoiceContext | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._state: AdvanceState = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, advance: AdvancePaymentInvoiceContext) -> Self:
        self._state = adapter.validate_python(advance.model_dump())
        return self

    def amount_before_correction(
        self,
        amount: Annotated[
            Decimal | None,
            builder_param(
                "Advance amount before the correction was applied.",
                examples=["1500.45"],
                format="decimal-string",
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["amount_before_correction"] = amount
        return self

    def currency_exchange_rate_before_correction(
        self,
        exchange_rate: Annotated[
            Decimal | None,
            builder_param(
                "Currency exchange rate used before the correction was applied.",
                examples=["4.4512"],
                format="decimal-string",
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["currency_exchange_rate_before_correction"] = exchange_rate
        return self

    def add_partial_payment(
        self,
        *,
        payment_date: Annotated[
            date,
            builder_param(
                "Date of the partial advance payment.",
                examples=["2026-04-05"],
                format="date",
            ),
        ],
        amount: Annotated[
            Decimal,
            builder_param(
                "Amount of the partial advance payment.",
                examples=["500.00"],
                format="decimal-string",
            ),
        ],
        currency_exchange_rate: Annotated[
            Decimal | None,
            builder_param(
                "Currency exchange rate used for the partial advance payment.",
                examples=["4.4512"],
                format="decimal-string",
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        self._state["advance_partial_payments"].append(
            PartialAdvancePayment(
                payment_date=payment_date,
                amount=amount,
                currency_exchange_rate=currency_exchange_rate,
            )
        )
        return self

    def add_partial_payment_model(self, partial_payment: PartialAdvancePayment) -> Self:
        self._state["advance_partial_payments"].append(partial_payment)
        return self

    def clear_partial_payments(self) -> Self:
        self._state["advance_partial_payments"].clear()
        return self

    def add_invoice_reference(
        self,
        *,
        ksef_id: Annotated[
            str | None,
            builder_param(
                "KSeF identifier of the referenced advance invoice.",
                examples=["20260405-1234567890-ABCDEF1234567890"],
                priority="advanced",
            ),
        ] = None,
        invoice_number: Annotated[
            str | None,
            builder_param(
                "Invoice number of the referenced advance invoice.",
                examples=["ZAL/2026/04/001"],
            ),
        ] = None,
        outside_ksef: Annotated[
            bool,
            builder_param(
                "Set to true when the referenced advance invoice was issued outside KSeF.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        deduction_amount: Annotated[
            Decimal | None,
            builder_param(
                "Amount deducted from the final settlement based on this advance invoice.",
                examples=["500.00"],
                format="decimal-string",
                priority="advanced",
            ),
        ] = None,
        deduction_reason: Annotated[
            str | None,
            builder_param(
                "Reason for the deduction linked to the advance invoice reference.",
                examples=["Advance already settled"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        self._state["advance_invoice_references"].append(
            AdvanceInvoiceReference(
                ksef_id=ksef_id,
                invoice_number=invoice_number,
                outside_ksef=outside_ksef,
                deduction_amount=deduction_amount,
                deduction_reason=deduction_reason,
            )
        )
        return self

    def add_invoice_reference_model(
        self, invoice_reference: AdvanceInvoiceReference
    ) -> Self:
        self._state["advance_invoice_references"].append(invoice_reference)
        return self

    def clear_invoice_references(self) -> Self:
        self._state["advance_invoice_references"].clear()
        return self

    def build(self) -> AdvancePaymentInvoiceContext:
        return AdvancePaymentInvoiceContext(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Advance details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class AdvanceBuilderMixin:
    _advance: AdvancePaymentInvoiceContext | None = None

    def advance(self) -> AdvanceBuilder[Self]:
        return AdvanceBuilder(self, self._set_advance, self._advance)

    def _set_advance(self, value: AdvancePaymentInvoiceContext) -> None:
        self._advance = value
