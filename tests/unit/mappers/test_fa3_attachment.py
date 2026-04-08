from ksef2.domain.models.fa3.attachment import Attachment, AttachmentTable, DataBlock
from ksef2.infra.mappers.invoices.fa3.domain.attachment import from_spec, to_spec
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaZalacznik,
    FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp,
)


def make_attachment() -> Attachment:
    return Attachment(
        data_blocks=[
            DataBlock(
                header="Attachment header",
                meta_data=[{"source": "manual"}],
                paragraphs=["First paragraph", "Second paragraph"],
                tables=[
                    AttachmentTable(
                        meta_data=[{"table_id": "tbl-1"}],
                        description="Attachment table",
                        columns_names=["Service", "Amount", "SupplyDate"],
                        columns_format=["txt", "decimal", "date"],
                        rows=[
                            ["Consulting", "100.00", "2026-04-03"],
                            ["Support", "50.00", "2026-04-04"],
                        ],
                    )
                ],
            )
        ]
    )


def test_attachment_to_spec_maps_column_names_and_summary() -> None:
    output = to_spec(make_attachment())

    assert isinstance(output, FakturaZalacznik)
    table = output.blok_danych[0].tabela[0]

    assert [column.nkom.value for column in table.tnaglowek.kol] == [
        "Service",
        "Amount",
        "SupplyDate",
    ]
    assert [column.typ for column in table.tnaglowek.kol] == [
        FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.TXT,
        FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.DEC,
        FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.DATE,
    ]
    assert table.suma is not None
    assert table.suma.skom == ["-", "150.00", "-"]


def test_attachment_to_spec_falls_back_to_placeholder_column_names() -> None:
    attachment = Attachment(
        data_blocks=[
            DataBlock(
                tables=[
                    AttachmentTable(
                        columns_format=["txt", "integer"],
                        rows=[["Hosting", "2"]],
                    )
                ]
            )
        ]
    )

    output = to_spec(attachment)
    header_columns = output.blok_danych[0].tabela[0].tnaglowek.kol

    assert [column.nkom.value for column in header_columns] == ["Column 1", "Column 2"]


def test_attachment_from_spec_restores_column_names_and_text() -> None:
    mapped = from_spec(to_spec(make_attachment()))

    assert isinstance(mapped, Attachment)
    block = mapped.data_blocks[0]
    assert block.tables is not None
    table = block.tables[0]

    assert block.paragraphs == ["First paragraph", "Second paragraph"]
    assert table.columns_names == ["Service", "Amount", "SupplyDate"]
    assert table.columns_format == ["txt", "decimal", "date"]
    assert table.summary == ["-", "150.00", "-"]
