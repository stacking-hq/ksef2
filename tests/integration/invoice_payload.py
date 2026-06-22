import os
from pathlib import Path

import pytest

TEST_INVOICE_XML_ENV = "KSEF2_TEST_INVOICE_XML"
TEST_INVOICE_SELLER_NIP_ENV = "KSEF2_TEST_INVOICE_SELLER_NIP"
TEST_INVOICE_BUYER_NIP_ENV = "KSEF2_TEST_INVOICE_BUYER_NIP"


def load_test_invoice_xml() -> bytes:
    path = os.environ.get(TEST_INVOICE_XML_ENV)
    if not path:
        pytest.skip(
            f"Set {TEST_INVOICE_XML_ENV} to a FA(3) XML file valid for the test seller."
        )
    return Path(path).expanduser().read_bytes()


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
