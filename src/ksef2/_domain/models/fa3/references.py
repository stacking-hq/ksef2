"""FA(3) invoice reference helper models."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import model_validator

from ksef2._domain.models import KSeFBaseModel


class DraftIntent(StrEnum):
    """Invoice intent tracked by serialized FA(3) builder drafts."""

    STANDARD = "VAT"
    CORRECTION = "KOR"
    ADVANCE = "ZAL"
    SETTLEMENT = "ROZ"
    MARGIN = "MARZA"


class CorrectedInvoiceReference(KSeFBaseModel):
    """Reference to an invoice corrected by a correction invoice."""

    issue_date: date
    """Issue date of the corrected invoice."""
    invoice_number: str
    """Number of the corrected invoice."""
    ksef_id: str | None = None
    """KSeF number of the corrected invoice; ``None`` when ``outside_ksef`` is set."""
    outside_ksef: bool = False
    """Marks a corrected invoice that was issued outside KSeF."""

    @model_validator(mode="after")
    def validate_reference(self) -> "CorrectedInvoiceReference":
        """Require exactly one of a KSeF number or the outside-KSeF marker.

        Returns:
            The validated reference.

        Raises:
            ValueError: If ``ksef_id`` and ``outside_ksef`` are used together, or neither is set.
        """
        if self.ksef_id and self.outside_ksef:
            raise ValueError("ksef_id and outside_ksef cannot be used together")
        if not self.ksef_id and not self.outside_ksef:
            raise ValueError("Either ksef_id or outside_ksef=True is required")
        return self


class AdvanceInvoiceReference(KSeFBaseModel):
    """Reference to an advance invoice settled by another invoice."""

    ksef_id: str | None = None
    """KSeF number of the advance invoice; ``None`` when ``outside_ksef`` is set."""
    invoice_number: str | None = None
    """Number of the advance invoice, for invoices issued outside KSeF."""
    outside_ksef: bool = False
    """Marks an advance invoice that was issued outside KSeF."""
    deduction_amount: Decimal | None = None
    """Amount of the advance deducted on this invoice."""
    deduction_reason: str | None = None
    """Reason for the deduction."""

    @model_validator(mode="after")
    def validate_reference(self) -> "AdvanceInvoiceReference":
        """Check that the reference identifies the advance invoice consistently.

        Returns:
            The validated reference.

        Raises:
            ValueError: If ``ksef_id`` is combined with ``invoice_number`` or ``outside_ksef``, an invoice without ``ksef_id`` lacks ``outside_ksef`` or ``invoice_number``, or only one of ``deduction_amount`` and ``deduction_reason`` is set.
        """
        if self.ksef_id and (self.invoice_number or self.outside_ksef):
            raise ValueError(
                "ksef_id cannot be combined with invoice_number/outside_ksef"
            )
        if not self.ksef_id:
            if not self.outside_ksef:
                raise ValueError(
                    "outside_ksef=True is required when advance invoice is not in KSeF"
                )
            if not self.invoice_number:
                raise ValueError(
                    "invoice_number is required for advance invoices outside KSeF"
                )
        if (self.deduction_amount is None) != (self.deduction_reason is None):
            raise ValueError(
                "deduction_amount and deduction_reason must be provided together"
            )
        return self
