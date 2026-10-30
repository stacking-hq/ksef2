"""FA(3) formatting preserves SDK validation errors and their diagnostics."""

import json

import pytest
from pydantic import ValidationError

from ksef2 import KSeFArgumentError, KSeFValidationError
from ksef2.fa3 import InvoiceBuilder, KsefInvoiceDraft
from ksef2._domain.models.fa3.body.row import InvoiceRow
from ksef2._domain.models.base import KSeFBaseModel


@pytest.mark.parametrize("entry_point", ["json", "dict", "builder"])
def test_invalid_vat_rate_preserves_actionable_sdk_error(entry_point: str) -> None:
    row = {"name": "Service", "vat_rate": "24"}
    draft = {"body": {"rows": [row]}}
    with pytest.raises(KSeFValidationError) as caught:
        if entry_point == "json":
            InvoiceBuilder.from_state_json(json.dumps(draft))
        elif entry_point == "dict":
            InvoiceBuilder.from_state(KsefInvoiceDraft.model_validate(draft))
        else:
            InvoiceBuilder().standard().rows().add_line(
                name="Service", quantity=1, unit_price_net=100, vat_rate="24"
            )

    error = caught.value
    assert isinstance(error, KSeFArgumentError)
    assert "Invalid VatRate value '24'" in str(error)
    assert "Valid values are: VAT_23 (23), VAT_22 (22), VAT_8 (8)" in str(error)
    assert "REVERSE_CHARGE (oo)" in str(error)
    assert error.errors() == []
    if entry_point == "builder":
        assert error.__cause__ is None
    else:
        assert isinstance(error.__cause__, ValidationError)
        assert error.__cause__.errors()[0].get("ctx", {}).get("error") is error


@pytest.mark.parametrize("structured", [False, True])
def test_formatting_preserves_exception_and_diagnostics(
    monkeypatch: pytest.MonkeyPatch, structured: bool
) -> None:
    cause = ValidationError.from_exception_data(
        "InvoiceRow",
        [
            {
                "type": "greater_than",
                "loc": ("quantity",),
                "input": 0,
                "ctx": {"gt": 0},
            },
            {"type": "missing", "loc": ("name",), "input": {}},
        ],
    )
    error = KSeFValidationError(
        "Original validation message",
        validation_error=cause if structured else None,
        parameter="quantity",
    )
    details = error.errors()
    context = error.context.copy()

    def reject(self: KSeFBaseModel, **data: object) -> None:
        raise error from cause

    monkeypatch.setattr(KSeFBaseModel, "__init__", reject)
    with pytest.raises(KSeFValidationError) as caught:
        InvoiceRow(name="Service")

    assert caught.value is error
    assert error.__cause__ is cause
    assert error.validation_error is (cause if structured else None)
    assert error.errors() == details
    assert all(error.context[key] == value for key, value in context.items())
    if structured:
        assert error.field_path == "quantity"
        assert error.local_rule is True
        assert error.hint
    else:
        assert error.context == context
    expected = (
        "Invalid FA(3) builder quantity: Input should be greater than 0"
        if structured
        else "Original validation message"
    )
    assert error.args == (expected,)
