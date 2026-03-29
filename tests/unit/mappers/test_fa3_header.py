from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from xsdata.models.datatype import XmlDateTime

from ksef2.domain.models.fa3 import InvoiceHeader
from ksef2.infra.mappers.invoices.fa3.header import to_spec as header_to_spec
from ksef2.infra.schema.fa3.models.schemat import (
    TkodFormularza,
    Tnaglowek,
    TnaglowekWariantFormularza,
)


def test_header_to_spec_maps_fa3_header_fields() -> None:
    output = header_to_spec(
        InvoiceHeader(
            generation_timestamp=datetime(2026, 2, 1, 10, 15, 30, tzinfo=timezone.utc),
            system_info="ACME ERP",
        )
    )

    assert isinstance(output, Tnaglowek)
    assert output.kod_formularza.value == TkodFormularza.FA
    assert output.kod_formularza.kod_systemowy == "FA (3)"
    assert output.kod_formularza.wersja_schemy == "1-0E"
    assert output.wariant_formularza == TnaglowekWariantFormularza.VALUE_3
    assert output.data_wytworzenia_fa == XmlDateTime.from_datetime(
        datetime(2026, 2, 1, 10, 15, 30, tzinfo=timezone.utc)
    )
    assert output.system_info == "ACME ERP"


def test_header_to_spec_treats_naive_timestamp_as_warsaw_time() -> None:
    generation_timestamp = datetime(2026, 2, 1, 10, 15, 30)

    output = header_to_spec(
        InvoiceHeader(
            generation_timestamp=generation_timestamp,
            system_info="ACME ERP",
        )
    )

    assert output.data_wytworzenia_fa == XmlDateTime.from_datetime(
        generation_timestamp.replace(tzinfo=ZoneInfo("Europe/Warsaw"))
    )
