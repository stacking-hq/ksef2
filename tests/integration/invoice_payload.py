"""FA(3) invoice fixtures for the invoice-submission integration tests.

Invoices are built by ``scripts.examples._common.example_invoice_xml``, the same
generator the example scripts use, so the repository keeps one FA(3) builder call
site. The dependency only points this way: the test layer imports from the
examples layer, which stays self-contained and runnable on its own.
"""

import os
from pathlib import Path

import pytest

from scripts.examples._common import example_invoice_xml

TEST_INVOICE_XML_ENV = "KSEF2_TEST_INVOICE_XML"
TEST_INVOICE_SELLER_NIP_ENV = "KSEF2_TEST_INVOICE_SELLER_NIP"
TEST_INVOICE_BUYER_NIP_ENV = "KSEF2_TEST_INVOICE_BUYER_NIP"


def load_test_invoice_xml(*, seller_nip: str) -> bytes:
    """Return a FA(3) invoice issued by ``seller_nip``.

    A document supplied through ``KSEF2_TEST_INVOICE_XML`` is returned
    byte-for-byte, unchanged, so a hand-made invoice is tested as written. With
    no file configured a fresh invoice is generated: an invoice number is minted
    per call because KSeF identifies an invoice by seller plus ``<P_2>`` and
    rejects a repeat with ``440 Duplikat faktury``, which would make a second
    submission in the same run fail for a reason unrelated to the endpoint under
    test.
    """
    configured_path = os.environ.get(TEST_INVOICE_XML_ENV)
    if configured_path:
        return Path(configured_path).expanduser().read_bytes()

    return example_invoice_xml(seller_nip=seller_nip)


def invoice_seller_nip(default: str | None = None) -> str:
    seller_nip = os.environ.get(TEST_INVOICE_SELLER_NIP_ENV) or default
    if not seller_nip:
        pytest.skip(f"Set {TEST_INVOICE_SELLER_NIP_ENV} for invoice submission tests.")
    return seller_nip


def invoice_buyer_nip() -> str:
    buyer_nip = os.environ.get(TEST_INVOICE_BUYER_NIP_ENV)
    if not buyer_nip:
        pytest.skip(f"Set {TEST_INVOICE_BUYER_NIP_ENV} for buyer export tests.")
    return buyer_nip
