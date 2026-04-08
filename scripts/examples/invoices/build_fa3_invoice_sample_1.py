from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from lxml import etree

from ksef2.fa3 import FA3InvoiceBuilder, InvoiceSummaryOverrides, VatRate

_MARKER = "pyproject.toml"


def repo_root() -> Path:
    for parent in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (parent / _MARKER).exists():
            return parent
    raise FileNotFoundError("Could not find repo root")


@dataclass
class ExampleConfig:
    output_path: Path = repo_root() / "output" / "fa3_przyklad_1_like.xml"
    schema_path: Path = repo_root() / "schemas" / "FA3" / "schemat.xsd"
    sample_path: Path = (
        repo_root() / "schemas" / "FA3" / "samples" / "FA_3_Przykład_1.xml"
    )


def build_invoice_xml() -> str:
    builder = FA3InvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
            system_info="SamploFaktur",
        )
        .seller(
            name="ABC AGD sp. z o. o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Kwiatowa 1 m. 2",
            address_line_2="00-001 Warszawa",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(
            name="F.H.U. Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Polna 1",
            address_line_2="00-001 Warszawa",
            customer_number="fdfd778343",
            email="jan@kowalski.pl",
            phone="555777999",
        )
    )

    _ = (
        builder.footer()
        .add_information("Kapiał zakładowy 5 000 000")
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    _ = (
        builder.standard()
        .issue_date(date(2026, 2, 15))
        .issue_place("Warszawa")
        .invoice_number("FV2026/02/150")
        .date_of_supply(date(2026, 1, 27))
        .mark_fp()
        .summary_overrides(
            InvoiceSummaryOverrides(
                base_rate_net_total=Decimal("1666.66"),
                base_rate_vat_total=Decimal("383.33"),
                second_reduced_rate_net_total=Decimal("0.95"),
                second_reduced_rate_vat_total=Decimal("0.05"),
                total_gross=Decimal("2051.00"),
            )
        )
        .add_description(
            key="preferowane godziny dowozu",
            value="dni robocze 17:00 - 20:00",
        )
        .rows()
        .add_line(
            name="lodówka Zimnotech mk1",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("1626.01"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339990",
        )
        .add_line(
            name="wniesienie sprzętu",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("40.65"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339991",
        )
        .add_line(
            name="promocja lodówka pełna mleka",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("0.95"),
            vat_rate=VatRate.VAT_5,
            unique_id="aaaa111133339992",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .already_paid(date(2026, 1, 27))
        .done()
        .transaction()
        .add_order(order_date=date(2026, 1, 26), order_number="4354343")
        .done()
        .done()
    )

    return builder.to_xml()


def validate_invoice_xml(xml_path: Path, schema_path: Path) -> None:
    schema = etree.XMLSchema(etree.parse(str(schema_path)))
    xml_doc = etree.parse(str(xml_path))
    if schema.validate(xml_doc):
        return

    raise ValueError(f"Generated FA(3) XML failed XSD validation:\n{schema.error_log}")


def run(config: ExampleConfig) -> Path:
    invoice_xml = build_invoice_xml()
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    _ = config.output_path.write_text(invoice_xml, encoding="utf-8")
    validate_invoice_xml(config.output_path, config.schema_path)
    print(f"Saved FA(3) XML to: {config.output_path}")
    print(f"Validated generated XML against: {config.schema_path}")
    print(f"Reference sample: {config.sample_path}")
    return config.output_path


def main() -> int:
    _ = run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
