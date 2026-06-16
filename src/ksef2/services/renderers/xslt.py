from pathlib import Path
from typing import final

from lxml import etree

from ksef2.core.exceptions import KSeFInvoiceRenderingError
from ksef2.core.xml import parse_xml_bytes, parse_xml_file
from ksef2.infra.schema.fa3 import STYLESHEET_PATH as _DEFAULT_STYLESHEET_PATH

from lxml.etree import _ElementTree as ElementTree, _Element as Element


@final
class InvoiceXSLTRenderer:
    """Render FA3 invoice XML to HTML using the bundled XSLT stylesheet."""

    def __init__(
        self,
        stylesheet_path: str | Path | None = None,
        enable_code_lookups: bool = False,
    ):
        self._stylesheet_path = (
            Path(stylesheet_path) if stylesheet_path else _DEFAULT_STYLESHEET_PATH
        )
        self._enable_code_lookups = enable_code_lookups
        self._transform: etree.XSLT | None = None

    def _get_params(self) -> dict[str, str]:
        xslt_params: dict[str, str] = {}
        if not self._enable_code_lookups:
            xslt_params["nazwy-dla-kodow"] = "false()"
        return xslt_params

    @property
    def stylesheet_path(self) -> Path:
        return self._stylesheet_path

    def _load_transform(self) -> None:
        if self._transform is not None:
            return

        try:
            xslt_doc = parse_xml_file(self._stylesheet_path)
        except (OSError, etree.XMLSyntaxError) as e:
            raise KSeFInvoiceRenderingError(
                f"Failed to parse XSLT stylesheet: {self._stylesheet_path}"
            ) from e

        try:
            self._transform = etree.XSLT(xslt_doc)
        except etree.XSLTParseError as e:
            raise KSeFInvoiceRenderingError(
                f"Failed to compile XSLT stylesheet: {self._stylesheet_path}"
            ) from e

    def _get_transform(self) -> etree.XSLT:
        if self._transform is None:
            self._load_transform()
        assert self._transform is not None  # for type checkers
        return self._transform

    def _render_doc(self, xml_doc: ElementTree | Element) -> str:
        transform = self._get_transform()

        try:
            html_result = transform(xml_doc, **self._get_params())  # pyright: ignore[reportArgumentType]
        except etree.XSLTApplyError as e:
            raise KSeFInvoiceRenderingError(
                "XSLT transformation failed while rendering invoice."
            ) from e

        try:
            return etree.tostring(
                html_result,
                pretty_print=True,
                encoding="unicode",
            )
        except (TypeError, ValueError, etree.SerialisationError) as e:
            raise KSeFInvoiceRenderingError(
                "Failed to serialize transformation result to HTML."
            ) from e

    def render_from_path(self, invoice_xml_path: str | Path) -> str:
        """Render an invoice XML file to HTML.

        Raises:
            FileNotFoundError: If ``invoice_xml_path`` does not exist.
            KSeFInvoiceRenderingError: If the stylesheet or invoice XML cannot be
                parsed, compiled, transformed, or serialized.
        """
        invoice_xml_path = Path(invoice_xml_path)

        if not invoice_xml_path.exists():
            raise FileNotFoundError(f"Invoice XML file not found: {invoice_xml_path}")

        try:
            xml_doc = parse_xml_file(invoice_xml_path)
        except (OSError, etree.XMLSyntaxError) as e:
            raise KSeFInvoiceRenderingError(
                f"Failed to parse invoice XML file: {invoice_xml_path}"
            ) from e

        return self._render_doc(xml_doc)

    def render_from_string(self, invoice_xml: str | bytes) -> str:
        """Render invoice XML content to HTML.

        Raises:
            KSeFInvoiceRenderingError: If the stylesheet or invoice XML cannot be
                parsed, compiled, transformed, or serialized.
        """
        try:
            if isinstance(invoice_xml, str):
                invoice_xml = invoice_xml.encode("utf-8")

            xml_doc = parse_xml_bytes(invoice_xml)
        except etree.XMLSyntaxError as e:
            raise KSeFInvoiceRenderingError(
                "Failed to parse invoice XML string."
            ) from e

        return self._render_doc(xml_doc)

    def render_to_file(
        self,
        invoice_xml_path: str | Path,
        output_html_path: str | Path,
    ) -> Path:
        """Render an invoice XML file and write HTML output to disk.

        Raises:
            FileNotFoundError: If ``invoice_xml_path`` does not exist.
            KSeFInvoiceRenderingError: If rendering fails or the output file cannot be
                written.
        """
        output_html_path = Path(output_html_path)
        output_html_path.parent.mkdir(parents=True, exist_ok=True)

        html = self.render_from_path(invoice_xml_path)

        try:
            _ = output_html_path.write_text(html, encoding="utf-8")
        except OSError as e:
            raise KSeFInvoiceRenderingError(
                f"Failed to write HTML output to: {output_html_path}"
            ) from e

        return output_html_path
