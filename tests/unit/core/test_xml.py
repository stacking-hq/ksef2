from pathlib import Path

from lxml import etree

from ksef2._core.xml import parse_xml_bytes, parse_xml_file


def test_parse_xml_bytes_does_not_expand_entities() -> None:
    xml = b'<!DOCTYPE foo [ <!ENTITY xxe "EXPLOIT"> ]><root>&xxe;</root>'

    root = parse_xml_bytes(xml)

    assert root.text is None
    assert len(root) == 1
    assert etree.tostring(root) == b"<root>&xxe;</root>"


def test_parse_xml_file_does_not_expand_entities(tmp_path: Path) -> None:
    xml_path = tmp_path / "entity.xml"
    xml_path.write_bytes(
        b'<!DOCTYPE foo [ <!ENTITY xxe "EXPLOIT"> ]><root>&xxe;</root>'
    )

    document = parse_xml_file(xml_path)

    root = document.getroot()
    assert root is not None
    assert root.text is None
    assert len(root) == 1
    assert etree.tostring(root) == b"<root>&xxe;</root>"
