from pathlib import Path
from xml.etree import ElementTree

import pytest
from lxml import etree

from tests.integration.invoice_payload import load_test_invoice_xml


def test_generated_test_invoices_are_valid_unique_and_match_the_parties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KSEF2_TEST_INVOICE_XML", raising=False)
    invoices = [
        load_test_invoice_xml(seller_nip="5261040828", buyer_nip="5252609987")
        for _ in range(2)
    ]
    schema_path = Path(__file__).parents[2] / "schemas/FA3/schemat.xsd"
    schema = etree.XMLSchema(etree.parse(str(schema_path)))
    for xml in invoices:
        schema.assertValid(etree.fromstring(xml))
        root = ElementTree.fromstring(xml)
        assert (
            root.findtext("{*}Podmiot1/{*}DaneIdentyfikacyjne/{*}NIP") == "5261040828"
        )
        assert (
            root.findtext("{*}Podmiot2/{*}DaneIdentyfikacyjne/{*}NIP") == "5252609987"
        )
    assert invoices[0] != invoices[1]


def test_supplied_test_invoice_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "invoice.xml"
    path.write_bytes(b"caller-supplied invoice")
    monkeypatch.setenv("KSEF2_TEST_INVOICE_XML", str(path))
    assert load_test_invoice_xml(seller_nip="5261040828") == path.read_bytes()
