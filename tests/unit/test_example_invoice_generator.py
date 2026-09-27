"""Offline tests for the two FA(3) invoice builders the repository ships.

``example_invoice_xml`` is the shared generator behind the examples and the
integration tests. ``quickstart.build_invoice`` is a deliberate copy of that
chain, because the quickstart has to run when copied out of the repository on its
own. Both are checked here so the copies cannot drift apart unnoticed: an invoice
KSeF rejects still yields a reference number at send time, so nothing else in the
suite would notice.

These run without KSeF credentials.
"""

from pathlib import Path
from typing import Callable

import pytest
from lxml import etree

from scripts.examples._common import (
    EXAMPLE_INVOICE_NUMBER_PREFIX,
    example_invoice_xml,
)
from scripts.examples.quickstart import SELLER_NIP, build_invoice

SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "FA3" / "schemat.xsd"

_PARSER = etree.XMLParser(no_network=True, resolve_entities=False)


@pytest.fixture(params=["shared", "quickstart"])
def generate(request: pytest.FixtureRequest) -> Callable[[str], bytes]:
    """Yield each builder, so a property holds for the copy as well as the original."""
    if request.param == "shared":
        return lambda seller_nip: example_invoice_xml(seller_nip=seller_nip)
    return build_invoice


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


def test_invoice_validates_against_the_fa3_xsd(
    generate: Callable[[str], bytes],
) -> None:
    schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH), _PARSER))

    document = etree.fromstring(generate(SELLER_NIP), parser=_PARSER)

    schema.assertValid(document)


def test_invoice_is_issued_by_the_requested_seller(
    generate: Callable[[str], bytes],
) -> None:
    document = etree.fromstring(generate("5261040827"), parser=_PARSER)

    seller_nip = document.find("{*}Podmiot1/{*}DaneIdentyfikacyjne/{*}NIP")

    assert seller_nip is not None
    assert seller_nip.text == "5261040827"


def test_consecutive_invoices_get_different_numbers(
    generate: Callable[[str], bytes],
) -> None:
    """KSeF rejects a repeated seller plus number, so each call must differ.

    Falsified by returning one constant invoice number: that fails here while a
    whole-document comparison stays green, see _invoice_number.
    """
    first = _invoice_number(generate(SELLER_NIP))
    second = _invoice_number(generate(SELLER_NIP))

    assert first != second


def test_quickstart_is_self_contained() -> None:
    """The quickstart must not lean on the shared helpers it is meant to survive without."""
    source = (
        Path(__file__).parents[2] / "scripts" / "examples" / "quickstart.py"
    ).read_text()

    assert "_common" not in source


def test_shared_generator_honours_an_explicit_number() -> None:
    """The batch examples number invoices ``<tag>-<ordinal>``, so honour it."""
    invoice_xml = example_invoice_xml(
        seller_nip=SELLER_NIP,
        invoice_number=f"{EXAMPLE_INVOICE_NUMBER_PREFIX}-TAG-01",
    )

    assert _invoice_number(invoice_xml) == f"{EXAMPLE_INVOICE_NUMBER_PREFIX}-TAG-01"
