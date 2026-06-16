"""PDF exporter for FA3 invoices using XSLT transformation and WeasyPrint."""

from importlib import import_module
from pathlib import Path
from typing import Any, final

from ksef2.services.renderers.xslt import InvoiceXSLTRenderer
from ksef2.infra.schema.fa3 import DEFAULT_CSS_OVERRIDES


def _load_weasyprint() -> Any:
    try:
        return import_module("weasyprint")
    except ModuleNotFoundError as exc:
        if exc.name == "weasyprint":
            raise ImportError(
                "InvoicePDFExporter requires the optional PDF dependencies. "
                "Install them with `pip install 'ksef2[pdf]'` or "
                "`uv add 'ksef2[pdf]'`."
            ) from exc
        raise


@final
class InvoicePDFExporter:
    """Export FA3 invoice XML to PDF through XSLT and WeasyPrint."""

    def __init__(
        self,
        stylesheet_path: str | Path | None = None,
        enable_code_lookups: bool = False,
        html_overrides: str | None = None,
    ):
        """Create a PDF exporter.

        Raises:
            ImportError: If optional PDF dependencies are not installed.
        """
        self._weasyprint = _load_weasyprint()
        self._xslt_renderer = InvoiceXSLTRenderer(
            stylesheet_path=stylesheet_path,
            enable_code_lookups=enable_code_lookups,
        )
        self._html_overrides = (
            html_overrides if html_overrides else DEFAULT_CSS_OVERRIDES
        )

    @property
    def stylesheet_path(self) -> Path:
        """Return the path to the XSL stylesheet being used."""
        return self._xslt_renderer.stylesheet_path

    def _render_html(self, html_content: str) -> bytes:
        stylesheets = [self._weasyprint.CSS(string=self._html_overrides)]

        pdf_bytes = self._weasyprint.HTML(
            string=html_content, base_url=str(self.stylesheet_path.parent)
        ).write_pdf(stylesheets=stylesheets)

        if pdf_bytes is None:
            raise RuntimeError("Failed to generate PDF document from provided XML.")
        return pdf_bytes

    def export_from_path(self, invoice_xml_path: str | Path) -> bytes:
        """Render an invoice XML file to PDF bytes.

        Raises:
            FileNotFoundError: If ``invoice_xml_path`` does not exist.
            KSeFInvoiceRenderingError: If HTML rendering fails.
            RuntimeError: If WeasyPrint does not return PDF bytes.
        """
        html_content = self._xslt_renderer.render_from_path(invoice_xml_path)
        return self._render_html(html_content)

    def export_from_string(self, invoice_xml: str | bytes) -> bytes:
        """Render invoice XML content to PDF bytes.

        Raises:
            KSeFInvoiceRenderingError: If HTML rendering fails.
            RuntimeError: If WeasyPrint does not return PDF bytes.
        """
        html_content = self._xslt_renderer.render_from_string(invoice_xml)
        return self._render_html(html_content)

    def export_to_file(
        self,
        invoice_xml_path: str | Path,
        output_pdf_path: str | Path,
    ) -> Path:
        """Render an invoice XML file and write PDF output to disk.

        Raises:
            FileNotFoundError: If ``invoice_xml_path`` does not exist.
            KSeFInvoiceRenderingError: If HTML rendering fails.
            RuntimeError: If WeasyPrint does not return PDF bytes.
            OSError: If the PDF output file cannot be written.
        """
        output_pdf_path = Path(output_pdf_path)
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        pdf_bytes = self.export_from_path(invoice_xml_path)
        output_pdf_path.write_bytes(pdf_bytes)

        return output_pdf_path
