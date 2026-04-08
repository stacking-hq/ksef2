from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from lxml import etree
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from ksef2.domain.models.fa3 import KsefInvoice
from ksef2.domain.models.fa3.body import VatRate
from ksef2.infra.mappers.invoices.fa3.domain.invoice import to_spec as invoice_to_spec
from ksef2.infra.schema.fa3.models.schemat import __NAMESPACE__
from ksef2.services import FA3InvoiceBuilder
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


def build_invoice() -> KsefInvoice:
    return (
        FA3InvoiceBuilder()
        .header(system_info="ksef2 example builder")
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
        .add_line(
            name="Consulting service",
            supply_date=date(2026, 3, 29),
            unit_of_measure="h",
            quantity=Decimal("10"),
            unit_price_net=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            net_amount=Decimal("1000.00"),
            vat_rate=VatRate.VAT_23,
        )
        .body(
            issue_place="Warszawa",
            issue_date=date(2026, 3, 29),
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
        )
        .build()
    )


def render_invoice_xml(invoice: KsefInvoice) -> str:
    serializer = XmlSerializer(
        config=SerializerConfig(
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )
    )
    return serializer.render(
        invoice_to_spec(invoice),
        ns_map={None: __NAMESPACE__},
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
    invoice_xml = render_invoice_xml(build_invoice())
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(invoice_xml, encoding="utf-8")
    validate_invoice_xml(config.output_path, config.schema_path)
    exported_pdf_path = export_invoice_pdf(config.output_path, config.pdf_output_path)
    print(f"Saved FA(3) invoice XML to: {config.output_path}")
    print(f"Validated FA(3) invoice XML against: {config.schema_path}")
    print(f"Saved FA(3) invoice PDF to: {exported_pdf_path}")
    return config.output_path, exported_pdf_path


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
