"""FA(3) attachment block domain models."""

from collections.abc import Sequence
from datetime import datetime, date, time
from decimal import Decimal, InvalidOperation
from typing import Literal, Self

from pydantic import field_validator, Field, model_validator

from ksef2.domain.models import KSeFBaseModel

ValueType = Literal["date", "datetime", "decimal", "integer", "time", "txt"]
NUMERIC_TYPES = {"decimal", "integer"}


class AttachmentTable(KSeFBaseModel):
    """FA(3) invoice attachment table structure.

    References:
        schemat.FakturaZalacznikBlokDanychTabela

    Maps:
    meta_data - tmeta_dane List(FakturaZalacznikBlokDanychTabelaTmetaDane)
    description - opis (str)
    columns_names - tnaglowek/kol/nkom (list[str])
    columns_format - tnaglowek/kol/typ (list[ValueType])
    rows - wiersz (FakturaZalacznikBlokDanychTabelaWiersz)
    summary - suma (FakturaZalacznikBlokDanychTabelaSuma)
    """

    meta_data: list[dict[str, str]] = Field(default_factory=list)
    description: str | None = None
    columns_names: list[str] | None = None
    columns_format: list[ValueType] = Field(default_factory=list)
    rows: list[list[str]] = Field(
        min_length=1,
        max_length=1000,
        description="Maps to FakturaZalacznikBlokDanychTabelaWiersz",
    )
    summary: list[str] | None = Field(default=None, description="Maps to")

    @model_validator(mode="after")
    def validate_rows_and_columns(self) -> Self:
        if any(len(row) > len(self.columns_format) for row in self.rows):
            raise ValueError("Row has more cells than declared columns")

        if self.columns_names is not None and len(self.columns_names) != len(
            self.columns_format
        ):
            raise ValueError("Column names count does not match column format count")

        def _validate_cell(value: str, row_idx: int, col_idx: int) -> None:
            if value in {"", "-"}:
                return
            match self.columns_format[col_idx]:
                case "decimal" | "integer":
                    try:
                        _ = Decimal(value)
                    except InvalidOperation as exc:
                        raise ValueError(
                            f"Cell ({row_idx}, {col_idx}) of value `{value}` is not numeric"
                        ) from exc
                case "date":
                    try:
                        _ = date.fromisoformat(value)
                    except ValueError as exc:
                        raise ValueError(
                            f"Cell ({row_idx}, {col_idx}) of value `{value}` is not a valid date"
                        ) from exc
                case "datetime":
                    try:
                        _ = datetime.fromisoformat(value)
                    except ValueError as exc:
                        raise ValueError(
                            f"Cell ({row_idx}, {col_idx}) of value `{value}` is not a valid datetime"
                        ) from exc
                case "time":
                    try:
                        _ = time.fromisoformat(value)
                    except ValueError as exc:
                        raise ValueError(
                            f"Cell ({row_idx}, {col_idx}) of value `{value}` is not a valid time"
                        ) from exc
                case "txt":
                    return
                case _:
                    raise ValueError(  # pyright: ignore[reportUnreachable]
                        f"Unsupported column type: {self.columns_format[col_idx]}"
                    )

        for row_idx, row in enumerate(self.rows):
            for col_idx, cell in enumerate(row):
                _validate_cell(cell, row_idx, col_idx)

        return self

    @model_validator(mode="after")
    def populate_summary(self) -> Self:
        if self.summary is not None:
            return self

        if not self.rows or not self.columns_format:
            return self
        if any(len(row) != len(self.columns_format) for row in self.rows):
            return self

        summary: list[str] = []

        for col_idx, col_type in enumerate(self.columns_format):
            if col_type not in NUMERIC_TYPES:
                summary.append("-")
                continue

            try:
                total = sum(Decimal(row[col_idx]) for row in self.rows)
            except InvalidOperation as exc:
                raise ValueError(
                    f"Column {col_idx} declared as {col_type} but contains non-numeric data"
                ) from exc

            summary.append(str(total))

        self.summary = summary
        return self


class DataBlock(KSeFBaseModel):
    """FA(3) invoice attachment data block.

    References:
        schemat.FakturaZalacznikBlokDanych

    Maps:
        header - znaglowek (str)
        meta_data - meta_dane (FakturaZalacznikBlokDanychMetaDane)
        paragraphs:
            tekst - akapit (FakturaZalacznikBlokDanychTekst)
        tables - tabela (FakturaZalacznikBlokDanychTabela)

    """

    header: str | None = None
    meta_data: Sequence[dict[str, str]] | None = Field(
        default=None, description="Maps to FakturaZalacznikBlokDanychMetaDane"
    )
    paragraphs: Sequence[str] | None = Field(
        default=None,
        description="Maps to FakturaZalacznikBlokDanychTekst",
        min_length=1,
        max_length=10,
    )
    tables: list[AttachmentTable] | None = None

    @field_validator("paragraphs")
    @classmethod
    def validate_paragraphs(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value

        if any(len(p) == 0 or len(p) > 512 for p in value):
            raise ValueError("Paragraphs must be between 1 and 512 characters long")

        return value


class Attachment(KSeFBaseModel):
    """FA(3) invoice attachment containing data blocks.

    References:
        schemat.FakturaZalacznik

    Maps:
        data_blocks - blok_danych List(FakturaZalacznikBlokDanych)
    """

    data_blocks: list[DataBlock]
