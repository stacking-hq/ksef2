from pydantic import ValidationError
import pytest

from ksef2.domain.models.fa3.attachment import AttachmentTable


def test_attachment_table_accepts_column_names_matching_column_format() -> None:
    table = AttachmentTable(
        columns_names=["Service", "Amount", "SupplyDate"],
        columns_format=["txt", "decimal", "date"],
        rows=[["Consulting", "100.00", "2026-04-03"]],
    )

    assert table.columns_names == ["Service", "Amount", "SupplyDate"]


def test_attachment_table_rejects_column_names_count_mismatch() -> None:
    with pytest.raises(
        ValidationError, match="Column names count does not match column format count"
    ):
        AttachmentTable(
            columns_names=["Service", "Amount"],
            columns_format=["txt", "decimal", "date"],
            rows=[["Consulting", "100.00", "2026-04-03"]],
        )
