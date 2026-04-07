from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from ksef2.domain.models.fa3 import (
    AdvanceInvoiceReference,
    CorrectedInvoiceReference,
    MarginProcedure,
)
from ksef2.services.builders.fa3.advance import AdvanceInvoiceBuilder
from ksef2.services.builders.fa3.base import BaseFA3Builder
from ksef2.services.builders.fa3.correction_advance import (
    CorrectionAdvanceInvoiceBuilder,
)
from ksef2.services.builders.fa3.correction import CorrectionInvoiceBuilder
from ksef2.services.builders.fa3.correction_settlement import (
    CorrectionSettlementInvoiceBuilder,
)
from ksef2.services.builders.fa3.margin import MarginInvoiceBuilder
from ksef2.services.builders.fa3.settlement import SettlementInvoiceBuilder
from ksef2.services.builders.fa3.simplified import SimplifiedInvoiceBuilder
from ksef2.services.builders.fa3.standard import StandardInvoiceBuilder


class FA3InvoiceBuilder(StandardInvoiceBuilder):
    """Backward-compatible entry point for standard FA(3) invoices."""

    @classmethod
    def standard(cls) -> StandardInvoiceBuilder:
        return StandardInvoiceBuilder()

    @classmethod
    def correction(
        cls,
        *,
        corrected_invoice_number: str | None = None,
        corrected_issue_date: date | None = None,
        corrected_ksef_id: str | None = None,
        corrected_outside_ksef: bool = False,
        correction_reason: str | None = None,
    ) -> CorrectionInvoiceBuilder:
        corrected_invoices = None
        if (
            corrected_invoice_number is not None
            or corrected_issue_date is not None
            or corrected_ksef_id is not None
            or corrected_outside_ksef
        ):
            if corrected_invoice_number is None or corrected_issue_date is None:
                raise ValueError(
                    "corrected_invoice_number and corrected_issue_date are required"
                )
            corrected_invoices = [
                CorrectedInvoiceReference(
                    issue_date=corrected_issue_date,
                    invoice_number=corrected_invoice_number,
                    ksef_id=corrected_ksef_id,
                    outside_ksef=corrected_outside_ksef,
                )
            ]
        return CorrectionInvoiceBuilder(
            corrected_invoices=corrected_invoices,
            correction_reason=correction_reason,
        )

    @classmethod
    def advance(cls, *, gross_advance_amount: Decimal) -> AdvanceInvoiceBuilder:
        return AdvanceInvoiceBuilder(gross_advance_amount=gross_advance_amount)

    @classmethod
    def settlement(
        cls, *, advance_invoice_references: Sequence[AdvanceInvoiceReference]
    ) -> SettlementInvoiceBuilder:
        return SettlementInvoiceBuilder(
            advance_invoice_references=advance_invoice_references
        )

    @classmethod
    def margin(cls, *, margin_procedure: MarginProcedure | str) -> MarginInvoiceBuilder:
        return MarginInvoiceBuilder(margin_procedure=margin_procedure)

    @classmethod
    def simplified(cls) -> SimplifiedInvoiceBuilder:
        return SimplifiedInvoiceBuilder()

    @classmethod
    def correction_advance(
        cls,
        *,
        gross_advance_amount: Decimal,
        corrected_invoices: Sequence[CorrectedInvoiceReference] | None = None,
        correction_reason: str | None = None,
    ) -> CorrectionAdvanceInvoiceBuilder:
        return CorrectionAdvanceInvoiceBuilder(
            gross_advance_amount=gross_advance_amount,
            corrected_invoices=corrected_invoices,
            correction_reason=correction_reason,
        )

    @classmethod
    def correction_settlement(
        cls,
        *,
        advance_invoice_references: Sequence[AdvanceInvoiceReference],
        corrected_invoices: Sequence[CorrectedInvoiceReference] | None = None,
        correction_reason: str | None = None,
    ) -> CorrectionSettlementInvoiceBuilder:
        return CorrectionSettlementInvoiceBuilder(
            advance_invoice_references=advance_invoice_references,
            corrected_invoices=corrected_invoices,
            correction_reason=correction_reason,
        )


__all__ = [
    "AdvanceInvoiceBuilder",
    "BaseFA3Builder",
    "CorrectionAdvanceInvoiceBuilder",
    "CorrectionInvoiceBuilder",
    "CorrectionSettlementInvoiceBuilder",
    "FA3InvoiceBuilder",
    "MarginInvoiceBuilder",
    "SettlementInvoiceBuilder",
    "SimplifiedInvoiceBuilder",
    "StandardInvoiceBuilder",
]
