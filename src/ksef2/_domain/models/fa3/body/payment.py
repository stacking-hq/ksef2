"""FA(3) payment, terms, and bank-account domain models."""

from datetime import date
from decimal import Decimal
from typing import Self, Literal

from pydantic import Field, model_validator

from ksef2._domain.models import KSeFBaseModel


PaymentForm = Literal[
    "cash", "card", "voucher", "check", "credit", "bank_transfer", "mobile"
]

PartialPaymentStatus = Literal["partial", "final"]

BankOwnAccountType = Literal[
    "purchased_receivables", "factor_collection", "internal_treasury"
]


class PaymentTermDescription(KSeFBaseModel):
    """FA(3) descriptive payment term.

    References:
        schemat.FakturaFaPlatnoscTerminPlatnosciTerminOpis

    Maps:
        quantity - ilosc (int)
        unit - jednostka (str)
        starting_event - zdarzenie_poczatkowe (str)
    """

    quantity: int
    """Length of the term, in ``unit``s."""
    unit: str
    """Unit of the term, such as days or months."""
    starting_event: str
    """Event the term counts from, for example the date of delivery."""


class PaymentTerm(KSeFBaseModel):
    """FA(3) payment term entry.

    References:
        schemat.FakturaFaPlatnoscTerminPlatnosci

    Maps:
        due_date - termin (date)
        due_date_description - termin_opis (FakturaFaPlatnoscTerminPlatnosciTerminOpis)
    """

    due_date: date | None = None
    """Due date of the payment."""
    due_date_description: PaymentTermDescription | None = None
    """Descriptive payment term, as an alternative to ``due_date``."""

    @model_validator(mode="after")
    def validate_term(self) -> Self:
        """Require a due date or a descriptive term.

        Returns:
            The validated payment term.

        Raises:
            ValueError: If neither ``due_date`` nor ``due_date_description`` is set.
        """
        if self.due_date is None and self.due_date_description is None:
            raise ValueError(
                "At least one of due_date or due_date_description must be provided"
            )
        return self


class BankAccount(KSeFBaseModel):
    """FA(3) bank account information used in payment data.

    References:
        schemat.TRachunekBankowy

    Maps:
        account_number - nr_rb (str)
        swift - swift (str)
        own_bank_account_type - rachunek_wlasny_banku (TrachunekWlasnyBanku)
        bank_name - nazwa_banku (str)
        account_description - opis_rachunku (str)
    """

    account_number: str
    """Bank account number (``NrRB``)."""
    swift: str | None = None
    """SWIFT/BIC code of the bank (``SWIFT``)."""
    own_bank_account_type: BankOwnAccountType | None = None
    """Kind of own bank account (``RachunekWlasnyBanku``)."""
    bank_name: str | None = None
    """Name of the bank (``NazwaBanku``)."""
    account_description: str | None = None
    """Free-text description of the account (``OpisRachunku``)."""


class PartialPayment(KSeFBaseModel):
    """FA(3) partial payment entry.

    References:
        schemat.FakturaFaPlatnoscZaplataCzesciowa

    Maps:
        amount - kwota_zaplaty_czesciowej (Decimal)
        payment_date - data_zaplaty_czesciowej (date)
        payment_form - forma_platnosci (TformaPlatnosci)
        other_payment_form - platnosc_inna (bool)
        payment_description - opis_platnosci (str)
    """

    amount: Decimal
    """Amount paid."""
    payment_date: date
    """Date of the payment."""
    payment_form: PaymentForm | None = None
    """Form of payment, such as cash or transfer."""
    other_payment_form: bool = False
    """Marks a payment form not in ``payment_form``; describe it in ``payment_description``."""
    payment_description: str | None = None
    """Description of the other payment form."""


class InvoicePayment(KSeFBaseModel):
    """FA(3) invoice payment details.

    References:
        schemat.FakturaFaPlatnosc

    Maps:
        paid - zaplacono (bool)
        payment_date - data_zaplaty (date)
        partial_payment_status - znacznik_zaplaty_czesciowej (PartialPaymentStatus)
        partial_payments - zaplata_czesciowa List(FakturaFaPlatnoscZaplataCzesciowa)
        payment_terms - termin_platnosci List(FakturaFaPlatnoscTerminPlatnosci)
        payment_form - forma_platnosci (TformaPlatnosci)
        other_payment_form - platnosc_inna (bool)
        payment_description - opis_platnosci (str)
        bank_accounts - rachunek_bankowy List(TRachunekBankowy)
        factor_bank_accounts - rachunek_bankowy_faktora List(TRachunekBankowy)
        discount - skonto (FakturaFaPlatnoscSkonto)
        discount_terms - warunki_skonta (FakturaFaPlatnoscSkonto)
        discount_amount - wysokosc_skonta (FakturaFaPlatnoscSkonto)
        payment_link - link_do_platnosci (str)
        ipksef - ipkse_f (str)
    """

    paid: bool = False
    """Whether the invoice has been paid in full (``Zaplacono``)."""
    payment_date: date | None = None
    """Date the invoice was paid (``DataZaplaty``)."""
    partial_payment_status: PartialPaymentStatus | None = None
    """Whether the invoice was partially paid (``ZnacznikZaplatyCzesciowej``)."""
    partial_payments: list[PartialPayment] = Field(default_factory=list)
    """Partial payments received."""
    payment_terms: list[PaymentTerm] = Field(default_factory=list)
    """Payment terms (``TerminPlatnosci``)."""
    payment_form: PaymentForm | None = None
    """Form of payment (``FormaPlatnosci``), such as cash or transfer."""
    other_payment_form: bool = False
    """Marks a payment form not in ``payment_form``; describe it in ``payment_description``."""
    payment_description: str | None = None
    """Description of the other payment form (``OpisPlatnosci``)."""
    bank_accounts: list[BankAccount] = Field(default_factory=list)
    """Bank accounts the payment should be made to."""
    factor_bank_accounts: list[BankAccount] = Field(default_factory=list)
    """Bank accounts of the factor, when the receivable is assigned."""
    discount_terms: str | None = None
    """Conditions the buyer must meet to receive the early-payment discount (``Skonto/WarunkiSkonta``)."""
    discount_amount: str | None = None
    """Amount of the early-payment discount (``Skonto/WysokoscSkonta``)."""
    payment_link: str | None = None
    """Link for paying the invoice online (``LinkDoPlatnosci``)."""
    ipksef: str | None = None
    """Identifier of a payment in KSeF (``IPKSeF``)."""
