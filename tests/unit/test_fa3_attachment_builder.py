"""Unit tests for the fluent FA(3) attachment builders reached from the public builder."""

import pytest

from ksef2.fa3 import FA3InvoiceBuilder
from ksef2._domain.models.fa3.attachment import (
    Attachment,
    AttachmentTable,
    DataBlock,
)
from ksef2._services.builders.fa3.attachment import (
    AttachmentBuilder,
    AttachmentTableBuilder,
    DataBlockBuilder,
)


def started_invoice() -> FA3InvoiceBuilder:
    builder = FA3InvoiceBuilder()
    _ = builder.header(system_info="billing-service")
    _ = builder.seller(
        name="ACME S.A.",
        tax_id="1234567890",
        country_code="PL",
        address_line_1="ul. Przykladowa 123",
    )
    _ = builder.buyer(
        name="XYZ GmbH",
        country_code="PL",
        address_line_1="Unter den Linden 1",
    )
    return builder


def test_table_builder_collects_every_element() -> None:
    table = (
        AttachmentTableBuilder()
        .set_description("Specification of delivered items")
        .add_meta_data("document_type", "technical_specification")
        .add_meta_data("revision", "2")
        .clear_meta_data()
        .add_meta_data("document_type", "technical_specification")
        .set_columns(["txt", "decimal"], names=["Item", "Net value"])
        .add_row(["Keyboard", "199.00"])
        .add_rows([["Mouse", "99.00"], ["Cable", "9.00"]])
        .clear_rows()
        .add_row(["Keyboard", "199.00"])
        .set_summary(["Total net: 199.00"])
        .build()
    )

    assert table.description == "Specification of delivered items"
    assert table.meta_data == [{"document_type": "technical_specification"}]
    assert table.columns_names == ["Item", "Net value"]
    assert table.columns_format == ["txt", "decimal"]
    assert table.rows == [["Keyboard", "199.00"]]
    assert table.summary == ["Total net: 199.00"]


def test_table_builder_without_names_keeps_columns_unnamed() -> None:
    table = AttachmentTableBuilder().set_columns(["txt"]).add_row(["Keyboard"]).build()

    assert table.columns_names is None
    assert table.columns_format == ["txt"]


def test_table_builder_clears_description_and_summary_with_none() -> None:
    table = (
        AttachmentTableBuilder()
        .set_columns(["txt", "decimal"], names=["Item", "Net value"])
        .set_description("Specification")
        .set_summary(["Total", "0.00"])
        .set_description(None)
        .set_summary(None)
        .add_row(["Keyboard", "199.00"])
        .add_row(["Mouse", "99.00"])
        .build()
    )

    assert table.description is None
    assert table.summary == ["-", "298.00"]


def test_table_builder_from_model_replaces_the_state() -> None:
    existing = AttachmentTable(
        description="Existing",
        columns_format=["txt"],
        rows=[["Old"]],
    )

    table = (
        AttachmentTableBuilder()
        .add_row(["Draft"])
        .from_model(existing)
        .add_row(["New"])
        .build()
    )

    assert table.description == "Existing"
    assert table.rows == [["Old"], ["New"]]


def test_table_builder_from_model_none_empties_the_state() -> None:
    table = (
        AttachmentTableBuilder()
        .set_description("Draft")
        .add_row(["Draft"])
        .from_model(None)
        .set_columns(["txt"])
        .add_row(["New"])
        .build()
    )

    assert table.description is None
    assert table.rows == [["New"]]


def test_table_builder_done_without_a_parent_is_rejected() -> None:
    with pytest.raises(ValueError, match="must have a parent DataBlockBuilder"):
        AttachmentTableBuilder().add_row(["Keyboard"]).done()


def test_empty_table_builder_done_is_rejected() -> None:
    block = AttachmentBuilder().build_data_block()

    with pytest.raises(ValueError, match="Attachment table is empty"):
        _ = block.build_table().done()


def test_data_block_builder_collects_every_element() -> None:
    block = (
        DataBlockBuilder()
        .set_header("Technical specification")
        .add_meta_data("source", "warehouse_system")
        .clear_meta_data()
        .add_meta_data("source", "warehouse_system")
        .add_paragraph("The goods were inspected before dispatch.")
        .clear_paragraphs()
        .add_paragraph("The goods were inspected before dispatch.")
        .add_table_model(AttachmentTable(columns_format=["txt"], rows=[["Keyboard"]]))
        .clear_tables()
        .build_table()
        .set_columns(["txt"])
        .add_row(["Keyboard"])
        .done()
        .build()
    )

    assert block.header == "Technical specification"
    assert block.meta_data == [{"source": "warehouse_system"}]
    assert block.paragraphs == ["The goods were inspected before dispatch."]
    assert block.tables is not None
    assert len(block.tables) == 1
    assert block.tables[0].rows == [["Keyboard"]]


def test_data_block_builder_from_model_replaces_the_state() -> None:
    existing = DataBlock(header="Existing", paragraphs=["Old"])

    block = (
        DataBlockBuilder()
        .add_paragraph("Draft")
        .from_model(existing)
        .add_paragraph("New")
        .build()
    )

    assert block.header == "Existing"
    assert block.paragraphs == ["Old", "New"]


def test_data_block_builder_from_model_none_empties_the_state() -> None:
    block = DataBlockBuilder().set_header("Draft").from_model(None).build()

    assert block.header is None
    assert block.meta_data is None
    assert block.paragraphs is None
    assert block.tables is None


def test_data_block_builder_done_without_a_parent_is_rejected() -> None:
    with pytest.raises(ValueError, match="must have a parent AttachmentBuilder"):
        DataBlockBuilder().set_header("Spec").done()


def test_empty_data_block_builder_done_is_rejected() -> None:
    with pytest.raises(ValueError, match="Attachment data block is empty"):
        _ = AttachmentBuilder().build_data_block().done()


def test_attachment_builder_collects_every_element() -> None:
    attachment = (
        AttachmentBuilder()
        .add_data_block_model(DataBlock(header="First"))
        .clear_data_blocks()
        .build_data_block()
        .set_header("Only block")
        .done()
        .build()
    )

    assert attachment.data_blocks[0].header == "Only block"


def test_attachment_builder_from_model_replaces_the_state() -> None:
    existing = Attachment(data_blocks=[DataBlock(header="Existing")])

    attachment = (
        AttachmentBuilder()
        .add_data_block_model(DataBlock(header="Draft"))
        .from_model(existing)
        .add_data_block_model(DataBlock(header="Added"))
        .build()
    )

    assert [block.header for block in attachment.data_blocks] == [
        "Existing",
        "Added",
    ]


def test_attachment_builder_from_model_none_empties_the_state() -> None:
    attachment = (
        AttachmentBuilder()
        .add_data_block_model(DataBlock(header="Draft"))
        .from_model(None)
        .build()
    )

    assert attachment.data_blocks == []


def test_attachment_builder_done_without_a_parent_is_rejected() -> None:
    with pytest.raises(ValueError, match="must have a parent builder"):
        AttachmentBuilder().add_data_block_model(DataBlock(header="Block")).done()


def test_empty_attachment_builder_done_is_rejected() -> None:
    with pytest.raises(ValueError, match="Attachment details are empty"):
        _ = started_invoice().attachment().done()


def test_attachment_chain_from_the_public_builder_lands_in_the_draft() -> None:
    builder = started_invoice()

    attachment_builder = builder.attachment()
    assert isinstance(attachment_builder, AttachmentBuilder)

    _ = (
        attachment_builder.build_data_block()
        .set_header("Technical specification")
        .add_paragraph("The goods were inspected before dispatch.")
        .build_table()
        .set_description("Specification of delivered items")
        .set_columns(["txt", "decimal"], names=["Item", "Net value"])
        .add_row(["Keyboard", "199.00"])
        .done()
        .done()
        .done()
    )

    attachment = builder.dump_state().attachment
    assert attachment is not None
    assert attachment.data_blocks[0].header == "Technical specification"
    table = attachment.data_blocks[0].tables
    assert table is not None
    assert table[0].columns_names == ["Item", "Net value"]
    assert table[0].rows == [["Keyboard", "199.00"]]


def test_reopening_the_attachment_builder_keeps_the_previous_blocks() -> None:
    builder = started_invoice()
    _ = builder.attachment().build_data_block().set_header("First").done().done()

    _ = builder.attachment().build_data_block().set_header("Second").done().done()

    attachment = builder.dump_state().attachment
    assert attachment is not None
    assert [block.header for block in attachment.data_blocks] == ["First", "Second"]


def test_attachment_survives_the_draft_round_trip() -> None:
    builder = started_invoice()
    _ = (
        builder.attachment()
        .build_data_block()
        .set_header("Technical specification")
        .build_table()
        .set_columns(["txt"])
        .add_row(["Keyboard"])
        .done()
        .done()
        .done()
    )

    restored = FA3InvoiceBuilder.from_state(builder.dump_state())

    restored_attachment = restored.dump_state().attachment
    assert restored_attachment is not None
    assert restored_attachment == builder.dump_state().attachment
