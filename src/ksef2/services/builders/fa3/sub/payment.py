from datetime import date
from decimal import Decimal
from typing import Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3.body import (
    BankAccount,
    BankOwnAccountType,
    InvoicePayment,
    PartialPayment,
    PartialPaymentStatus,
    PaymentForm,
    PaymentTerm,
    PaymentTermDescription,
)


class InvoicePaymentState(TypedDict):
    paid: bool
    payment_date: date | None
    partial_payment_status: PartialPaymentStatus | None
    partial_payments: list[PartialPayment]
    payment_terms: list[PaymentTerm]
    payment_form: PaymentForm | None
    other_payment_form: bool
    payment_description: str | None
    bank_accounts: list[BankAccount]
    factor_bank_accounts: list[BankAccount]
    discount_terms: str | None
    discount_amount: str | None
    payment_link: str | None
    ipksef: str | None


adapter = TypeAdapter(InvoicePaymentState)


def _default_state() -> InvoicePaymentState:
    return {
        "paid": False,
        "payment_date": None,
        "partial_payment_status": None,
        "partial_payments": [],
        "payment_terms": [],
        "payment_form": None,
        "other_payment_form": False,
        "payment_description": None,
        "bank_accounts": [],
        "factor_bank_accounts": [],
        "discount_terms": None,
        "discount_amount": None,
        "payment_link": None,
        "ipksef": None,
    }


class PaymentBuilder[TParent]:
    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[InvoicePayment], None],
        existing_state: InvoicePayment | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._state: InvoicePaymentState = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, payment: InvoicePayment) -> Self:
        self._state = adapter.validate_python(payment.model_dump())
        return self

    def via(self, payment_form: PaymentForm | None) -> Self:
        self._state["payment_form"] = payment_form
        return self

    def already_paid(self, payment_date: date | None = None) -> Self:
        self._state["paid"] = True
        self._state["payment_date"] = payment_date
        return self

    def unpaid(self) -> Self:
        self._state["paid"] = False
        self._state["payment_date"] = None
        return self

    def payment_date(self, payment_date: date | None) -> Self:
        self._state["payment_date"] = payment_date
        return self

    def partial_payment_status(self, status: PartialPaymentStatus | None) -> Self:
        self._state["partial_payment_status"] = status
        return self

    def other_form(self, enabled: bool = True) -> Self:
        self._state["other_payment_form"] = enabled
        return self

    def description(self, description: str | None) -> Self:
        self._state["payment_description"] = description
        return self

    def _add_term(
        self,
        *,
        due_on: date | None = None,
        description: PaymentTermDescription | None = None,
    ) -> Self:
        self._state["payment_terms"].append(
            PaymentTerm(due_date=due_on, due_date_description=description)
        )
        return self

    def due_on(self, due_date: date) -> Self:
        return self._add_term(due_on=due_date)

    def due_with_description(
        self,
        *,
        quantity: int,
        unit: str,
        starting_event: str,
        due_date: date | None = None,
    ) -> Self:
        return self._add_term(
            due_on=due_date,
            description=PaymentTermDescription(
                quantity=quantity,
                unit=unit,
                starting_event=starting_event,
            ),
        )

    def add_term_model(self, term: PaymentTerm) -> Self:
        self._state["payment_terms"].append(term)
        return self

    def clear_terms(self) -> Self:
        self._state["payment_terms"].clear()
        return self

    def add_partial_payment(
        self,
        *,
        amount: Decimal,
        payment_date: date,
        payment_form: PaymentForm | None = None,
        other_payment_form: bool = False,
        payment_description: str | None = None,
    ) -> Self:
        self._state["partial_payments"].append(
            PartialPayment(
                amount=amount,
                payment_date=payment_date,
                payment_form=payment_form,
                other_payment_form=other_payment_form,
                payment_description=payment_description,
            )
        )
        return self

    def add_partial_payment_model(self, partial_payment: PartialPayment) -> Self:
        self._state["partial_payments"].append(partial_payment)
        return self

    def clear_partial_payments(self) -> Self:
        self._state["partial_payments"].clear()
        return self

    def _append_bank_account(
        self,
        target: list[BankAccount],
        account_number: str,
        swift: str | None = None,
        *,
        bank_name: str | None = None,
        account_description: str | None = None,
        own_bank_account_type: BankOwnAccountType | None = None,
    ) -> None:
        target.append(
            BankAccount(
                account_number=account_number,
                swift=swift,
                own_bank_account_type=own_bank_account_type,
                bank_name=bank_name,
                account_description=account_description,
            )
        )

    def bank_account(
        self,
        account_number: str,
        swift: str | None = None,
        *,
        bank_name: str | None = None,
        account_description: str | None = None,
        own_bank_account_type: BankOwnAccountType | None = None,
    ) -> Self:
        self._append_bank_account(
            self._state["bank_accounts"],
            account_number,
            swift,
            bank_name=bank_name,
            account_description=account_description,
            own_bank_account_type=own_bank_account_type,
        )
        return self

    def add_bank_account_model(self, account: BankAccount) -> Self:
        self._state["bank_accounts"].append(account)
        return self

    def clear_bank_accounts(self) -> Self:
        self._state["bank_accounts"].clear()
        return self

    def factor_bank_account(
        self,
        account_number: str,
        swift: str | None = None,
        *,
        bank_name: str | None = None,
        account_description: str | None = None,
        own_bank_account_type: BankOwnAccountType | None = None,
    ) -> Self:
        self._append_bank_account(
            self._state["factor_bank_accounts"],
            account_number,
            swift,
            bank_name=bank_name,
            account_description=account_description,
            own_bank_account_type=own_bank_account_type,
        )
        return self

    def add_factor_bank_account_model(self, account: BankAccount) -> Self:
        self._state["factor_bank_accounts"].append(account)
        return self

    def clear_factor_bank_accounts(self) -> Self:
        self._state["factor_bank_accounts"].clear()
        return self

    def discount(self, *, terms: str | None = None, amount: str | None = None) -> Self:
        self._state["discount_terms"] = terms
        self._state["discount_amount"] = amount
        return self

    def skonto(self, *, terms: str | None = None, amount: str | None = None) -> Self:
        return self.discount(terms=terms, amount=amount)

    def payment_link(self, link: str | None) -> Self:
        self._state["payment_link"] = link
        return self

    def ipksef(self, value: str | None) -> Self:
        self._state["ipksef"] = value
        return self

    def build(self) -> InvoicePayment:
        self._validate_state()
        return InvoicePayment(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Payment details are empty. Set at least one field before calling done()."
            )

        self._on_done(self.build())
        return self._parent

    def _validate_state(self) -> None:

        if not self._state["paid"]:
            self._state["payment_date"] = None

        if self._state["other_payment_form"] and not self._state["payment_description"]:
            raise ValueError(
                "payment_description is required when other_payment_form is enabled"
            )


class PaymentBuilderMixin:
    _payment: InvoicePayment | None = None

    def payment(self) -> PaymentBuilder[Self]:
        return PaymentBuilder(self, self._set_payment, self._payment)

    def _set_payment(self, value: InvoicePayment) -> None:
        self._payment = value
