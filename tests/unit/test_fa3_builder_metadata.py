from datetime import date
from decimal import Decimal
from typing import Annotated, cast, get_args, get_origin, get_type_hints

from pydantic.fields import FieldInfo

from ksef2.fa3 import FA3InvoiceBuilder
from ksef2.domain.models.fa3.body import VatRate
from ksef2.services.builders.fa3.body.base import BaseBodyBuilder
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder
from ksef2.services.builders.fa3.sub.payment import PaymentBuilder
from ksef2.services.builders.fa3.sub.rows import RowsBuilder


def _field_info(annotation: object) -> FieldInfo:
    assert get_origin(annotation) is Annotated
    metadata = cast(tuple[object, ...], get_args(annotation)[1:])
    field_info = next(item for item in metadata if isinstance(item, FieldInfo))
    return field_info


def _type_hints(obj: object) -> dict[str, object]:
    return cast(dict[str, object], get_type_hints(obj, include_extras=True))


def test_header_metadata_is_available_via_type_hints() -> None:
    hints = _type_hints(StandardInvoiceBuilder.header)

    system_info = _field_info(hints["system_info"])
    generation_timestamp = _field_info(hints["generation_timestamp"])

    assert system_info.description == (
        "Name of the application or service that generated the invoice."
    )
    assert system_info.examples == ["my-erp", "billing-service"]
    assert generation_timestamp.json_schema_extra == {
        "x-builder-prefer-omit-when-null": True,
        "x-builder-format": "date-time",
        "x-builder-priority": "advanced",
    }


def test_body_metadata_is_available_for_billing_period() -> None:
    hints = _type_hints(BaseBodyBuilder.billing_period)

    period_start = _field_info(hints["period_start"])
    period_end = _field_info(hints["period_end"])

    assert period_start.description == (
        "Start of the billing period for period-based invoices."
    )
    assert period_start.examples == ["2026-04-01"]
    assert period_start.json_schema_extra == {
        "x-builder-prefer-omit-when-null": True,
        "x-builder-format": "date",
        "x-builder-priority": "advanced",
    }
    assert period_end.description == (
        "End of the billing period for period-based invoices."
    )


def test_add_line_metadata_marks_advanced_and_override_fields() -> None:
    hints = _type_hints(cast(object, RowsBuilder.add_line))

    quantity = _field_info(hints["quantity"])
    vat_classification = _field_info(hints["vat_classification"])
    net_amount = _field_info(hints["net_amount"])

    assert quantity.description == "Quantity billed on this line."
    assert quantity.examples == ["1", "2.5"]
    assert quantity.json_schema_extra == {
        "x-builder-prefer-omit-when-null": True,
        "x-builder-format": "decimal-string",
    }
    assert vat_classification.json_schema_extra == {
        "x-builder-prefer-omit-when-null": True,
        "x-builder-format": "object",
        "x-builder-priority": "advanced",
        "x-builder-schema-ref": "ksef2.domain.models.fa3.body.tax.VatClassification",
    }
    assert net_amount.json_schema_extra == {
        "x-builder-prefer-omit-when-null": True,
        "x-builder-format": "decimal-string",
        "x-builder-priority": "override",
    }


def test_payment_metadata_is_available_for_partial_payment() -> None:
    hints = _type_hints(cast(object, PaymentBuilder.add_partial_payment))

    amount = _field_info(hints["amount"])
    payment_date = _field_info(hints["payment_date"])

    assert amount.description == "Monetary amount used for payment entries."
    assert amount.examples == ["500.00"]
    assert amount.json_schema_extra == {
        "x-builder-prefer-omit-when-null": True,
        "x-builder-format": "decimal-string",
    }
    assert payment_date.json_schema_extra == {
        "x-builder-prefer-omit-when-null": True,
        "x-builder-format": "date",
    }


def test_runtime_builder_behavior_is_unchanged() -> None:
    invoice = (
        FA3InvoiceBuilder()
        .header(system_info="metadata-test")
        .seller(
            name="ACME S.A.",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="ul. Przykladowa 123",
        )
        .buyer(
            name="XYZ GmbH",
            country_code="DE",
            address_line_1="Unter den Linden 1",
        )
        .standard()
        .issue_date(date(2026, 4, 9))
        .invoice_number("FV/2026/04/0001")
        .payment()
        .via("bank_transfer")
        .already_paid(date(2026, 4, 10))
        .add_partial_payment(
            amount=Decimal("50.00"),
            payment_date=date(2026, 4, 10),
        )
        .done()
        .rows()
        .add_line(
            name="Consulting service",
            quantity=Decimal("1"),
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
        .build()
    )

    assert invoice.body.invoice_number == "FV/2026/04/0001"
    assert invoice.body.issue_date == date(2026, 4, 9)
    assert invoice.body.rows[0].vat_rate is VatRate.VAT_23
    assert invoice.body.payment is not None
    assert invoice.body.payment.payment_form == "bank_transfer"
    assert invoice.body.payment.partial_payments[0].amount == Decimal("50.00")
