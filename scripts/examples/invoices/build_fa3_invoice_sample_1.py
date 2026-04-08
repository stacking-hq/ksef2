from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ksef2.domain.models.fa3.body.root import InvoiceType
from ksef2.services.builders.fa3.base import BaseFA3Builder
from ksef2.domain.models.fa3 import DraftIntent
from lxml import etree


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

    builder = BaseFA3Builder(
        intent=DraftIntent.STANDARD,
        invoice_type=InvoiceType.VAT,
    )

    invoice = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 1, 0, 0, 0),
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
        .add_description(
            key="preferowane godziny dowozu",
            value="dni robocze 17:00 - 20:00",
        )
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
    config.output_path.write_text(invoice_xml, encoding="utf-8")
    validate_invoice_xml(config.output_path, config.schema_path)
    print(f"Saved FA(3) XML to: {config.output_path}")
    print(f"Validated generated XML against: {config.schema_path}")
    print(f"Reference sample: {config.sample_path}")
    print(
        "Note: generated P_15 is 2050.99 because totals are derived from rounded line values."
    )
    return config.output_path


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
