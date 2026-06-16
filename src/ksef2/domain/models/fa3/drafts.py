"""Reusable FA(3) draft helper models."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum

from pydantic import field_validator, model_validator

from ksef2.domain.models import KSeFBaseModel


def round_pln(value: Decimal) -> Decimal:
    """Round a monetary amount using standard PLN precision."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class DraftIntent(StrEnum):
    """High-level invoice intent used by draft helpers."""

    STANDARD = "VAT"
    CORRECTION = "KOR"
    ADVANCE = "ZAL"
    SETTLEMENT = "ROZ"
    MARGIN = "MARZA"


class MarginProcedure(StrEnum):
    """Margin procedure variants supported by FA(3) annotations."""

    TRAVEL_AGENCY = "travel_agency"
    USED_GOODS = "used_goods"
    ARTWORKS = "artworks"
    COLLECTIBLES_AND_ANTIQUES = "collectibles_and_antiques"


class CorrectedInvoiceReference(KSeFBaseModel):
    """Reference to an invoice corrected by a correction invoice."""

    issue_date: date
    invoice_number: str
    ksef_id: str | None = None
    outside_ksef: bool = False

    @model_validator(mode="after")
    def validate_reference(self) -> "CorrectedInvoiceReference":
        if self.ksef_id and self.outside_ksef:
            raise ValueError("ksef_id and outside_ksef cannot be used together")
        if not self.ksef_id and not self.outside_ksef:
            raise ValueError("Either ksef_id or outside_ksef=True is required")
        return self


class AdvanceInvoiceReference(KSeFBaseModel):
    """Reference to an advance invoice settled by another invoice."""

    ksef_id: str | None = None
    invoice_number: str | None = None
    outside_ksef: bool = False
    deduction_amount: Decimal | None = None
    deduction_reason: str | None = None

    @model_validator(mode="after")
    def validate_reference(self) -> "AdvanceInvoiceReference":
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


class SettlementCharge(KSeFBaseModel):
    """Additional settlement charge included in a draft invoice."""

    amount: Decimal
    reason: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= Decimal("0.00"):
            raise ValueError("amount must be greater than zero")
        return round_pln(value)


class SettlementDeduction(KSeFBaseModel):
    """Settlement deduction included in a draft invoice."""

    amount: Decimal
    reason: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= Decimal("0.00"):
            raise ValueError("amount must be greater than zero")
        return round_pln(value)
