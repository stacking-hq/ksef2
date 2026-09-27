"""Offline tests for the integration invoice fixture in invoice_payload.py.

These run without KSeF credentials: they pin down what the fixture hands to the
submission tests, which is the part that silently no-op'd while the module
skipped on a missing KSEF2_TEST_INVOICE_XML.
"""

from pathlib import Path

import pytest
from lxml import etree

from scripts.examples._common import EXAMPLE_INVOICE_NUMBER_PREFIX
from tests.integration.invoice_payload import (
    TEST_INVOICE_XML_ENV,
    load_test_invoice_xml,
)

SELLER_NIP = "5261040828"
SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "FA3" / "schemat.xsd"

_PARSER = etree.XMLParser(no_network=True, resolve_entities=False)


@pytest.fixture(autouse=True)
def _no_supplied_invoice(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the generated path under test regardless of the developer's shell."""
    _ = monkeypatch.delenv(TEST_INVOICE_XML_ENV, raising=False)


def _invoice_number(invoice_xml: bytes) -> str:
    """Return the parsed ``<P_2>`` value.

    Comparing documents instead of this number proves nothing: every build stamps
    a fresh ``<DataWytworzeniaFa>``, so two invoices sharing one ``<P_2>`` still
    differ as bytes and a whole-document ``!=`` passes with the number pinned.
    """
    document = etree.fromstring(invoice_xml, parser=_PARSER)
    number = document.find("{*}Fa/{*}P_2")
    assert number is not None and number.text
    return number.text


def test_generated_invoice_validates_against_the_fa3_xsd() -> None:
    schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH), _PARSER))

    document = etree.fromstring(
        load_test_invoice_xml(seller_nip=SELLER_NIP), parser=_PARSER
    )

    schema.assertValid(document)


def test_generated_invoice_is_issued_by_the_requested_seller() -> None:
    document = etree.fromstring(
        load_test_invoice_xml(seller_nip=SELLER_NIP), parser=_PARSER
    )

    seller_nip = document.find("{*}Podmiot1/{*}DaneIdentyfikacyjne/{*}NIP")

    assert seller_nip is not None
    assert seller_nip.text == SELLER_NIP


def test_consecutive_invoices_get_different_numbers() -> None:
    """KSeF rejects a repeated seller plus number, so each call must differ.

    Falsified by returning one constant from example_invoice_number: that fails
    here while a whole-document comparison stays green, see the _invoice_number
    docstring.
    """
    first = _invoice_number(load_test_invoice_xml(seller_nip=SELLER_NIP))
    second = _invoice_number(load_test_invoice_xml(seller_nip=SELLER_NIP))

    assert first != second


def test_generated_numbers_share_the_example_prefix() -> None:
    number = _invoice_number(load_test_invoice_xml(seller_nip=SELLER_NIP))

    assert number.startswith(f"{EXAMPLE_INVOICE_NUMBER_PREFIX}-")


def test_supplied_invoice_is_returned_byte_for_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hand-made invoice must reach KSeF exactly as its author wrote it."""
    supplied = tmp_path / "hand-made.xml"
    original = load_test_invoice_xml(seller_nip=SELLER_NIP)
    _ = supplied.write_bytes(original)
    _ = monkeypatch.setenv(TEST_INVOICE_XML_ENV, str(supplied))

    loaded = load_test_invoice_xml(seller_nip="5261040827")

    assert loaded == original
    assert _invoice_number(loaded) == _invoice_number(original)


def test_supplied_invoice_with_a_repeated_number_is_not_rewritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uniqueness is the generated path's job; a supplied file stays untouched."""
    supplied = tmp_path / "fixed.xml"
    _ = supplied.write_bytes(b"<Faktura><Fa><P_2>FIXED-001</P_2></Fa></Faktura>")
    _ = monkeypatch.setenv(TEST_INVOICE_XML_ENV, str(supplied))

    loaded = load_test_invoice_xml(seller_nip=SELLER_NIP)

    assert loaded == supplied.read_bytes()
    assert _invoice_number(loaded) == "FIXED-001"
