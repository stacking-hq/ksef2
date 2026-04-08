"""Mappings between FA(3) attachment domain models and generated schema models."""

from collections.abc import Sequence
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3.attachment import (
    Attachment,
    AttachmentTable,
    DataBlock,
    ValueType,
)
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaZalacznik,
    FakturaZalacznikBlokDanych,
    FakturaZalacznikBlokDanychMetaDane,
    FakturaZalacznikBlokDanychTabela,
    FakturaZalacznikBlokDanychTabelaSuma,
    FakturaZalacznikBlokDanychTabelaTmetaDane,
    FakturaZalacznikBlokDanychTabelaTnaglowek,
    FakturaZalacznikBlokDanychTabelaTnaglowekKol,
    FakturaZalacznikBlokDanychTabelaTnaglowekKolNkom,
    FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp,
    FakturaZalacznikBlokDanychTabelaWiersz,
    FakturaZalacznikBlokDanychTekst,
)


def _to_spec_meta_data(
    meta_data: Sequence[dict[str, str]] | None,
) -> list[FakturaZalacznikBlokDanychMetaDane]:
    if not meta_data:
        return []

    items: list[FakturaZalacznikBlokDanychMetaDane] = []
    for entry in meta_data:
        for key, value in entry.items():
            items.append(
                FakturaZalacznikBlokDanychMetaDane(
                    zklucz=key,
                    zwartosc=value,
                )
            )
    return items


def _to_spec_table_meta_data(
    meta_data: list[dict[str, str]] | None,
) -> list[FakturaZalacznikBlokDanychTabelaTmetaDane]:
    if not meta_data:
        return []

    items: list[FakturaZalacznikBlokDanychTabelaTmetaDane] = []
    for entry in meta_data:
        for key, value in entry.items():
            items.append(
                FakturaZalacznikBlokDanychTabelaTmetaDane(
                    tklucz=key,
                    twartosc=value,
                )
            )
    return items


def _to_spec_column_name(index: int, column_names: list[str] | None) -> str:
    if column_names is None:
        return f"Column {index}"
    return column_names[index - 1]


def _to_spec_column_type(
    value: ValueType,
) -> FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp:
    value_type_map: dict[ValueType, FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp] = {
        "date": FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.DATE,
        "datetime": FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.DATETIME,
        "decimal": FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.DEC,
        "integer": FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.INT,
        "time": FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.TIME,
        "txt": FakturaZalacznikBlokDanychTabelaTnaglowekKolTyp.TXT,
    }
    return value_type_map[value]


@overload
def to_spec(request: Attachment) -> FakturaZalacznik: ...


@overload
def to_spec(request: DataBlock) -> FakturaZalacznikBlokDanych: ...


@overload
def to_spec(request: AttachmentTable) -> FakturaZalacznikBlokDanychTabela: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert an attachment domain model into the FA(3) attachment schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: Attachment) -> FakturaZalacznik:
    data_blocks = [to_spec(block) for block in request.data_blocks]

    return FakturaZalacznik(blok_danych=data_blocks)


@_to_spec.register
def _(request: DataBlock) -> FakturaZalacznikBlokDanych:
    text = (
        FakturaZalacznikBlokDanychTekst(akapit=list(request.paragraphs))
        if request.paragraphs
        else None
    )
    tables = [to_spec(table) for table in request.tables] if request.tables else []

    return FakturaZalacznikBlokDanych(
        znaglowek=request.header,
        meta_dane=_to_spec_meta_data(request.meta_data),
        tekst=text,
        tabela=tables,
    )


@_to_spec.register
def _(request: AttachmentTable) -> FakturaZalacznikBlokDanychTabela:
    columns = [
        FakturaZalacznikBlokDanychTabelaTnaglowekKol(
            nkom=FakturaZalacznikBlokDanychTabelaTnaglowekKolNkom(
                value=_to_spec_column_name(index, request.columns_names)
            ),
            typ=_to_spec_column_type(column_type),
        )
        for index, column_type in enumerate(request.columns_format, start=1)
    ]
    rows = [
        FakturaZalacznikBlokDanychTabelaWiersz(wkom=list(row)) for row in request.rows
    ]
    summary = (
        FakturaZalacznikBlokDanychTabelaSuma(skom=list(request.summary))
        if request.summary
        else None
    )

    return FakturaZalacznikBlokDanychTabela(
        tmeta_dane=_to_spec_table_meta_data(request.meta_data),
        opis=request.description,
        tnaglowek=FakturaZalacznikBlokDanychTabelaTnaglowek(kol=columns),
        wiersz=rows,
        suma=summary,
    )


def _from_spec_column_type(value: str) -> ValueType:
    column_type_map: dict[str, ValueType] = {
        "date": "date",
        "datetime": "datetime",
        "dec": "decimal",
        "int": "integer",
        "time": "time",
        "txt": "txt",
    }
    return column_type_map[value]


def _from_spec_meta_data(
    meta_data: Sequence[FakturaZalacznikBlokDanychMetaDane],
) -> list[dict[str, str]]:
    return [{entry.zklucz: entry.zwartosc} for entry in meta_data]


def _from_spec_table_meta_data(
    meta_data: Sequence[FakturaZalacznikBlokDanychTabelaTmetaDane],
) -> list[dict[str, str]]:
    return [{entry.tklucz: entry.twartosc} for entry in meta_data]


@overload
def from_spec(schema: FakturaZalacznik) -> Attachment: ...


@overload
def from_spec(schema: FakturaZalacznikBlokDanych) -> DataBlock: ...


@overload
def from_spec(schema: FakturaZalacznikBlokDanychTabela) -> AttachmentTable: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert an FA(3) attachment schema model into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: FakturaZalacznik) -> Attachment:
    data_blocks = [from_spec(block) for block in schema.blok_danych]

    return Attachment(data_blocks=data_blocks)


@_from_spec.register
def _(schema: FakturaZalacznikBlokDanych) -> DataBlock:
    meta_data = _from_spec_meta_data(schema.meta_dane) if schema.meta_dane else None
    paragraphs = list(schema.tekst.akapit) if schema.tekst else None
    tables = [from_spec(table) for table in schema.tabela] if schema.tabela else None

    return DataBlock(
        header=schema.znaglowek,
        meta_data=meta_data,
        paragraphs=paragraphs,
        tables=tables,
    )


@_from_spec.register
def _(schema: FakturaZalacznikBlokDanychTabela) -> AttachmentTable:
    meta_data = (
        _from_spec_table_meta_data(schema.tmeta_dane) if schema.tmeta_dane else []
    )
    columns_names = [column.nkom.value for column in schema.tnaglowek.kol]
    columns_format = [
        _from_spec_column_type(column.typ.value) for column in schema.tnaglowek.kol
    ]
    rows = [list(row.wkom) for row in schema.wiersz]
    summary = list(schema.suma.skom) if schema.suma else None

    return AttachmentTable(
        meta_data=meta_data,
        description=schema.opis,
        columns_names=columns_names,
        columns_format=columns_format,
        rows=rows,
        summary=summary,
    )
