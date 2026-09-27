"""Seller selection for the invoice integration tests.

Invoices are built by ``scripts.examples._common.example_invoice_xml``, the
generator the example scripts and these tests share. Submission tests call it
directly with the seller NIP resolved here.
"""

import os

import pytest

TEST_INVOICE_SELLER_NIP_ENV = "KSEF2_TEST_INVOICE_SELLER_NIP"


def invoice_seller_nip(default: str | None = None) -> str:
    seller_nip = os.environ.get(TEST_INVOICE_SELLER_NIP_ENV) or default
    if not seller_nip:
        pytest.skip(f"Set {TEST_INVOICE_SELLER_NIP_ENV} for invoice submission tests.")
    return seller_nip
