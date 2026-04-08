from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3.body.payment import (
    InvoicePayment,
    PartialPayment,
    PaymentTerm,
    PaymentTermDescription,
)


def test_payment_term_requires_date_or_description() -> None:
    with pytest.raises(
        ValidationError,
        match="At least one of due_date or due_date_description must be provided",
    ):
        PaymentTerm()


def test_invoice_payment_accepts_nested_payment_data() -> None:
    payment = InvoicePayment(
        paid=True,
        payment_date=date(2026, 4, 3),
        partial_payments=[
            PartialPayment(
                amount=Decimal("100.00"),
                payment_date=date(2026, 4, 1),
                payment_form="card",
            )
        ],
        payment_terms=[
            PaymentTerm(
                due_date_description=PaymentTermDescription(
                    quantity=7,
                    unit="dni",
                    starting_event="delivery",
                )
            )
        ],
    )

    assert payment.paid is True
    assert payment.partial_payments[0].amount == Decimal("100.00")
    assert payment.payment_terms[0].due_date_description is not None
