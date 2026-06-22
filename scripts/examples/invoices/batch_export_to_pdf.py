"""Render all sample FA3 invoices to HTML and PDF files.

Prerequisites:
- run from the repository checkout so the sample invoice path resolves

What it demonstrates:
- local XSLT rendering to HTML
- local PDF rendering from XML without calling KSeF
"""

from dataclasses import dataclass
from pathlib import Path

from ksef2.services.renderers import InvoicePDFExporter, InvoiceXSLTRenderer
from scripts.examples._common import repo_root


@dataclass
class ExampleConfig:
    source_dir: Path = repo_root() / "schemas" / "FA3" / "samples"
    output_dir: Path = repo_root() / "output" / "pdf_exports"


def run(config: ExampleConfig) -> None:
    print(f"Input directory: {config.source_dir}")
    print(f"Output directory: {config.output_dir}")

    config.output_dir.mkdir(parents=True, exist_ok=True)

    pdf_exporter = InvoicePDFExporter()
    html_exporter = InvoiceXSLTRenderer()

    for path in sorted(config.source_dir.glob("*.xml")):
        print(f"Exporting {path.name}...")

        print("Exporting to HTML...")
        exported_html_path = html_exporter.render_to_file(
            path,
            config.output_dir / f"{path.stem}.html",
        )
        print(f"  Saved to: {exported_html_path}")

        print("Exporting to PDF...")
        exported_pdf_path = pdf_exporter.export_to_file(
            path,
            config.output_dir / f"{path.stem}.pdf",
        )
        print(f"  Saved to: {exported_pdf_path}")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
