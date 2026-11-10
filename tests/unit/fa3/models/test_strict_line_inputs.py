"""Financial line inputs reject typos and mutation without changing derived totals."""

import json
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from ksef2 import KSeFValidationError
from ksef2.fa3 import InvoiceOrderLine, InvoiceRow, VatRate


@pytest.mark.parametrize("model", [InvoiceRow, InvoiceOrderLine])
@pytest.mark.parametrize(
    "entry", ["constructor", "python", "json", "strings", "adapter"]
)
def test_line_rejects_unknown_fields(
    model: type[InvoiceRow | InvoiceOrderLine], entry: str
) -> None:
    data = {
        "name": "X",
        "gross_amount": "123",
        "vat_rate": "23",
        "net_ammount": "100",
    }
    with pytest.raises(
        ValidationError if entry == "adapter" else KSeFValidationError,
        match="net_ammount",
    ):
        if entry == "constructor":
            model(**data)  # pyright: ignore[reportArgumentType] - intentional invalid input
        elif entry == "python":
            model.model_validate(data)
        elif entry == "json":
            model.model_validate_json(json.dumps(data))
        elif entry == "strings":
            model.model_validate_strings(data)
        else:
            TypeAdapter(model).validate_python(data)


@pytest.mark.parametrize("model", [InvoiceRow, InvoiceOrderLine])
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", Decimal("3")),
        ("unit_price_net", Decimal("300")),
        ("vat_rate", VatRate.VAT_8),
        ("net_amount", Decimal("999")),
        ("vat_amount", Decimal("999")),
        ("gross_amount", Decimal("999")),
        ("name", "changed"),
    ],
)
def test_line_rejects_assignment_and_preserves_amounts(
    model: type[InvoiceRow | InvoiceOrderLine], field: str, value: object
) -> None:
    line = model(gross_amount=Decimal("123"), vat_rate=VatRate.VAT_23)
    original = line.model_dump()
    with pytest.raises(ValidationError) as caught:
        setattr(line, field, value)
    assert caught.value.errors()[0]["type"] == "frozen_instance"
    assert line.model_dump() == original


@pytest.mark.parametrize("model", [InvoiceRow, InvoiceOrderLine])
def test_line_rejects_field_deletion(
    model: type[InvoiceRow | InvoiceOrderLine],
) -> None:
    line = model(gross_amount=Decimal("123"), vat_rate=VatRate.VAT_23)
    with pytest.raises(ValidationError) as caught:
        del line.gross_amount
    assert caught.value.errors()[0]["type"] == "frozen_instance"
    assert line.gross_amount == Decimal("123.00")


@pytest.mark.parametrize("model", [InvoiceRow, InvoiceOrderLine])
def test_line_derived_amounts_survive_round_trip_and_nested_validation(
    model: type[InvoiceRow | InvoiceOrderLine],
) -> None:
    original = model(
        gross_amount=Decimal("123"), quantity=Decimal("2"), vat_rate=VatRate.VAT_23
    )
    restored = model.model_validate_json(original.model_dump_json())
    assert restored.model_dump() == original.model_dump()
    adapter = (
        TypeAdapter(list[InvoiceRow])
        if isinstance(original, InvoiceRow)
        else TypeAdapter(list[InvoiceOrderLine])
    )
    assert adapter.validate_python([original]) == [original]
    assert restored.net_amount == Decimal("100.00")
    assert restored.vat_amount == Decimal("23.00")
    assert {"net_amount", "vat_amount"} <= original.model_fields_set


def test_reconstruct_row_from_source_recalculates_amounts() -> None:
    source = dict(
        name="Service",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        vat_rate=VatRate.VAT_23,
    )
    original = InvoiceRow.model_validate(source)
    source["quantity"] = Decimal("3")
    updated = InvoiceRow.model_validate(source)
    assert original.gross_amount == Decimal("123.00")
    assert updated.net_amount == Decimal("300.00")
    assert updated.vat_amount == Decimal("69.00")
    assert updated.gross_amount == Decimal("369.00")


def test_reconstruct_order_line_from_source_recalculates_amounts() -> None:
    source = dict(name="Service", gross_amount=Decimal("123"), vat_rate=VatRate.VAT_23)
    original = InvoiceOrderLine.model_validate(source)
    source["gross_amount"] = Decimal("369")
    updated = InvoiceOrderLine.model_validate(source)
    assert original.net_amount == Decimal("100.00")
    assert updated.net_amount == Decimal("300.00")
    assert updated.vat_amount == Decimal("69.00")
