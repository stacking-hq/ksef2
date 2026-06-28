from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from lxml import etree

from ksef2.fa3 import FA3InvoiceBuilder, VatRate
from ksef2.services.renderers import InvoicePDFExporter

_MARKER = "pyproject.toml"


def repo_root() -> Path:
    for parent in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (parent / _MARKER).exists():
            return parent
    raise FileNotFoundError("Could not find repo root")


@dataclass
class ExampleConfig:
    output_path: Path = repo_root() / "output" / "fa3_invoice.xml"
    pdf_output_path: Path = repo_root() / "output" / "fa3_invoice.pdf"
    schema_path: Path = repo_root() / "schemas" / "FA3" / "schemat.xsd"


def build_invoice_builder() -> FA3InvoiceBuilder:
    builder = FA3InvoiceBuilder()
    return (
        builder.header(system_info="ksef2 example builder")
        .seller(
            name="ACME S.A.",
            tax_id="1234567890",
            country_code="PL",
            address_line_1="ul. Przykładowa 123",
            address_line_2="Warszawa",
        )
        .buyer(
            name="XYZ GmbH",
            country_code="DE",
            address_line_1="Unter den Linden 1",
            address_line_2="10115 Berlin",
        )
        .standard()
        .issue_place("Warszawa")
        .issue_date(date(2026, 3, 29))
        .invoice_number("FV/2026/03/0001")
        .billing_period(
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
        )
        .rows()
        .add_line(
            name="Consulting service",
            supply_date=date(2026, 3, 29),
            unit_of_measure="h",
            quantity=Decimal("10"),
            unit_price_net=Decimal("100.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .payment()
        .via("bank_transfer")
        .due_on(date(2026, 4, 12))
        .bank_account("PL10101010101010101010101010")
        .done()
        .annotations()
        .split_payment()
        .done()
        .done()
    )


def validate_invoice_xml(xml_path: Path, schema_path: Path) -> None:
    schema = etree.XMLSchema(etree.parse(str(schema_path)))
    xml_doc = etree.parse(str(xml_path))
    if schema.validate(xml_doc):
        return

    raise ValueError(f"Generated FA(3) XML failed XSD validation:\n{schema.error_log}")


def export_invoice_pdf(xml_path: Path, pdf_output_path: Path) -> Path:
    pdf_exporter = InvoicePDFExporter()
    return pdf_exporter.export_to_file(xml_path, pdf_output_path)


def run(config: ExampleConfig) -> tuple[Path, Path]:
    invoice_xml = build_invoice_builder().to_xml()
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    _ = config.output_path.write_text(invoice_xml, encoding="utf-8")
    validate_invoice_xml(config.output_path, config.schema_path)
    exported_pdf_path = export_invoice_pdf(config.output_path, config.pdf_output_path)
    print(f"Saved FA(3) invoice XML to: {config.output_path}")
    print(f"Validated FA(3) invoice XML against: {config.schema_path}")
    print(f"Saved FA(3) invoice PDF to: {exported_pdf_path}")
    return config.output_path, exported_pdf_path


def main() -> int:
    _ = run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
