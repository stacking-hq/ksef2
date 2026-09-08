import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from ksef2.fa3 import FA3InvoiceBuilder, VatRate

TEST_INVOICE_XML_ENV = "KSEF2_TEST_INVOICE_XML"
TEST_INVOICE_SELLER_NIP_ENV = "KSEF2_TEST_INVOICE_SELLER_NIP"


def load_test_invoice_xml(*, seller_nip: str, buyer_nip: str | None = None) -> bytes:
    """Read a supplied invoice or build a fresh FA(3) invoice for KSeF TEST."""
    path = os.environ.get(TEST_INVOICE_XML_ENV)
    if path:
        return Path(path).expanduser().read_bytes()

    builder = (
        FA3InvoiceBuilder()
        .header(system_info="ksef2 integration tests")
        .seller(
            name="SDK TEST seller",
            tax_id=seller_nip,
            country_code="PL",
            address_line_1="Testowa 1",
        )
        .buyer(
            name="SDK TEST buyer",
            tax_id=buyer_nip,
            country_code="PL",
            address_line_1="Testowa 2",
        )
        .standard()
        .issue_date(date.today())
        .invoice_number(f"SDK-TEST-{uuid4().hex}")
        .rows()
        .add_line(
            name="TEST service",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("10.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
    )
    return builder.to_xml().encode("utf-8")


def invoice_seller_nip(default: str | None = None) -> str:
    seller_nip = os.environ.get(TEST_INVOICE_SELLER_NIP_ENV) or default
    if not seller_nip:
        pytest.skip(f"Set {TEST_INVOICE_SELLER_NIP_ENV} for invoice submission tests.")
    return seller_nip


def invoice_buyer_nip() -> str:
    buyer_nip = os.environ.get("KSEF2_TEST_INVOICE_BUYER_NIP")
    if not buyer_nip:
        pytest.skip("Set KSEF2_TEST_INVOICE_BUYER_NIP for buyer export tests.")
    return buyer_nip
