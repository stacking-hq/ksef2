from pathlib import Path

from lxml import etree
from lxml.etree import _Element as Element, _ElementTree as ElementTree


def secure_xml_parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        recover=False,
    )


def parse_xml_bytes(xml_bytes: bytes) -> Element:
    return etree.fromstring(xml_bytes, parser=secure_xml_parser())


def parse_xml_file(path: str | Path) -> ElementTree:
    return etree.parse(str(path), parser=secure_xml_parser())
