from decimal import Decimal

import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3.body import InvoiceOrder, InvoiceOrderLine, VatRate


def test_invoice_order_populates_total_value_from_order_lines() -> None:
    order = InvoiceOrder(
        order_lines=[
            InvoiceOrderLine(
                name="Projekt",
                gross_amount=Decimal("1230.00"),
                vat_rate=VatRate.VAT_23,
            )
        ]
    )

    assert order.total_value == Decimal("1230.00")


def test_invoice_order_rejects_total_value_mismatch() -> None:
    with pytest.raises(
        ValidationError,
        match="gross amount must equal the sum of order line gross amounts",
    ):
        InvoiceOrder(
            total_value=Decimal("999.00"),
            order_lines=[
                InvoiceOrderLine(
                    name="Projekt",
                    gross_amount=Decimal("1230.00"),
                    vat_rate=VatRate.VAT_23,
                )
            ],
        )
