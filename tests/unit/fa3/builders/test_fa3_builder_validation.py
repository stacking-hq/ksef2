"""Public builder regressions for SDK errors, decimal inputs and guide XML."""

from datetime import date
from decimal import Decimal
from pathlib import Path
import re
from typing import Any

import pytest
from pydantic import ValidationError

from ksef2 import KSeFException, KSeFValidationError
from ksef2.fa3 import InvoiceBuilder


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", Decimal("NaN")),
        ("unit_price_net", Decimal("NaN")),
        ("unit_price_net", Decimal("Infinity")),
        ("unit_price_net", Decimal("-Infinity")),
        ("unit_price_net", "not a number"),
        ("name", "Invalid\x00name"),
        ("name", "Invalid\x1fname"),
        ("name", "Invalid\ud800name"),
        ("unit_of_measure", "Invalid\x00unit"),
    ],
)
def test_invalid_row_fields_raise_sdk_validation_error(
    field: str, value: object
) -> None:
    values: dict[str, Any] = dict(
        name="Service", quantity=1, unit_price_net=100, vat_rate="23"
    )
    values[field] = value
    with pytest.raises(KSeFValidationError, match=field) as caught:
        InvoiceBuilder().standard().rows().add_line(**values)

    assert isinstance(caught.value, KSeFException)
    assert isinstance(caught.value, ValueError)
    assert isinstance(caught.value.__cause__, ValidationError)
    assert caught.value.validation_error is caught.value.__cause__
    assert "InvoiceRow" not in str(caught.value)


@pytest.mark.parametrize("invoice_number", ["", " ", "X" * 257, "FV\x00/1"])
def test_invalid_invoice_number_raises_sdk_error_at_build(invoice_number: str) -> None:
    body = InvoiceBuilder().standard().invoice_number(invoice_number)
    with pytest.raises(KSeFValidationError, match="invoice_number") as caught:
        body.build()
    assert isinstance(caught.value.__cause__, ValidationError)
    assert "KsefInvoiceBody" not in str(caught.value)


@pytest.mark.parametrize("finish", ["build", "done"])
def test_partial_payment_requires_explicit_status(finish: str) -> None:
    payment = (
        InvoiceBuilder()
        .standard()
        .payment()
        .add_partial_payment(
            amount=50.0, payment_date=date(2026, 6, 24), payment_form="card"
        )
    )
    with pytest.raises(
        KSeFValidationError,
        match=r'partial_payment_status\("partial"\).*partial_payment_status\("final"\)',
    ):
        getattr(payment, finish)()


@pytest.mark.parametrize("lang", ["en", "pl"])
def test_payment_guide_example_validates_against_xsd(lang: str) -> None:
    guide = (
        Path(__file__).resolve().parents[4]
        / "docs"
        / lang
        / "how-to-guides"
        / "build-fa3-invoices.md"
    )
    blocks = re.findall(r"```python\n(.*?)```", guide.read_text(), re.DOTALL)
    namespace: dict[str, Any] = {}
    exec(blocks[0], namespace)
    exec(next(block for block in blocks if ".add_partial_payment(" in block), namespace)
    builder = namespace["builder"]
    xml = builder.to_xml(validate=True)
    assert "<ZnacznikZaplatyCzesciowej>1</ZnacznikZaplatyCzesciowej>" in xml
    assert "<KwotaZaplatyCzesciowej>50.00</KwotaZaplatyCzesciowej>" in xml


@pytest.mark.parametrize("value", [Decimal("1.005"), 1.005, "1.005"])
def test_numeric_inputs_round_after_decimal_conversion(
    value: Decimal | float | str,
) -> None:
    body = (
        InvoiceBuilder()
        .standard()
        .rows()
        .add_line(name="Service", quantity=1, unit_price_net=value, vat_rate="23")
        .done()
        .build()
    )
    assert body.rows[0].unit_price_net == Decimal("1.005")
    assert body.total_net == Decimal("1.01")
    assert body.total_vat == Decimal("0.23")
    assert body.total_gross == Decimal("1.24")


def test_float_inputs_across_builder_sections() -> None:
    body = InvoiceBuilder().standard()
    row = (
        body.rows()
        .add_line(
            name="Service",
            quantity=2.5,
            unit_price_gross=12.3,
            vat_rate="23",
            discount_amount=0.0,
            currency_exchange_rate=4.25,
        )
        .build()[0]
    )
    assert row.quantity == Decimal("2.5")
    assert row.gross_amount == Decimal("30.75")
    payment = (
        body.payment()
        .partial_payment_status("final")
        .add_partial_payment(amount=30.75, payment_date=date(2026, 6, 24))
        .build()
    )
    assert payment.partial_payments[0].amount == Decimal("30.75")
    assert payment.partial_payment_status == "final"
    settlement = (
        body.settlement()
        .add_charge(amount=2.55, reason="Delivery")
        .amount_due(33.3)
        .build()
    )
    assert settlement.charges[0].amount == Decimal("2.55")
    assert settlement.amount_due == Decimal("33.30")
    order = (
        InvoiceBuilder()
        .advance()
        .order(declared_total=12.3)
        .add_line(
            name="Service",
            gross_amount=12.3,
            quantity=1.0,
            unit_price_net=10.0,
            vat_rate="23",
        )
        .build()
    )
    assert order.total_value == Decimal("12.30")


def test_standard_builder_rejects_zero_quantity_at_body_boundary() -> None:
    body = InvoiceBuilder().standard()
    body.rows().add_line(
        name="Service", quantity=0, unit_price_net=100, vat_rate="23"
    ).done()
    with pytest.raises(KSeFValidationError, match="quantity") as caught:
        body.build()
    assert caught.value.field_path == "rows.0.quantity"
    assert caught.value.local_rule is True
