"""Seller and buyer selection for the invoice integration tests.

The invoices themselves are built by
``scripts.examples._common.example_invoice_xml``, the generator the example
scripts use, so the repository keeps one FA(3) builder call site. Submission
tests call that generator directly with the seller NIP resolved here.
"""

import os

import pytest

TEST_INVOICE_SELLER_NIP_ENV = "KSEF2_TEST_INVOICE_SELLER_NIP"
TEST_INVOICE_BUYER_NIP_ENV = "KSEF2_TEST_INVOICE_BUYER_NIP"


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
