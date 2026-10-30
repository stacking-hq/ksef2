from pathlib import Path
from typing import cast, final

from lxml import etree

from ksef2._core.paths import reject_path_like_content
from ksef2._core.exceptions import KSeFInvoiceRenderingError, KSeFValidationError
from ksef2._services.fa3 import validate_invoice_document
from ksef2._core.xml import parse_xml_bytes, parse_xml_file
from ksef2._infra.schema.fa3 import STYLESHEET_PATH as _DEFAULT_STYLESHEET_PATH

from lxml.etree import _ElementTree as ElementTree, _Element as Element


_CODE_LIST_FILES = {
    "schema-krajow": "KodyKrajow_v10-0E.xsd",
    "schema-urzedow": "KodyUrzedowSkarbowych_v8-0E.xsd",
    "schema-urzedowexwus": "KodyUrzedowSkarbowychExWUS_v8-0E.xsd",
    "schema-naczelnikow-urzedow": "KodyNaczelnikowUrzedowSkarbowych_v4-0E.xsd",
    "schema-walut": "KodyWalut_v1-0E.xsd",
}


@final
class InvoiceXSLTRenderer:
    """Render FA3 invoice XML to HTML using the bundled XSLT stylesheet.

    By default, XSLT ``document()`` reads cannot access local files or the
    network. Enabling code lookups resolves country, currency, tax-office,
    tax-office ex-WUS, and tax-office-head descriptions from bundled XSD files
    offline. It allows read-only local file access; network access and writes
    remain blocked. Use enabled code lookups only with trusted stylesheets and
    invoice XML: either can direct ``document()`` to other local files.
    """

    def __init__(
        self,
        stylesheet_path: str | Path | None = None,
        enable_code_lookups: bool = False,
        *,
        validate: bool = False,
        footer_text: str | None = None,
        watermark_text: str | None = None,
    ):
        """Create the InvoiceXSLTRenderer.

        Args:
            validate: Opt into bundled FA(3) XSD validation when using the default stylesheet.
            stylesheet_path: Path of an XSLT stylesheet to use; the bundled FA(3) stylesheet when ``None``.
            footer_text: Optional plain-text notice appended once after the invoice.
            watermark_text: Optional plain-text watermark, repeated on printed pages.
            enable_code_lookups: Resolve code descriptions offline using bundled XSD files. Allows local file reads, so use only with trusted stylesheets and invoice XML. Network access and writes remain blocked.
        """
        self._footer_text = footer_text
        self._watermark_text = watermark_text
        self._stylesheet_path = (
            Path(stylesheet_path) if stylesheet_path else _DEFAULT_STYLESHEET_PATH
        )
        self._enable_code_lookups = enable_code_lookups
        self._validate = validate
        read_file = enable_code_lookups
        write_file = False
        create_dir = False
        read_network = False
        write_network = False
        xslt_access_options = {
            "read_file": read_file,
            "write_file": write_file,
            "create_dir": create_dir,
            "read_network": read_network,
            "write_network": write_network,
        }
        self._access_control = etree.XSLTAccessControl(**xslt_access_options)
        self._transform: etree.XSLT | None = None

    def _get_params(self) -> dict[str, object]:
        xslt_params: dict[str, object] = {}
        if not self._enable_code_lookups:
            xslt_params["nazwy-dla-kodow"] = "false()"
        else:
            for parameter, filename in _CODE_LIST_FILES.items():
                uri = (_DEFAULT_STYLESHEET_PATH.parent / filename).resolve().as_uri()
                xslt_params[parameter] = etree.XSLT.strparam(uri)
        return xslt_params

    @property
    def stylesheet_path(self) -> Path:
        """Return the stylesheet used for rendering.

        Returns:
            Path of the XSLT stylesheet.
        """
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
            self._transform = etree.XSLT(
                xslt_doc,
                access_control=self._access_control,
            )
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
        if self._stylesheet_path == _DEFAULT_STYLESHEET_PATH:
            root = xml_doc.getroot() if isinstance(xml_doc, ElementTree) else xml_doc
            try:
                validate_invoice_document(root, validate=self._validate)
            except KSeFValidationError as exc:
                raise KSeFInvoiceRenderingError(
                    cast(str, exc.args[0]),
                    **exc.context,
                ) from exc
        transform = self._get_transform()

        try:
            html_result = transform(xml_doc, **self._get_params())  # pyright: ignore[reportArgumentType]
        except etree.XSLTApplyError as e:
            details = str(cast(object, e))
            raise KSeFInvoiceRenderingError(
                f"XSLT transformation failed while rendering invoice: {details}",
                details=details,
            ) from e

        try:
            html_content = etree.tostring(
                html_result,
                pretty_print=True,
                encoding="unicode",
            )
        except (TypeError, ValueError, etree.SerialisationError) as e:
            raise KSeFInvoiceRenderingError(
                "Failed to serialize transformation result to HTML."
            ) from e

        return self._add_notices(html_content)

    def _add_notices(self, html_content: str) -> str:
        if not self._footer_text and not self._watermark_text:
            return html_content
        document = etree.HTML(html_content)
        if document is None:  # pyright: ignore[reportUnnecessaryComparison]
            raise KSeFInvoiceRenderingError("Rendered invoice HTML is empty.")
        body = document.find("body")
        if body is None:
            raise KSeFInvoiceRenderingError("Rendered invoice HTML has no body.")
        if self._watermark_text:
            watermark = etree.Element(
                "div",
                attrib={
                    "class": "ksef2-watermark",
                    "style": "position:fixed;top:40%;left:10%;width:80%;text-align:center;"
                    "font:48pt sans-serif;color:#999;opacity:0.18;transform:rotate(-30deg);"
                    "pointer-events:none;z-index:1000;overflow-wrap:anywhere",
                },
            )
            watermark.text = self._watermark_text
            body.insert(0, watermark)
        if self._footer_text:
            footer = etree.SubElement(
                body,
                "div",
                attrib={
                    "class": "ksef2-footer",
                    "style": "text-align:center;font:9pt sans-serif;margin:4mm;"
                    "break-inside:avoid;overflow-wrap:anywhere",
                },
            )
            footer.text = self._footer_text
        return etree.tostring(document, encoding="unicode", method="html")

    def render_from_path(self, invoice_xml_path: str | Path) -> str:
        """Render an invoice XML file to HTML.

        Args:
            invoice_xml_path: Path of the invoice XML file.

        Returns:
            The rendered HTML.

        Raises:
            FileNotFoundError: If ``invoice_xml_path`` does not exist.
            KSeFInvoiceRenderingError: If the stylesheet or invoice XML cannot be
                parsed, compiled, transformed, or serialized.

        Example:
            ```python
            from ksef2.renderers import InvoiceXSLTRenderer

            html = InvoiceXSLTRenderer().render_from_path("invoice.xml")
            ```
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

        Args:
            invoice_xml: Invoice XML content.

        Returns:
            The rendered HTML.

        Raises:
            KSeFArgumentError: If a short string looks like a file path instead of XML content.
            KSeFInvoiceRenderingError: If the stylesheet or invoice XML cannot be
                parsed, compiled, transformed, or serialized.
        """
        try:
            if isinstance(invoice_xml, str):
                reject_path_like_content(invoice_xml, content_type="XML")
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

        Args:
            invoice_xml_path: Path of the invoice XML file.
            output_html_path: Path to write the HTML to.

        Returns:
            The path of the written HTML file.

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
