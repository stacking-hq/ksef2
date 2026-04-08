from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3 import AdvancePayment, PartialAdvancePayment
from ksef2.domain.models.fa3.body import AdvancePaymentInvoiceContext


def test_partial_advance_payment_accepts_schema_shape() -> None:
    payment = PartialAdvancePayment(
        payment_date=date(2026, 9, 10),
        amount=Decimal("500"),
        currency_exchange_rate=Decimal("4.4512"),
    )

    assert str(payment.payment_date) == "2026-09-10"
    assert str(payment.amount) == "500.00"
    assert str(payment.currency_exchange_rate) == "4.451200"


def test_advance_payment_accepts_outside_ksef_reference() -> None:
    payment = AdvancePayment(
        outside_ksef=True,
        invoice_number="FZ/123/07/2025",
    )

    assert payment.outside_ksef is True
    assert payment.invoice_number == "FZ/123/07/2025"
    assert payment.ksef_id is None


def test_advance_payment_accepts_ksef_reference() -> None:
    payment = AdvancePayment(
        ksef_id="1234567890-20260301-ABCDEF-ABCDEF-FF",
    )

    assert payment.outside_ksef is False
    assert payment.ksef_id == "1234567890-20260301-ABCDEF-ABCDEF-FF"
    assert payment.invoice_number is None


def test_advance_payment_rejects_mixed_reference_modes() -> None:
    with pytest.raises(
        ValidationError,
        match="ksef_id cannot be combined with outside_ksef advance invoice references",
    ):
        AdvancePayment(
            outside_ksef=True,
            invoice_number="FZ/123/07/2025",
            ksef_id="1234567890-20260301-ABCDEF-ABCDEF-FF",
        )

    with pytest.raises(
        ValidationError,
        match="invoice_number cannot be combined with in-KSeF advance invoice references",
    ):
        AdvancePayment(
            invoice_number="FZ/123/07/2025",
            ksef_id="1234567890-20260301-ABCDEF-ABCDEF-FF",
        )


def test_invoice_advance_context_rounds_before_correction_values() -> None:
    context = AdvancePaymentInvoiceContext(
        amount_before_correction=Decimal("1200.456"),
        currency_exchange_rate_before_correction=Decimal("4.4512349"),
    )

    assert str(context.amount_before_correction) == "1200.46"
    assert str(context.currency_exchange_rate_before_correction) == "4.451235"
