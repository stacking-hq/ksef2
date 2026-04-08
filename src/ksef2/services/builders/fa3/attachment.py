from typing import Callable, Self

from ksef2.domain.models.fa3.attachment import (
    Attachment,
    AttachmentTable,
    DataBlock,
    ValueType,
)


class AttachmentTableBuilder:
    def __init__(
        self,
        parent: "DataBlockBuilder | None" = None,
        existing_state: AttachmentTable | None = None,
    ) -> None:
        self._parent = parent
        self._meta_data: list[dict[str, str]] = (
            list(existing_state.meta_data) if existing_state else []
        )
        self._description: str | None = (
            existing_state.description if existing_state else None
        )
        self._columns_names: list[str] | None = (
            list(existing_state.columns_names)
            if existing_state and existing_state.columns_names
            else None
        )
        self._columns_format: list[ValueType] = (
            list(existing_state.columns_format) if existing_state else []
        )
        self._rows: list[list[str]] = (
            [list(row) for row in existing_state.rows] if existing_state else []
        )
        self._summary: list[str] | None = (
            list(existing_state.summary)
            if existing_state and existing_state.summary
            else None
        )

    def from_model(self, table: AttachmentTable | None) -> Self:
        table = table.model_copy(deep=True) if table is not None else None
        self._meta_data = list(table.meta_data) if table else []
        self._description = table.description if table else None
        self._columns_names = (
            list(table.columns_names) if table and table.columns_names else None
        )
        self._columns_format = list(table.columns_format) if table else []
        self._rows = [list(row) for row in table.rows] if table else []
        self._summary = list(table.summary) if table and table.summary else None
        return self

    def set_description(self, description: str | None) -> Self:
        self._description = description
        return self

    def add_meta_data(self, key: str, value: str) -> Self:
        self._meta_data.append({key: value})
        return self

    def clear_meta_data(self) -> Self:
        self._meta_data = []
        return self

    def set_columns(
        self, formats: list[ValueType], names: list[str] | None = None
    ) -> Self:
        self._columns_format = list(formats)
        self._columns_names = list(names) if names is not None else None
        return self

    def add_row(self, row: list[str]) -> Self:
        self._rows.append([str(value) for value in row])
        return self

    def add_rows(self, rows: list[list[str]]) -> Self:
        self._rows.extend([[str(value) for value in row] for row in rows])
        return self

    def clear_rows(self) -> Self:
        self._rows = []
        return self

    def set_summary(self, summary: list[str] | None) -> Self:
        self._summary = list(summary) if summary is not None else None
        return self

    def build(self) -> AttachmentTable:
        return AttachmentTable(
            meta_data=self._meta_data,
            description=self._description,
            columns_names=self._columns_names,
            columns_format=self._columns_format,
            rows=self._rows,
            summary=self._summary,
        )

    def _is_empty(self) -> bool:
        return (
            not self._rows
            and not self._meta_data
            and self._description is None
            and not self._columns_format
            and self._columns_names is None
            and self._summary is None
        )

    def done(self) -> "DataBlockBuilder":
        if self._parent is None:
            raise ValueError(
                "AttachmentTableBuilder must have a parent DataBlockBuilder to call done()."
            )
        if self._is_empty():
            raise ValueError(
                "Attachment table is empty. Add at least one row before calling done()."
            )
        _ = self._parent.add_table_model(self.build())
        return self._parent


class DataBlockBuilder:
    def __init__(
        self,
        parent: "AttachmentBuilder[object] | None" = None,
        existing_state: DataBlock | None = None,
    ) -> None:
        self._parent = parent
        self._header: str | None = existing_state.header if existing_state else None
        self._meta_data: list[dict[str, str]] = (
            list(existing_state.meta_data)
            if existing_state and existing_state.meta_data
            else []
        )
        self._paragraphs: list[str] = (
            list(existing_state.paragraphs)
            if existing_state and existing_state.paragraphs
            else []
        )
        self._tables: list[AttachmentTable] = (
            [table.model_copy(deep=True) for table in existing_state.tables]
            if existing_state and existing_state.tables
            else []
        )

    def from_model(self, block: DataBlock | None) -> Self:
        block = block.model_copy(deep=True) if block is not None else None
        self._header = block.header if block else None
        self._meta_data = list(block.meta_data) if block and block.meta_data else []
        self._paragraphs = list(block.paragraphs) if block and block.paragraphs else []
        self._tables = list(block.tables) if block and block.tables else []
        return self

    def set_header(self, header: str | None) -> Self:
        self._header = header
        return self

    def add_meta_data(self, key: str, value: str) -> Self:
        self._meta_data.append({key: value})
        return self

    def clear_meta_data(self) -> Self:
        self._meta_data = []
        return self

    def add_paragraph(self, text: str) -> Self:
        self._paragraphs.append(text)
        return self

    def clear_paragraphs(self) -> Self:
        self._paragraphs = []
        return self

    def build_table(self) -> AttachmentTableBuilder:
        return AttachmentTableBuilder(self, None)

    def add_table_model(self, table: AttachmentTable) -> Self:
        self._tables.append(table)
        return self

    def clear_tables(self) -> Self:
        self._tables = []
        return self

    def build(self) -> DataBlock:
        return DataBlock(
            header=self._header,
            meta_data=self._meta_data if self._meta_data else None,
            paragraphs=self._paragraphs if self._paragraphs else None,
            tables=self._tables if self._tables else None,
        )

    def _is_empty(self) -> bool:
        return (
            self._header is None
            and not self._meta_data
            and not self._paragraphs
            and not self._tables
        )

    def done(self) -> "AttachmentBuilder[object]":
        if self._parent is None:
            raise ValueError(
                "DataBlockBuilder must have a parent AttachmentBuilder to call done()."
            )
        if self._is_empty():
            raise ValueError(
                "Attachment data block is empty. Set at least one field before calling done()."
            )
        _ = self._parent.add_data_block_model(self.build())
        return self._parent


class AttachmentBuilder[TParent]:
    def __init__(
        self,
        parent: TParent | None = None,
        on_done: Callable[[Attachment], None] | None = None,
        existing_state: Attachment | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._data_blocks: list[DataBlock] = (
            [block.model_copy(deep=True) for block in existing_state.data_blocks]
            if existing_state
            else []
        )

    def from_model(self, attachment: Attachment | None) -> Self:
        attachment = (
            attachment.model_copy(deep=True) if attachment is not None else None
        )
        self._data_blocks = list(attachment.data_blocks) if attachment else []
        return self

    def build_data_block(self) -> DataBlockBuilder:
        return DataBlockBuilder(self, None)

    def add_data_block_model(self, block: DataBlock) -> Self:
        self._data_blocks.append(block)
        return self

    def clear_data_blocks(self) -> Self:
        self._data_blocks = []
        return self

    def build(self) -> Attachment:
        return Attachment(data_blocks=self._data_blocks)

    def _is_empty(self) -> bool:
        return not self._data_blocks

    def done(self) -> TParent:
        if self._parent is None or self._on_done is None:
            raise ValueError(
                "AttachmentBuilder must have a parent builder to call done()."
            )
        if self._is_empty():
            raise ValueError(
                "Attachment details are empty. Add at least one data block before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class AttachmentBuilderMixin:
    _attachment: Attachment | None = None

    def attachment(self) -> AttachmentBuilder[Self]:
        return AttachmentBuilder(self, self._set_attachment, self._attachment)

    def _set_attachment(self, attachment: Attachment) -> None:
        self._attachment = attachment
