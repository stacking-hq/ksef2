"""Parse FA(3) XML into public invoice models."""

import re
from typing import cast

from lxml import etree
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers.lxml import LxmlEventHandler

from ksef2._core.xml import parse_xml_bytes
from ksef2._domain.models.fa3 import KsefInvoice
from ksef2._infra.mappers.invoices.fa3.spec.invoice import from_spec
from ksef2._infra.schema.fa3.models.schemat import Faktura


def parse_invoice_xml(invoice_xml: bytes | str) -> KsefInvoice:
    """Parse FA(3) XML content without exposing generated schema types.

    Args:
        invoice_xml: Original XML bytes or a Unicode XML string, including an XML declaration.

    Returns:
        The public invoice aggregate. Domain validation is applied; this is
        not full XSD validation or a lossless XML representation.

    Raises:
        ValueError: If XML is malformed, uses a DTD, is not FA(3), or cannot
            be mapped to a valid invoice. The original cause is preserved.
    """
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
        if cast(etree.DTD | None, root.getroottree().docinfo.internalDTD) is not None:
            raise ValueError("FA(3) invoice XML must not contain a DTD")
        if root.tag != f"{{{Faktura.Meta.namespace}}}Faktura":
            raise ValueError("Expected a Faktura root in the FA(3) namespace")
        parser = XmlParser(handler=LxmlEventHandler)
        schema = parser.parse(root, Faktura)
        return from_spec(schema)
    except (etree.XMLSyntaxError, ParserError, ValueError) as exc:
        raise ValueError(f"Failed to parse FA(3) invoice XML: {exc}") from exc
