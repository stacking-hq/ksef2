from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3 import AdvanceInvoiceReference
from ksef2.domain.models.fa3.body import (
    AdvancePaymentInvoiceContext,
    InvoiceType,
    InvoiceRow,
    InvoiceSettlement,
    KsefInvoiceBody,
    SettlementCharge,
    SettlementDeduction,
    VatRate,
)


def make_invoice_line() -> InvoiceRow:
    return InvoiceRow(
        name="Consulting service",
        quantity=Decimal("1"),
        unit_price_net=Decimal("1000.00"),
        net_amount=Decimal("1000.00"),
        vat_rate=VatRate.VAT_23,
        vat_amount=Decimal("230.00"),
    )


def test_invoice_settlement_populates_totals_from_entries() -> None:
    settlement = InvoiceSettlement(
        charges=[SettlementCharge(amount=Decimal("17.00"), reason="Oplata skarbowa")],
        deductions=[
            SettlementDeduction(amount=Decimal("100.00"), reason="Rabat rozliczeniowy")
        ],
    )

    assert settlement.charges_total == Decimal("17.00")
    assert settlement.deductions_total == Decimal("100.00")


def test_invoice_settlement_rejects_conflicting_balance_fields() -> None:
    with pytest.raises(
        ValidationError,
        match="amount_due and amount_to_settle cannot be provided together",
    ):
        InvoiceSettlement(
            amount_due=Decimal("10.00"),
            amount_to_settle=Decimal("5.00"),
        )


def test_invoice_body_combines_settlement_and_advance_reference_deductions() -> None:
    body = KsefInvoiceBody(
        issue_date=date(2026, 3, 29),
        issue_place=None,
        invoice_number="FR/1/2026",
        invoice_type=InvoiceType.ROZ,
        rows=[make_invoice_line()],
        settlement=InvoiceSettlement(
            charges=[
                SettlementCharge(amount=Decimal("17.00"), reason="Oplata skarbowa")
            ],
            deductions=[
                SettlementDeduction(
                    amount=Decimal("30.00"),
                    reason="Potracenie administracyjne",
                )
            ],
        ),
        advance=AdvancePaymentInvoiceContext(
            advance_invoice_references=[
                AdvanceInvoiceReference(
                    ksef_id="1234567890-20260301-ABCDEF-ABCDEF-FF",
                    deduction_amount=Decimal("500.00"),
                    deduction_reason="Rozliczenie faktury zaliczkowej nr 1",
                )
            ]
        ),
    )

    assert body.settlement_charges_total == Decimal("17.00")
    assert body.settlement_deductions_total == Decimal("530.00")
    assert body.settlement_balance == Decimal("717.00")
