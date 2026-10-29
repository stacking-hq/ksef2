from datetime import date, datetime, timezone
from decimal import Decimal
import json

import pytest

from ksef2 import KSeFValidationError

from ksef2.fa3 import InvoiceBuilder, KsefInvoiceDraft, VatRate


def test_fa3_builder_can_roundtrip_partial_draft_json() -> None:
    draft_json = (
        InvoiceBuilder()
        .header(
            generation_timestamp=datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
            system_info="draft json test",
        )
        .seller(
            name="ACME S.A.",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="ul. Przykladowa 123",
        )
        .dump_state_json(indent=2)
    )

    restored_draft = KsefInvoiceDraft.model_validate_json(draft_json)
    restored_builder = InvoiceBuilder.from_state_json(draft_json)

    assert restored_draft.buyer is None
    assert restored_draft.body is None
    assert restored_draft.seller is not None
    assert restored_draft.seller.tax_id == "1234567890"

    invoice = (
        restored_builder.buyer(
            name="XYZ GmbH",
            country_code="DE",
            address_line_1="Unter den Linden 1",
        )
        .standard()
        .issue_date(date(2026, 4, 8))
        .invoice_number("FV/2026/04/0001")
        .rows()
        .add_line(
            name="Consulting service",
            quantity=Decimal("1"),
            unit_of_measure="h",
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
        .build()
    )

    assert invoice.body.invoice_number == "FV/2026/04/0001"
    assert invoice.body.rows[0].vat_rate is VatRate.VAT_23


def test_fa3_builder_can_reload_existing_sections_and_continue_editing() -> None:
    builder = InvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
            system_info="draft reload test",
        )
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
    )
    _ = builder.footer().add_information("Original footer note").done()
    _ = (
        builder.standard()
        .issue_date(date(2026, 4, 8))
        .invoice_number("FV/2026/04/0002")
        .rows()
        .add_line(
            name="Initial line",
            quantity=Decimal("1"),
            unit_of_measure="h",
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .payment()
        .via("bank_transfer")
        .bank_account("PL10101010101010101010101010")
        .done()
        .done()
    )

    restored_builder = InvoiceBuilder.from_state(builder.dump_state())
    _ = restored_builder.footer().add_information("Updated footer note").done()
    _ = (
        restored_builder.standard()
        .rows()
        .add_line(
            name="Follow-up line",
            quantity=Decimal("2"),
            unit_of_measure="h",
            unit_price_net=Decimal("50.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .payment()
        .due_on(date(2026, 4, 15))
        .done()
        .done()
    )

    invoice = restored_builder.build()

    assert invoice.footer is not None
    assert invoice.footer.additional_informations == [
        "Original footer note",
        "Updated footer note",
    ]
    assert len(invoice.body.rows) == 2
    assert invoice.body.payment is not None
    assert invoice.body.payment.payment_form == "bank_transfer"
    assert invoice.body.payment.payment_terms[0].due_date == date(2026, 4, 15)


def test_fa3_draft_can_be_created_from_built_invoice() -> None:
    invoice = (
        InvoiceBuilder()
        .header(
            generation_timestamp=datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
            system_info="invoice snapshot test",
        )
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
        .issue_date(date(2026, 4, 8))
        .invoice_number("FV/2026/04/0003")
        .rows()
        .add_line(
            name="Consulting service",
            quantity=Decimal("1"),
            unit_of_measure="h",
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
        .build()
    )

    draft = KsefInvoiceDraft.from_invoice(invoice)
    restored_builder = InvoiceBuilder.from_state(draft)

    assert restored_builder.build() == invoice


@pytest.mark.parametrize("entrypoint", ["constructor", "python", "json", "builder"])
def test_draft_rejects_quantity_typo_before_build(entrypoint: str) -> None:
    data = {
        "body": {
            "issue_date": "2026-10-29",
            "rows": [{"qty": "10", "unit_price_net": "100.00", "vat_rate": "23"}],
        }
    }
    with pytest.raises(KSeFValidationError) as caught:
        if entrypoint == "constructor":
            KsefInvoiceDraft(**data)  # pyright: ignore[reportArgumentType]
        elif entrypoint == "python":
            KsefInvoiceDraft.model_validate(data)
        elif entrypoint == "json":
            KsefInvoiceDraft.model_validate_json(json.dumps(data))
        else:
            InvoiceBuilder.from_state_json(json.dumps(data))
    assert caught.value.errors()[0]["loc"] == ("body", "rows", 0, "qty")
    assert "body.rows.0.qty" in str(caught.value)


def test_draft_schema_forbids_nested_unknown_fields() -> None:
    schema = KsefInvoiceDraft.model_json_schema()
    objects = [schema, *schema["$defs"].values()]
    assert len([item for item in objects if "properties" in item]) > 20
    for item in objects:
        if "properties" in item:
            assert item["additionalProperties"] is False, item.get("title")


@pytest.mark.parametrize(
    "path",
    [
        ("header",),
        ("seller",),
        ("seller", "address"),
        ("buyer", "contact"),
        ("third_parties", 0, "contact", 0),
        ("body",),
        ("body", "rows", 0),
        ("body", "rows", 0, "vat_classification"),
        ("body", "payment"),
        ("body", "payment", "bank_accounts", 0),
        ("body", "correction"),
        ("body", "correction", "corrected_seller", "address"),
        ("attachment", "data_blocks", 0, "tables", 0),
        ("footer",),
        ("attachment",),
    ],
)
def test_draft_rejects_nested_extras_with_full_path(
    path: tuple[str | int, ...],
) -> None:
    data: object = {"unexpected": True}
    for part in reversed(path):
        data = [data] if isinstance(part, int) else {part: data}
    with pytest.raises(KSeFValidationError) as caught:
        KsefInvoiceDraft.model_validate(data)
    assert caught.value.errors()[0]["loc"] == (*path, "unexpected")
    assert caught.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize(
    "row",
    [
        {"name": "Description only"},
        {"name": "Explicit amount", "net_amount": "1000.00", "vat_rate": "23"},
        {"name": "Margin", "tax_regime": "margin", "gross_amount": "1000.00"},
    ],
)
def test_draft_preserves_rows_without_quantity(row: dict[str, str]) -> None:
    draft = KsefInvoiceDraft.model_validate(
        {"body": {"issue_date": "2026-10-29", "rows": [row]}}
    )
    assert draft.body is not None
    assert draft.body.rows[0].quantity is None
    assert draft.body.rows[0].name == row["name"]


def test_valid_draft_builds_original_example_total() -> None:
    builder = (
        InvoiceBuilder()
        .header()
        .seller(
            name="Seller",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="Street 1",
        )
        .buyer(name="Buyer", country_code="PL", address_line_1="Street 2")
        .standard()
        .issue_date(date(2026, 10, 29))
        .invoice_number("FV/1")
        .rows()
        .add_line(
            name="Service",
            quantity=Decimal("10"),
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
    )
    restored = InvoiceBuilder.from_state_json(builder.dump_state_json())
    assert restored.build().total_gross == Decimal("1230.00")
    assert "1230.00" in restored.to_xml()


def test_draft_strictness_does_not_change_shared_models() -> None:
    from ksef2.fa3 import InvoiceEntity
    from ksef2._domain.models.base import KSeFBaseModel

    KsefInvoiceDraft.model_json_schema()
    assert (
        InvoiceEntity.model_validate({"name": "Seller", "future_field": 1}).name
        == "Seller"
    )
    assert KSeFBaseModel.model_validate({"future_api_field": 1}).model_dump() == {}
    assert InvoiceEntity.model_json_schema().get("additionalProperties") is not False


def test_draft_preserves_free_form_attachment_metadata() -> None:
    draft = KsefInvoiceDraft.model_validate(
        {
            "attachment": {
                "data_blocks": [{"meta_data": [{"Customer reference": "custom value"}]}]
            }
        }
    )
    assert draft.attachment is not None
    assert draft.attachment.data_blocks[0].meta_data == [
        {"Customer reference": "custom value"}
    ]


def test_draft_schema_is_strict_when_embedded_in_type_adapter() -> None:
    from pydantic import TypeAdapter

    schema = TypeAdapter(list[KsefInvoiceDraft]).json_schema()
    assert schema["$defs"]["InvoiceRow"]["additionalProperties"] is False
    assert schema["$defs"]["InvoiceAddress"]["additionalProperties"] is False
