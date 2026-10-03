"""FA(3) settlement charge and deduction domain models."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Self

from pydantic import Field, field_validator, model_validator

from ksef2._domain.models import KSeFBaseModel


def round_pln(value: Decimal) -> Decimal:
    """Round a monetary amount using standard PLN precision."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SettlementCharge(KSeFBaseModel):
    """FA(3) settlement charge entry.

    References:
        schemat.FakturaFaRozliczenieObciazenia

    Maps:
        amount - kwota (Decimal)
        reason - powod (str)
    """

    amount: Decimal
    """Amount of the charge."""
    reason: str
    """Reason for the charge."""

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        """Round the charge amount to PLN precision.

        Args:
            value: Amount to round.

        Returns:
            The rounded amount.
        """
        if value < Decimal("0.00"):
            raise ValueError("amount must be non-negative")
        return round_pln(value)


class SettlementDeduction(KSeFBaseModel):
    """FA(3) settlement deduction entry.

    References:
        schemat.FakturaFaRozliczenieOdliczenia

    Maps:
        amount - kwota (Decimal)
        reason - powod (str)
    """

    amount: Decimal
    """Amount of the deduction."""
    reason: str
    """Reason for the deduction."""

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        """Round the deduction amount to PLN precision.

        Args:
            value: Amount to round.

        Returns:
            The rounded amount.
        """
        if value < Decimal("0.00"):
            raise ValueError("amount must be non-negative")
        return round_pln(value)


class InvoiceSettlement(KSeFBaseModel):
    """FA(3) settlement block attached to the invoice body.

    References:
        schemat.FakturaFaRozliczenie

    Maps:
        charges - obciazenia List(FakturaFaRozliczenieObciazenia)
        charges_total - suma_obciazen (Decimal)
        deductions - odliczenia List(FakturaFaRozliczenieOdliczenia)
        deductions_total - suma_odliczen (Decimal)
        amount_due - do_zaplaty (Decimal)
        amount_to_settle - do_rozliczenia (Decimal)
    """

    charges: list[SettlementCharge] = Field(default_factory=list)
    """Additional charges (``Obciazenia``)."""
    charges_total: Decimal | None = None
    """Total of all charges (``SumaObciazen``)."""
    deductions: list[SettlementDeduction] = Field(default_factory=list)
    """Deductions (``Odliczenia``)."""
    deductions_total: Decimal | None = None
    """Total of all deductions (``SumaOdliczen``)."""
    amount_due: Decimal | None = None
    """Amount due (``DoZaplaty``)."""
    amount_to_settle: Decimal | None = None
    """Amount to be settled (``DoRozliczenia``)."""

    @field_validator(
        "charges_total", "deductions_total", "amount_due", "amount_to_settle"
    )
    @classmethod
    def round_optional_amounts(cls, value: Decimal | None) -> Decimal | None:
        """Round settlement totals and balances to PLN precision.

        Args:
            value: Amount to round, or ``None``.

        Returns:
            The rounded amount, or ``None``.
        """
        if value is None:
            return None
        return round_pln(value)

    @model_validator(mode="after")
    def validate_and_populate_totals(self) -> Self:
        """Fill in charge and deduction totals from their entries and check them.

        Returns:
            The validated settlement.

        Raises:
            ValueError: If a given total disagrees with the sum of its entries, or both ``amount_due`` and ``amount_to_settle`` are set.
        """
        computed_charges_total = sum(
            (charge.amount for charge in self.charges),
            start=Decimal("0.00"),
        )
        computed_deductions_total = sum(
            (deduction.amount for deduction in self.deductions),
            start=Decimal("0.00"),
        )

        if (
            self.charges_total is not None
            and self.charges_total != computed_charges_total
        ):
            raise ValueError("charges_total must equal the sum of charges")
        if (
            self.deductions_total is not None
            and self.deductions_total != computed_deductions_total
        ):
            raise ValueError("deductions_total must equal the sum of deductions")
        if self.amount_due is not None and self.amount_to_settle is not None:
            raise ValueError(
                "amount_due and amount_to_settle cannot be provided together"
            )

        if self.charges_total is None:
            self.charges_total = computed_charges_total
        if self.deductions_total is None:
            self.deductions_total = computed_deductions_total

        return self
