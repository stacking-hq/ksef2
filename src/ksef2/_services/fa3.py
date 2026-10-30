"""Parse FA(3) XML into public invoice models."""

import re
from typing import cast

from lxml import etree
from lxml.etree import _Element as Element  # pyright: ignore[reportPrivateUsage]
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers.lxml import LxmlEventHandler

from ksef2._core.exceptions import KSeFValidationError
from ksef2._infra.schema.fa3.validation import load_fa3_schema
from ksef2._infra.mappers.invoices.fa3.construction import xml_mapping

from ksef2._core.paths import reject_path_like_content
from ksef2._core.xml import parse_xml_bytes
from ksef2._domain.models.fa3 import KsefInvoice
from ksef2._infra.mappers.invoices.fa3.spec.invoice import from_spec
from ksef2._infra.schema.fa3.models.schemat import Faktura


def parse_invoice_xml(
    invoice_xml: bytes | str, *, validate: bool = False
) -> KsefInvoice:
    """Parse FA(3) XML content without exposing generated schema types.

    Args:
        invoice_xml: Original XML bytes or a Unicode XML string, including an XML declaration.
        validate: Opt into validation against the bundled FA(3) XSD.

    Returns:
        The public invoice aggregate. Draft business rules are not applied.
        XSD validation is opt-in. This is not a lossless XML representation.

    Raises:
        KSeFArgumentError: If a short string looks like a file path instead of XML content.
        KSeFValidationError: If XML is malformed, uses a DTD, is not FA(3), or
            violates the XSD. Also a ValueError for compatibility. Includes
            actionable hints and schema context, preserving the original cause.
    """
    if isinstance(invoice_xml, str):
        reject_path_like_content(invoice_xml, content_type="XML")
    root: Element | None = None
    try:
        if isinstance(invoice_xml, str):
            declaration = re.compile(
                r'(<\?xml\b[^?]*?\bencoding\s*=\s*)(["\']).*?\2',
                flags=re.IGNORECASE | re.DOTALL,
            )
            invoice_xml = declaration.sub(r'\1"UTF-8"', invoice_xml, count=1)
            xml_bytes = invoice_xml.encode("utf-8")
        else:
            xml_bytes = invoice_xml
        root = parse_xml_bytes(xml_bytes)
        validate_invoice_document(root, validate=validate)
        parser = XmlParser(handler=LxmlEventHandler)
        schema = parser.parse(root, Faktura)
        with xml_mapping():
            return from_spec(schema)
    except KSeFValidationError:
        raise
    except (etree.XMLSyntaxError, ParserError, ValueError) as exc:
        raise KSeFValidationError(
            f"Failed to parse FA(3) invoice XML: {exc}",
            hint="Check XML syntax and encoding. Supply the original invoice XML, without a DTD.",
            field_path="/Faktura",
            detected_schema="FA(3)" if root is not None else None,
            detected_namespace=etree.QName(root).namespace
            if root is not None
            else None,
            local_rule=False,
            accepted_by_ksef=None,
        ) from exc


FA2_NAMESPACE = "http://crd.gov.pl/wzor/2023/06/29/12648/"


def validate_invoice_document(root: Element, *, validate: bool = False) -> None:
    """Check XML safety/version, optionally its XSD, never draft rules."""
    namespace = etree.QName(root).namespace
    detected_schema = (
        "FA(2)"
        if namespace == FA2_NAMESPACE
        else ("FA(3)" if namespace == Faktura.Meta.namespace else None)
    )
    context = dict(
        field_path="/Faktura",
        detected_schema=detected_schema,
        detected_namespace=namespace,
        local_rule=False,
        accepted_by_ksef=None,
    )
    try:
        if cast(etree.DTD | None, root.getroottree().docinfo.internalDTD) is not None:
            raise ValueError("FA(3) invoice XML must not contain a DTD")
        if namespace == FA2_NAMESPACE:
            raise ValueError(
                "FA(2) is unsupported; parsing and rendering support FA(3) only"
            )
        if root.tag != f"{{{Faktura.Meta.namespace}}}Faktura":
            raise ValueError("Expected a Faktura root in the FA(3) namespace")
        if validate:
            load_fa3_schema().assertValid(root)
    except (ValueError, etree.DocumentInvalid) as exc:
        hint = (
            "Use an FA(2)-compatible viewer or the Ministry of Finance FA(2) visualization stylesheet. "
            "Do not change the namespace to FA(3)."
            if detected_schema == "FA(2)"
            else "Check the indicated XML element against the FA(3) XSD. Render the original XML; do not rebuild it as a draft."
        )
        if isinstance(exc, etree.DocumentInvalid):
            entry = getattr(exc.error_log, "last_error", None)
            context["field_path"] = (
                cast(str | None, getattr(entry, "path", None)) or "/Faktura"
            )
        raise KSeFValidationError(
            f"Failed to parse FA(3) invoice XML: {exc}", hint=hint, **context
        ) from exc
