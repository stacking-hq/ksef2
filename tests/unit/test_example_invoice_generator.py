"""Offline tests for the shared FA(3) generator in ``scripts/examples/_common``.

Every invoice the integration tests submit comes from ``example_invoice_xml``, so
this is where the properties the submission tests rely on are pinned down. They
run without KSeF credentials.
"""

from pathlib import Path

from lxml import etree

from scripts.examples._common import (
    EXAMPLE_INVOICE_NUMBER_PREFIX,
    example_invoice_xml,
)

SELLER_NIP = "5261040828"
SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "FA3" / "schemat.xsd"

_PARSER = etree.XMLParser(no_network=True, resolve_entities=False)


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


def _generated() -> bytes:
    return example_invoice_xml(seller_nip=SELLER_NIP)


def test_invoice_validates_against_the_fa3_xsd() -> None:
    schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH), _PARSER))

    document = etree.fromstring(_generated(), parser=_PARSER)

    schema.assertValid(document)


def test_invoice_is_issued_by_the_requested_seller() -> None:
    document = etree.fromstring(_generated(), parser=_PARSER)

    seller_nip = document.find("{*}Podmiot1/{*}DaneIdentyfikacyjne/{*}NIP")

    assert seller_nip is not None
    assert seller_nip.text == SELLER_NIP


def test_consecutive_invoices_get_different_numbers() -> None:
    """KSeF rejects a repeated seller plus number, so each call must differ.

    Falsified by returning one constant from example_invoice_number: that fails
    here while a whole-document comparison stays green, see _invoice_number.
    """
    first = _invoice_number(_generated())
    second = _invoice_number(_generated())

    assert first != second


def test_generated_numbers_share_the_example_prefix() -> None:
    assert _invoice_number(_generated()).startswith(f"{EXAMPLE_INVOICE_NUMBER_PREFIX}-")


def test_explicit_number_is_used_verbatim() -> None:
    """The batch examples number invoices ``<tag>-<ordinal>``, so honour it."""
    invoice_xml = example_invoice_xml(
        seller_nip=SELLER_NIP,
        invoice_number="BATCH-TAG-01",
    )

    assert _invoice_number(invoice_xml) == "BATCH-TAG-01"
