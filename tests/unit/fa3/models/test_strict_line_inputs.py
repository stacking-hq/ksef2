"""Opt-in strict line construction preserves the mutable 1.x defaults."""

from decimal import Decimal

import pytest
from pydantic import ConfigDict

from ksef2 import KSeFValidationError
from ksef2.fa3 import InvoiceOrderLine, InvoiceRow, VatRate


class StrictInvoiceRow(InvoiceRow):
    model_config = ConfigDict(extra="forbid")


class StrictOrderLine(InvoiceOrderLine):
    model_config = ConfigDict(extra="forbid")


@pytest.mark.parametrize("model", [StrictInvoiceRow, StrictOrderLine])
def test_strict_line_rejects_unknown_fields(
    model: type[InvoiceRow | InvoiceOrderLine],
) -> None:
    with pytest.raises(KSeFValidationError, match="net_ammount"):
        model.model_validate(
            {
                "name": "X",
                "gross_amount": Decimal("123"),
                "vat_rate": VatRate.VAT_23,
                "net_ammount": Decimal("100"),
            }
        )


def test_reconstruct_row_from_source_recalculates_amounts() -> None:
    source = dict(
        name="Service",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        vat_rate=VatRate.VAT_23,
    )
    original = StrictInvoiceRow.model_validate(source)
    source["quantity"] = Decimal("3")
    updated = StrictInvoiceRow.model_validate(source)
    assert original.gross_amount == Decimal("123.00")
    assert updated.net_amount == Decimal("300.00")
    assert updated.vat_amount == Decimal("69.00")
    assert updated.gross_amount == Decimal("369.00")


def test_reconstruct_order_line_from_source_recalculates_amounts() -> None:
    source = dict(name="Service", gross_amount=Decimal("123"), vat_rate=VatRate.VAT_23)
    original = StrictOrderLine.model_validate(source)
    source["gross_amount"] = Decimal("369")
    updated = StrictOrderLine.model_validate(source)
    assert original.net_amount == Decimal("100.00")
    assert updated.net_amount == Decimal("300.00")
    assert updated.vat_amount == Decimal("69.00")
