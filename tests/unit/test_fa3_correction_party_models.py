from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3 import (
    AdvanceInvoiceReference,
    CorrectedBuyerEntity,
    CorrectedInvoiceReference,
    CorrectedSellerEntity,
    InvoiceAddress,
)
from ksef2.domain.models.fa3.body import (
    AdvancePaymentInvoiceContext,
    CorrectionInvoiceContext,
    InvoiceType,
    KsefInvoiceBody,
    InvoiceRow,
    VatRate,
)


def make_polish_address() -> InvoiceAddress:
    return InvoiceAddress(
        country_code="PL",
        address_line_1="Marszalkowska 10/5",
        address_line_2="00-001 Warszawa",
    )


def make_invoice_line() -> InvoiceRow:
    return InvoiceRow(
        name="Consulting service",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        net_amount=Decimal("100.00"),
        vat_rate=VatRate.VAT_23,
        vat_amount=Decimal("23.00"),
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
            issue_date=date(2026, 3, 29),
            issue_place=None,
            invoice_number="FV/1/2026",
            rows=[make_invoice_line()],
            correction=CorrectionInvoiceContext(
                corrected_seller=CorrectedSellerEntity(
                    tax_id="1234567890",
                    name="Old Seller Sp. z o.o.",
                    address=make_polish_address(),
                ),
            ),
        )


def test_invoice_body_rejects_correction_context_on_non_correcting_invoice() -> None:
    with pytest.raises(ValidationError, match="correction is only valid"):
        KsefInvoiceBody(
            issue_date=date(2026, 3, 29),
            issue_place=None,
            invoice_number="FV/1/2026",
            rows=[make_invoice_line()],
            correction=CorrectionInvoiceContext(
                correction_reason="Should not be here",
            ),
        )


def test_invoice_body_accepts_correction_parties_on_correcting_invoice() -> None:
    body = KsefInvoiceBody(
        issue_date=date(2026, 3, 29),
        issue_place=None,
        invoice_number="FK/1/2026",
        invoice_type=InvoiceType.CORRECTING,
        rows=[make_invoice_line()],
        correction=CorrectionInvoiceContext(
            correction_effect_type="correction_issue_date",
            corrected_invoice_period="2026-03",
            corrected_invoice_number_override="FV/1/2026/CORR",
            corrected_invoices=[
                CorrectedInvoiceReference(
                    issue_date=date(2026, 3, 1),
                    invoice_number="FV/1/2026",
                    ksef_id="1234567890-20260301-ABCDEF-ABCDEF-FF",
                )
            ],
            corrected_buyers=[
                CorrectedBuyerEntity(
                    eu_vat_id="de123456789",
                    name="Old Buyer GmbH",
                    buyer_id="BUYER-1",
                )
            ],
        ),
    )

    assert body.correction is not None
    assert body.correction.correction_effect_type == "correction_issue_date"
    assert body.correction.corrected_invoice_period == "2026-03"
    assert body.correction.corrected_invoice_number_override == "FV/1/2026/CORR"
    assert len(body.correction.corrected_buyers) == 1
    assert body.correction.corrected_buyers[0].eu_vat_id == "DE123456789"


def test_invoice_body_accepts_advance_context() -> None:
    body = KsefInvoiceBody(
        issue_date=date(2026, 3, 29),
        issue_place=None,
        invoice_number="FR/1/2026",
        invoice_type=InvoiceType.ROZ,
        rows=[make_invoice_line()],
        advance=AdvancePaymentInvoiceContext(
            amount_before_correction=Decimal("1500.45"),
            currency_exchange_rate_before_correction=Decimal("4.501234"),
            advance_invoice_references=[
                AdvanceInvoiceReference(
                    ksef_id="1234567890-20260301-ABCDEF-ABCDEF-FF",
                    deduction_amount=Decimal("500.00"),
                    deduction_reason="Rozliczenie faktury zaliczkowej nr 1",
                )
            ],
        ),
    )

    assert body.advance is not None
    assert str(body.advance.amount_before_correction) == "1500.45"
    assert str(body.advance.currency_exchange_rate_before_correction) == "4.501234"
    assert len(body.advance.advance_invoice_references) == 1


def test_invoice_body_rejects_advance_context_on_standard_invoice() -> None:
    with pytest.raises(ValidationError, match="advance is only valid"):
        KsefInvoiceBody(
            issue_date=date(2026, 3, 29),
            issue_place=None,
            invoice_number="FV/1/2026",
            rows=[make_invoice_line()],
            advance=AdvancePaymentInvoiceContext(
                amount_before_correction=Decimal("1500.45"),
            ),
        )
