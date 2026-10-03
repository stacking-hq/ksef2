"""FA(3) advance-payment and settlement-reference body models."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from pydantic import Field, field_validator, model_validator

from ksef2._domain.models import KSeFBaseModel
from ksef2._domain.models.fa3.references import AdvanceInvoiceReference


def round_pln(value: Decimal) -> Decimal:
    """Round a monetary amount using standard PLN precision."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def round_rate(value: Decimal) -> Decimal:
    """Round an exchange rate to FA(3) precision."""
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


class PartialAdvancePayment(KSeFBaseModel):
    """FA(3) partial advance payment entry.

    References:
        schemat.FakturaFaZaliczkaCzesciowa

    Maps:
        payment_date - p_6_z (date)
        amount - p_15_z (Decimal)
        currency_exchange_rate - kurs_waluty_zw (Decimal)
    """

    payment_date: date = Field(
        description="p_6_z: Date the advance payment was received."
    )
    """Date the advance payment was received (``P_6Z``)."""
    amount: Decimal = Field(
        description="p_15_z: Advance payment amount contributing to invoice total."
    )
    """Amount of the advance payment (``P_15Z``)."""
    currency_exchange_rate: Decimal | None = Field(
        default=None,
        description=(
            "kurs_waluty_zw: Exchange rate used to calculate VAT for the advance payment."
        ),
    )
    """Exchange rate applied to the advance payment (``KursWalutyZW``)."""

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        """Round the advance payment amount to PLN precision.

        Args:
            value: Amount to round.

        Returns:
            The rounded amount.
        """
        return round_pln(value)

    @field_validator("currency_exchange_rate")
    @classmethod
    def validate_currency_exchange_rate(cls, value: Decimal | None) -> Decimal | None:
        """Round the exchange rate to schema precision.

        Args:
            value: Exchange rate to round, or ``None``.

        Returns:
            The rounded rate, or ``None``.
        """
        if value is None:
            return None
        return round_rate(value)


class AdvancePayment(KSeFBaseModel):
    """FA(3) referenced advance invoice entry.

    References:
        schemat.FakturaFaFakturaZaliczkowa

    Maps:
        outside_ksef - nr_kse_fzn (bool)
        invoice_number - nr_fa_zaliczkowej (str)
        ksef_id - nr_kse_ffa_zaliczkowej (str)
    """

    outside_ksef: bool = False
    """Marks an advance invoice that was issued outside KSeF."""
    invoice_number: str | None = None
    """Number of the advance invoice, for invoices issued outside KSeF."""
    ksef_id: str | None = None
    """KSeF number of the advance invoice."""

    @model_validator(mode="after")
    def validate_reference(self) -> "AdvancePayment":
        if self.outside_ksef:
            if self.invoice_number is None:
                raise ValueError(
                    "invoice_number is required when the advance invoice was issued outside KSeF"
                )
            if self.ksef_id is not None:
                raise ValueError(
                    "ksef_id cannot be combined with outside_ksef advance invoice references"
                )
            return self

        if self.ksef_id is None:
            raise ValueError(
                "ksef_id is required when the advance invoice was issued in KSeF"
            )
        if self.invoice_number is not None:
            raise ValueError(
                "invoice_number cannot be combined with in-KSeF advance invoice references"
            )
        return self


class AdvancePaymentInvoiceContext(KSeFBaseModel):
    """FA(3) advance-invoice-specific body data.

    References:
        schemat.FakturaFa

    Maps:
        amount_before_correction - p_15_zk (Decimal)
        currency_exchange_rate_before_correction - kurs_waluty_zk (Decimal)
        advance_partial_payments - zaliczka_czesciowa (list[PartialAdvancePayment])
        advance_invoice_references - faktura_zaliczkowa (list[AdvanceInvoiceReference])
    """

    amount_before_correction: Decimal | None = Field(
        default=None,
        description="p_15_zk: Advance amount or amount due before correction.",
    )
    """Advance amount before correction (``P_15ZK``)."""
    currency_exchange_rate_before_correction: Decimal | None = Field(
        default=None,
        description="kurs_waluty_zk: Exchange rate used before correction.",
    )
    """Exchange rate before correction (``KursWalutyZK``)."""
    advance_partial_payments: list[PartialAdvancePayment] = Field(
        default_factory=list,
        description="zaliczka_czesciowa: Partial advance payments.",
    )
    """Advance payments received (``ZaliczkaCzesciowa``)."""
    advance_invoice_references: list[AdvanceInvoiceReference] = Field(
        default_factory=list,
        description="faktura_zaliczkowa: Referenced advance invoices on settlements.",
    )
    """Advance invoices this invoice settles (``FakturaZaliczkowa``)."""

    @field_validator("amount_before_correction")
    @classmethod
    def validate_amount_before_correction(cls, value: Decimal | None) -> Decimal | None:
        """Round the pre-correction advance amount to PLN precision.

        Args:
            value: Amount to round, or ``None``.

        Returns:
            The rounded amount, or ``None``.
        """
        if value is None:
            return None
        return round_pln(value)

    @field_validator("currency_exchange_rate_before_correction")
    @classmethod
    def validate_rate_before_correction(cls, value: Decimal | None) -> Decimal | None:
        """Round the pre-correction exchange rate to schema precision.

        Args:
            value: Exchange rate to round, or ``None``.

        Returns:
            The rounded rate, or ``None``.
        """
        if value is None:
            return None
        return round_rate(value)
