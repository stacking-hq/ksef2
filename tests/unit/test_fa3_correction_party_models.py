import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3 import (
    CorrectedBuyerEntity,
    CorrectedSellerEntity,
    InvoiceAddress,
)
from ksef2.domain.models.fa3.body import InvoiceType, KsefInvoiceBody, InvoiceRow


def make_polish_address() -> InvoiceAddress:
    return InvoiceAddress(
        country_code="PL",
        address_line_1="Marszalkowska 10/5",
        address_line_2="00-001 Warszawa",
    )


def make_invoice_line() -> InvoiceRow:
    return InvoiceRow(
        name="Consulting service",
        quantity="1",
        unit_price_net="100.00",
        net_amount="100.00",
        vat_rate="23",
        vat_amount="23.00",
    )


def test_corrected_seller_entity_accepts_prefix_and_address() -> None:
    seller = CorrectedSellerEntity(
        vat_prefix="de",
        tax_id="1234567890",
        name="Seller Sp. z o.o.",
        address=make_polish_address(),
    )

    assert seller.vat_prefix == "DE"
    assert seller.tax_id == "1234567890"


def test_corrected_buyer_entity_rejects_no_id_with_identifiers() -> None:
    with pytest.raises(ValidationError, match="no_id cannot be combined"):
        CorrectedBuyerEntity(
            no_id=True,
            tax_id="1234567890",
            name="Buyer Sp. z o.o.",
        )


def test_invoice_body_rejects_correction_parties_on_non_correcting_invoice() -> None:
    with pytest.raises(ValidationError, match="only valid for correcting invoices"):
        KsefInvoiceBody(
            issue_date="2026-03-29",
            invoice_number="FV/1/2026",
            rows=[make_invoice_line()],
            corrected_seller=CorrectedSellerEntity(
                tax_id="1234567890",
                name="Old Seller Sp. z o.o.",
                address=make_polish_address(),
            ),
        )


def test_invoice_body_accepts_correction_parties_on_correcting_invoice() -> None:
    body = KsefInvoiceBody(
        issue_date="2026-03-29",
        invoice_number="FK/1/2026",
        invoice_type=InvoiceType.CORRECTING,
        rows=[make_invoice_line()],
        corrected_invoices=[
            {
                "issue_date": "2026-03-01",
                "invoice_number": "FV/1/2026",
                "ksef_id": "1234567890-20260301-ABCDEF-ABCDEF-FF",
            }
        ],
        corrected_buyers=[
            CorrectedBuyerEntity(
                eu_vat_id="de123456789",
                name="Old Buyer GmbH",
                buyer_id="BUYER-1",
            )
        ],
    )

    assert len(body.corrected_buyers) == 1
    assert body.corrected_buyers[0].eu_vat_id == "DE123456789"
