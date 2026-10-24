"""PDF exporter for FA3 invoices using XSLT transformation and WeasyPrint."""

from base64 import b64encode, urlsafe_b64encode
from enum import StrEnum
from hashlib import sha256
from html import escape
from importlib import import_module
from io import BytesIO
from pathlib import Path
import re
from typing import Any, final

from lxml import etree

from ksef2._config import Environment
from ksef2._core import exceptions
from ksef2._services.fa3 import parse_invoice_xml

from ksef2._services.renderers.xslt import InvoiceXSLTRenderer
from ksef2._infra.schema.fa3 import DEFAULT_CSS_OVERRIDES


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


class PDFPageSize(StrEnum):
    """Supported PDF paper sizes and orientations."""

    A4 = "A4 portrait"
    A4_LANDSCAPE = "A4 landscape"
    A3 = "A3 portrait"
    A3_LANDSCAPE = "A3 landscape"
    LETTER = "letter portrait"
    LETTER_LANDSCAPE = "letter landscape"


@final
class InvoicePDFExporter:
    """Export FA3 invoice XML to PDF through XSLT and WeasyPrint."""

    def __init__(
        self,
        stylesheet_path: str | Path | None = None,
        enable_code_lookups: bool = False,
        html_overrides: str | None = None,
        *,
        page_size: PDFPageSize | None = None,
        verification_environment: Environment = Environment.PRODUCTION,
    ):
        """Create a PDF exporter.

        Args:
            stylesheet_path: Path of an XSLT stylesheet to use; the bundled FA(3) stylesheet when ``None``.
            enable_code_lookups: Allow the stylesheet to read local files and the network to resolve code descriptions. Use only with trusted stylesheets.
            html_overrides: CSS applied before PDF conversion; ``None`` uses the bundled defaults.
            page_size: Paper size and orientation; ``None`` preserves the stylesheet setting, normally A4 landscape. Overrides page size in ``html_overrides``.
            verification_environment: KSeF environment used for verification QR links. QR output is enabled per export by supplying ``ksef_number``.

        Raises:
            ImportError: If optional PDF dependencies are not installed.
        """
        self._page_size = PDFPageSize(page_size) if page_size is not None else None
        self._verification_environment = Environment(verification_environment)
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
        """Return the path to the XSL stylesheet being used.

        Returns:
            The path to the XSL stylesheet being used.
        """
        return self._xslt_renderer.stylesheet_path

    def _render_html(
        self, html_content: str, invoice_xml: bytes, ksef_number: str | None
    ) -> bytes:
        if ksef_number is not None:
            if not ksef_number.strip():
                raise ValueError("ksef_number must not be empty")
            invoice = parse_invoice_xml(invoice_xml)
            hosts = {
                Environment.PRODUCTION: "https://qr.ksef.mf.gov.pl",
                Environment.TEST: "https://qr-test.ksef.mf.gov.pl",
                Environment.DEMO: "https://qr-demo.ksef.mf.gov.pl",
            }
            digest = (
                urlsafe_b64encode(sha256(invoice_xml).digest())
                .decode("ascii")
                .rstrip("=")
            )
            issue_date = invoice.body.issue_date.strftime("%d-%m-%Y")
            url = f"{hosts[self._verification_environment]}/invoice/{invoice.seller.tax_id}/{issue_date}/{digest}"
            # Optional PDF dependency, loaded only when QR output is requested.
            segno = import_module("segno")
            svg = BytesIO()
            segno.make_qr(url, error="m").save(svg, kind="svg", scale=4, border=4)  # pyright: ignore[reportAny]
            image_url = "data:image/svg+xml;base64," + b64encode(svg.getvalue()).decode(
                "ascii"
            )
            document = etree.HTML(html_content)
            if document is None:  # pyright: ignore[reportUnnecessaryComparison]
                raise ValueError("Rendered invoice HTML is empty")
            body = document.find("body")
            if body is None:
                raise ValueError(
                    "Rendered invoice HTML has no body for verification QR"
                )
            body.append(
                etree.fromstring(
                    '<div style="text-align:center;break-inside:avoid;margin:8mm">'
                    f'<a href="{escape(url, quote=True)}">'
                    f'<img src="{image_url}" alt="KSeF QR" style="width:35mm;height:35mm" /></a>'
                    f"<div>{escape(ksef_number)}</div></div>"
                )
            )
            html_content = etree.tostring(document, encoding="unicode", method="html")
        css = self._html_overrides
        if self._page_size is not None:
            css += f"\n@page {{ size: {self._page_size.value}; }}"
        stylesheets = [self._weasyprint.CSS(string=css)]

        pdf_bytes = self._weasyprint.HTML(
            string=html_content, base_url=str(self.stylesheet_path.parent)
        ).write_pdf(stylesheets=stylesheets)

        if pdf_bytes is None:
            raise RuntimeError("Failed to generate PDF document from provided XML.")
        return pdf_bytes

    def export_from_path(
        self, invoice_xml_path: str | Path, *, ksef_number: str | None = None
    ) -> bytes:
        """Render an invoice XML file to PDF bytes.

        Args:
            invoice_xml_path: Path of the invoice XML file.
            ksef_number: Assigned KSeF number to display below a verification QR. ``None`` omits the QR. Supports accepted invoices only, not offline certificate QR signing.

        Returns:
            The PDF as bytes.

        Raises:
            FileNotFoundError: If ``invoice_xml_path`` does not exist.
            KSeFInvoiceRenderingError: If HTML rendering fails.
            RuntimeError: If WeasyPrint does not return PDF bytes.
            ValueError: If QR output is requested with an empty number or invalid FA(3) XML.
        """
        invoice_xml = Path(invoice_xml_path).read_bytes()
        return self.export_from_string(invoice_xml, ksef_number=ksef_number)

    def export_from_string(
        self, invoice_xml: str | bytes, *, ksef_number: str | None = None
    ) -> bytes:
        """Render invoice XML content to PDF bytes.

        Args:
            invoice_xml: Original invoice XML content. Strings are encoded as UTF-8; use bytes to preserve the hash of the submitted document.
            ksef_number: Assigned KSeF number to display below a verification QR. ``None`` omits the QR. Supports accepted invoices only, not offline certificate QR signing.

        Returns:
            The PDF as bytes.

        Raises:
            KSeFInvoiceRenderingError: If HTML rendering fails.
            RuntimeError: If WeasyPrint does not return PDF bytes.
            ValueError: If QR output is requested with an empty number or invalid FA(3) XML.
        """
        if isinstance(invoice_xml, str):
            invoice_xml = invoice_xml.encode("utf-8")
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        try:
            root = etree.fromstring(invoice_xml, parser)
        except etree.XMLSyntaxError as exc:
            raise exceptions.KSeFValidationError(
                "Invoice XML must have a Faktura root element.",
                hint="Pass a well-formed FA(3) invoice document.",
            ) from exc
        if etree.QName(root).localname != "Faktura":
            raise exceptions.KSeFValidationError(
                "Invoice XML must have a Faktura root element.",
                hint="Pass a FA(3) invoice whose root element is Faktura.",
            )
        if ksef_number is not None:
            if not ksef_number.strip():
                raise exceptions.KSeFArgumentError(
                    "ksef_number must not be empty.",
                    hint="Pass the KSeF number assigned to this accepted invoice.",
                )
            if not re.fullmatch(
                r"\d{10}-\d{8}-[A-Za-z0-9]{12}-[A-Za-z0-9]{2}", ksef_number
            ):
                raise exceptions.KSeFArgumentError(
                    "ksef_number must match the KSeF number format.",
                    hint="Pass a number in NIP-date-12-character-id-2-character-checksum format.",
                )
        html_content = self._xslt_renderer.render_from_string(invoice_xml)
        return self._render_html(html_content, invoice_xml, ksef_number)

    def export_to_file(
        self,
        invoice_xml_path: str | Path,
        output_pdf_path: str | Path,
        *,
        ksef_number: str | None = None,
    ) -> Path:
        """Render an invoice XML file and write PDF output to disk.

        Args:
            invoice_xml_path: Path of the invoice XML file.
            ksef_number: Assigned KSeF number to display below a verification QR. ``None`` omits the QR. Supports accepted invoices only, not offline certificate QR signing.
            output_pdf_path: Path to write the PDF to.

        Returns:
            The path of the written PDF file.

        Raises:
            FileNotFoundError: If ``invoice_xml_path`` does not exist.
            KSeFInvoiceRenderingError: If HTML rendering fails.
            RuntimeError: If WeasyPrint does not return PDF bytes.
            ValueError: If QR output is requested with an empty number or invalid FA(3) XML.
            OSError: If the PDF output file cannot be written.
        """
        output_pdf_path = Path(output_pdf_path)
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        pdf_bytes = self.export_from_path(invoice_xml_path, ksef_number=ksef_number)
        _ = output_pdf_path.write_bytes(pdf_bytes)

        return output_pdf_path
