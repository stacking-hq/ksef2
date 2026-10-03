"""Fluent builder for FA(3) payment blocks."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Self, TypedDict
from collections.abc import Callable

from pydantic import TypeAdapter

from ksef2._domain.models.fa3.body import (
    BankAccount,
    BankOwnAccountType,
    InvoicePayment,
    PartialPayment,
    PartialPaymentStatus,
    PaymentForm,
    PaymentTerm,
    PaymentTermDescription,
)
from ksef2._services.builders.fa3.metadata import builder_param


class InvoicePaymentState(TypedDict):
    """Typed state for FA(3) payment fields."""

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

PaymentDateParam = Annotated[
    date | None,
    builder_param(
        "Payment date linked to the invoice or a partial payment entry.",
        examples=["2026-04-15"],
        format="date",
    ),
]
PaymentFormParam = Annotated[
    PaymentForm | None,
    builder_param(
        "Payment form used for the invoice or the partial payment entry.",
        examples=["bank_transfer", "cash"],
        format="enum-string",
    ),
]
PartialPaymentStatusParam = Annotated[
    PartialPaymentStatus | None,
    builder_param(
        "Partial payment status recorded on the invoice.",
        examples=["partial", "final"],
        format="enum-string",
        priority="advanced",
    ),
]
PaymentDescriptionParam = Annotated[
    str | None,
    builder_param(
        "Free-text payment description shown with the payment details.",
        examples=["Card payment at delivery"],
        priority="advanced",
    ),
]
PaymentAmountParam = Annotated[
    Decimal,
    builder_param(
        "Monetary amount used for payment entries.",
        examples=["500.00"],
        format="decimal-string",
    ),
]
BankAccountNumberParam = Annotated[
    str,
    builder_param(
        "Bank account number used for invoice payment.",
        examples=["98102055580000123456789012"],
    ),
]


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
    """Fluent builder for FA(3) payment details."""

    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[InvoicePayment], None],
        existing_state: InvoicePayment | None = None,
    ) -> None:
        """Create the builder.

        Args:
            parent: Parent builder that ``done()`` returns to.
            on_done: Callback that receives the built model when ``done()`` is called.
            existing_state: Existing model to start from; ``None`` starts empty.
        """
        self._parent = parent
        self._on_done = on_done
        self._state: InvoicePaymentState = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, payment: InvoicePayment) -> Self:
        """Replace the builder state from an existing domain model.

        Args:
            payment: Model to load into the builder.

        Returns:
            The builder, for chaining.
        """
        self._state = adapter.validate_python(payment.model_dump())
        return self

    def via(self, payment_form: PaymentFormParam) -> Self:
        """Set the invoice payment form.

        Args:
            payment_form: Payment form used for the invoice or the partial payment entry.

        Returns:
            The builder, for chaining.
        """
        self._state["payment_form"] = payment_form
        return self

    def already_paid(self, payment_date: PaymentDateParam = None) -> Self:
        """Mark the invoice as paid, optionally with a payment date.

        Args:
            payment_date: Payment date linked to the invoice or a partial payment entry.

        Returns:
            The builder, for chaining.
        """
        self._state["paid"] = True
        self._state["payment_date"] = payment_date
        return self

    def unpaid(self) -> Self:
        """Mark the invoice as unpaid and clear the payment date.

        Returns:
            The builder, for chaining.
        """
        self._state["paid"] = False
        self._state["payment_date"] = None
        return self

    def payment_date(self, payment_date: PaymentDateParam) -> Self:
        """Set the payment date value.

        Args:
            payment_date: Payment date linked to the invoice or a partial payment entry.

        Returns:
            The builder, for chaining.
        """
        self._state["payment_date"] = payment_date
        return self

    def partial_payment_status(self, status: PartialPaymentStatusParam) -> Self:
        """Set the partial payment status value.

        Args:
            status: Partial payment status recorded on the invoice.

        Returns:
            The builder, for chaining.
        """
        self._state["partial_payment_status"] = status
        return self

    def other_form(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the payment form as a custom form outside the standard enum.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        """Mark the payment form as a custom non-enum value.

        Args:
            enabled: Marks the payment form as a custom form outside the standard enum.

        Returns:
            The builder, for chaining.
        """
        self._state["other_payment_form"] = enabled
        return self

    def description(self, description: PaymentDescriptionParam) -> Self:
        """Set the description value.

        Args:
            description: Free-text payment description shown with the payment details.

        Returns:
            The builder, for chaining.
        """
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

    def due_on(
        self,
        due_date: Annotated[
            date,
            builder_param(
                "Invoice payment due date.",
                examples=["2026-04-30"],
                format="date",
            ),
        ],
    ) -> Self:
        """Add a payment term with a concrete due date.

        Args:
            due_date: Invoice payment due date.

        Returns:
            The builder, for chaining.
        """
        return self._add_term(due_on=due_date)

    def due_with_description(
        self,
        *,
        quantity: Annotated[
            int,
            builder_param(
                "Quantity used in the textual payment deadline description.",
                examples=[14],
                priority="advanced",
            ),
        ],
        unit: Annotated[
            str,
            builder_param(
                "Unit used in the textual payment deadline description.",
                examples=["days", "months"],
                priority="advanced",
            ),
        ],
        starting_event: Annotated[
            str,
            builder_param(
                "Event from which the payment deadline is counted.",
                examples=["from invoice issue date", "from delivery"],
                priority="advanced",
            ),
        ],
        due_date: PaymentDateParam = None,
    ) -> Self:
        """Add a payment term described by duration and starting event.

        Args:
            quantity: Quantity used in the textual payment deadline description.
            unit: Unit used in the textual payment deadline description.
            starting_event: Event from which the payment deadline is counted.
            due_date: Payment date linked to the invoice or a partial payment entry.

        Returns:
            The builder, for chaining.
        """
        return self._add_term(
            due_on=due_date,
            description=PaymentTermDescription(
                quantity=quantity,
                unit=unit,
                starting_event=starting_event,
            ),
        )

    def add_term_model(self, term: PaymentTerm) -> Self:
        """Add an existing payment-term domain model.

        Args:
            term: Model to add.

        Returns:
            The builder, for chaining.
        """
        self._state["payment_terms"].append(term)
        return self

    def clear_terms(self) -> Self:
        """Remove all payment terms.

        Returns:
            The builder, for chaining.
        """
        self._state["payment_terms"].clear()
        return self

    def add_partial_payment(
        self,
        *,
        amount: PaymentAmountParam,
        payment_date: Annotated[
            date,
            builder_param(
                "Date of the partial payment.",
                examples=["2026-04-10"],
                format="date",
            ),
        ],
        payment_form: PaymentFormParam = None,
        other_payment_form: Annotated[
            bool,
            builder_param(
                "Set to true when the partial payment uses a non-standard payment form.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        payment_description: PaymentDescriptionParam = None,
    ) -> Self:
        """Add a partial payment entry.

        Args:
            amount: Monetary amount used for payment entries.
            payment_date: Date of the partial payment.
            payment_form: Payment form used for the invoice or the partial payment entry.
            other_payment_form: Set to true when the partial payment uses a non-standard payment form.
            payment_description: Free-text payment description shown with the payment details.

        Returns:
            The builder, for chaining.
        """
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
        """Add an existing partial-payment domain model.

        Args:
            partial_payment: Model to add.

        Returns:
            The builder, for chaining.
        """
        self._state["partial_payments"].append(partial_payment)
        return self

    def clear_partial_payments(self) -> Self:
        """Remove all partial-payment entries.

        Returns:
            The builder, for chaining.
        """
        self._state["partial_payments"].clear()
        return self

    def _append_bank_account(
        self,
        target: list[BankAccount],
        account_number: BankAccountNumberParam,
        swift: Annotated[
            str | None,
            builder_param(
                "SWIFT or BIC code for the bank account.",
                examples=["BREXPLPW"],
                priority="advanced",
            ),
        ] = None,
        *,
        bank_name: Annotated[
            str | None,
            builder_param(
                "Name of the bank for the account.",
                examples=["PKO Bank Polski"],
                priority="advanced",
            ),
        ] = None,
        account_description: Annotated[
            str | None,
            builder_param(
                "Description shown next to the bank account.",
                examples=["Main settlement account"],
                priority="advanced",
            ),
        ] = None,
        own_bank_account_type: Annotated[
            BankOwnAccountType | None,
            builder_param(
                "Own-account marker used by FA(3) for the bank account entry.",
                examples=["purchased_receivables"],
                format="enum-string",
                priority="advanced",
            ),
        ] = None,
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
        account_number: BankAccountNumberParam,
        swift: Annotated[
            str | None,
            builder_param(
                "SWIFT or BIC code for the factor bank account.",
                examples=["BREXPLPW"],
                priority="advanced",
            ),
        ] = None,
        *,
        bank_name: Annotated[
            str | None,
            builder_param(
                "Name of the bank operating the factor account.",
                examples=["Bank Pekao"],
                priority="advanced",
            ),
        ] = None,
        account_description: Annotated[
            str | None,
            builder_param(
                "Description shown next to the factor bank account.",
                examples=["Factoring account"],
                priority="advanced",
            ),
        ] = None,
        own_bank_account_type: Annotated[
            BankOwnAccountType | None,
            builder_param(
                "Own-account marker used by FA(3) for the factor bank account entry.",
                examples=["factor_collection"],
                format="enum-string",
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        """Add a bank account for invoice payment.

        Args:
            account_number: Bank account number used for invoice payment.
            swift: SWIFT or BIC code for the factor bank account.
            bank_name: Name of the bank operating the factor account.
            account_description: Description shown next to the factor bank account.
            own_bank_account_type: Own-account marker used by FA(3) for the factor bank account entry.

        Returns:
            The builder, for chaining.
        """
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
        """Add an existing bank-account domain model.

        Args:
            account: Model to add.

        Returns:
            The builder, for chaining.
        """
        self._state["bank_accounts"].append(account)
        return self

    def clear_bank_accounts(self) -> Self:
        """Remove all bank accounts.

        Returns:
            The builder, for chaining.
        """
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
        """Add a factoring bank account for invoice payment.

        Args:
            account_number: Bank account number.
            swift: SWIFT/BIC code of the bank.
            bank_name: Name of the bank.
            account_description: Free-text description of the account.
            own_bank_account_type: Kind of own bank account of the bank.

        Returns:
            The builder, for chaining.
        """
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
        """Add an existing factoring bank-account domain model.

        Args:
            account: Model to add.

        Returns:
            The builder, for chaining.
        """
        self._state["factor_bank_accounts"].append(account)
        return self

    def clear_factor_bank_accounts(self) -> Self:
        """Remove all factoring bank accounts.

        Returns:
            The builder, for chaining.
        """
        self._state["factor_bank_accounts"].clear()
        return self

    def discount(
        self,
        *,
        terms: Annotated[
            str | None,
            builder_param(
                "Description of discount terms attached to the payment.",
                examples=["2% within 7 days"],
                priority="advanced",
            ),
        ] = None,
        amount: Annotated[
            str | None,
            builder_param(
                "Discount amount or value description stored with the payment terms.",
                examples=["20.00"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        """Set discount terms and amount for payment details.

        Args:
            terms: Description of discount terms attached to the payment.
            amount: Discount amount or value description stored with the payment terms.

        Returns:
            The builder, for chaining.
        """
        self._state["discount_terms"] = terms
        self._state["discount_amount"] = amount
        return self

    def skonto(
        self,
        *,
        terms: Annotated[
            str | None,
            builder_param(
                "Description of skonto terms attached to the payment.",
                examples=["2% within 7 days"],
                priority="advanced",
            ),
        ] = None,
        amount: Annotated[
            str | None,
            builder_param(
                "Skonto amount or value description stored with the payment terms.",
                examples=["20.00"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        """Set skonto terms and amount for payment details.

        Args:
            terms: Description of skonto terms attached to the payment.
            amount: Skonto amount or value description stored with the payment terms.

        Returns:
            The builder, for chaining.
        """
        return self.discount(terms=terms, amount=amount)

    def payment_link(
        self,
        link: Annotated[
            str | None,
            builder_param(
                "Link leading to an online payment page for the invoice.",
                examples=["https://payments.example.com/invoice/123"],
                priority="advanced",
            ),
        ],
    ) -> Self:
        """Set the payment link value.

        Args:
            link: Link leading to an online payment page for the invoice.

        Returns:
            The builder, for chaining.
        """
        self._state["payment_link"] = link
        return self

    def ipksef(
        self,
        value: Annotated[
            str | None,
            builder_param(
                "IPKSeF payment identifier linked to the invoice.",
                examples=["IPKSEF-123456789"],
                priority="advanced",
            ),
        ],
    ) -> Self:
        """Set the IP KSeF payment marker value.

        Args:
            value: IPKSeF payment identifier linked to the invoice.

        Returns:
            The builder, for chaining.
        """
        self._state["ipksef"] = value
        return self

    def build(self) -> InvoicePayment:
        """Build the corresponding FA(3) domain model.

        Returns:
            The built ``InvoicePayment``.

        Raises:
            ValueError: If a custom payment form is enabled without a description.
        """
        self._validate_state()
        return InvoicePayment(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        """Attach the built payment details to the parent builder and return it.

        Returns:
            The parent builder.

        Raises:
            ValueError: If payment details are empty, or a custom payment form has
                no description.
        """
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
    """Mixin exposing the Payment sub-builder."""

    _payment: InvoicePayment | None = None

    def payment(self) -> PaymentBuilder[Self]:
        """Start a payment sub-builder.

        Returns:
            A ``PaymentBuilder`` for this part of the invoice; call ``done()`` on it to attach the result and return to this builder.
        """
        return PaymentBuilder(self, self._set_payment, self._payment)

    def _set_payment(self, value: InvoicePayment) -> None:
        self._payment = value
