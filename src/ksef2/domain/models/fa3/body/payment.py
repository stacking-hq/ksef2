"""FA(3) payment, terms, and bank-account domain models."""

from datetime import date
from decimal import Decimal
from typing import Self, Literal

from pydantic import Field, model_validator

from ksef2.domain.models import KSeFBaseModel


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
    unit: str
    starting_event: str


class PaymentTerm(KSeFBaseModel):
    """FA(3) payment term entry.

    References:
        schemat.FakturaFaPlatnoscTerminPlatnosci

    Maps:
        due_date - termin (date)
        due_date_description - termin_opis (FakturaFaPlatnoscTerminPlatnosciTerminOpis)
    """

    due_date: date | None = None
    due_date_description: PaymentTermDescription | None = None

    @model_validator(mode="after")
    def validate_term(self) -> Self:
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
    swift: str | None = None
    own_bank_account_type: BankOwnAccountType | None = None
    bank_name: str | None = None
    account_description: str | None = None


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
    payment_date: date
    payment_form: PaymentForm | None = None
    other_payment_form: bool = False
    payment_description: str | None = None


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
    payment_date: date | None = None
    partial_payment_status: PartialPaymentStatus | None = None
    partial_payments: list[PartialPayment] = Field(default_factory=list)
    payment_terms: list[PaymentTerm] = Field(default_factory=list)
    payment_form: PaymentForm | None = None
    other_payment_form: bool = False
    payment_description: str | None = None
    bank_accounts: list[BankAccount] = Field(default_factory=list)
    factor_bank_accounts: list[BankAccount] = Field(default_factory=list)
    discount_terms: str | None = None
    discount_amount: str | None = None
    payment_link: str | None = None
    ipksef: str | None = None
