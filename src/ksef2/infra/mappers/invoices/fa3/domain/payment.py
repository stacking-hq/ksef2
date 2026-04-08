"""Mappings between FA(3) payment domain models and generated schema models."""

from datetime import date
from decimal import Decimal
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3.body.payment import (
    BankAccount,
    BankOwnAccountType,
    InvoicePayment,
    PartialPayment,
    PartialPaymentStatus,
    PaymentForm,
    PaymentTerm,
    PaymentTermDescription,
)
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaPlatnosc,
    FakturaFaPlatnoscSkonto,
    FakturaFaPlatnoscTerminPlatnosci,
    FakturaFaPlatnoscTerminPlatnosciTerminOpis,
    FakturaFaPlatnoscZaplataCzesciowa,
    TformaPlatnosci,
    TrachunekBankowy,
    TrachunekWlasnyBanku,
)


def _format_decimal(value: Decimal) -> str:
    return format(value, "f")


def _map_payment_form(value: PaymentForm) -> TformaPlatnosci:
    payment_form_map: dict[PaymentForm, TformaPlatnosci] = {
        "cash": TformaPlatnosci.VALUE_1,
        "card": TformaPlatnosci.VALUE_2,
        "voucher": TformaPlatnosci.VALUE_3,
        "check": TformaPlatnosci.VALUE_4,
        "credit": TformaPlatnosci.VALUE_5,
        "bank_transfer": TformaPlatnosci.VALUE_6,
        "mobile": TformaPlatnosci.VALUE_7,
    }
    return payment_form_map[value]


def _from_payment_form(value: TformaPlatnosci) -> PaymentForm:
    payment_form_map: dict[TformaPlatnosci, PaymentForm] = {
        TformaPlatnosci.VALUE_1: "cash",
        TformaPlatnosci.VALUE_2: "card",
        TformaPlatnosci.VALUE_3: "voucher",
        TformaPlatnosci.VALUE_4: "check",
        TformaPlatnosci.VALUE_5: "credit",
        TformaPlatnosci.VALUE_6: "bank_transfer",
        TformaPlatnosci.VALUE_7: "mobile",
    }
    return payment_form_map[value]


def _map_bank_account_type(value: BankOwnAccountType) -> TrachunekWlasnyBanku:
    bank_account_type_map: dict[BankOwnAccountType, TrachunekWlasnyBanku] = {
        "purchased_receivables": TrachunekWlasnyBanku.VALUE_1,
        "factor_collection": TrachunekWlasnyBanku.VALUE_2,
        "internal_treasury": TrachunekWlasnyBanku.VALUE_3,
    }
    return bank_account_type_map[value]


def _from_bank_account_type(value: TrachunekWlasnyBanku) -> BankOwnAccountType:
    bank_account_type_map: dict[TrachunekWlasnyBanku, BankOwnAccountType] = {
        TrachunekWlasnyBanku.VALUE_1: "purchased_receivables",
        TrachunekWlasnyBanku.VALUE_2: "factor_collection",
        TrachunekWlasnyBanku.VALUE_3: "internal_treasury",
    }
    return bank_account_type_map[value]


def _map_partial_payment_status(value: PartialPaymentStatus) -> Twybor12:
    partial_payment_status_map: dict[PartialPaymentStatus, Twybor12] = {
        "partial": Twybor12.VALUE_1,
        "final": Twybor12.VALUE_2,
    }
    return partial_payment_status_map[value]


def _from_partial_payment_status(value: Twybor12) -> PartialPaymentStatus:
    partial_payment_status_map: dict[Twybor12, PartialPaymentStatus] = {
        Twybor12.VALUE_1: "partial",
        Twybor12.VALUE_2: "final",
    }
    return partial_payment_status_map[value]


@overload
def to_spec(request: InvoicePayment) -> FakturaFaPlatnosc: ...


@overload
def to_spec(request: PartialPayment) -> FakturaFaPlatnoscZaplataCzesciowa: ...


@overload
def to_spec(request: PaymentTerm) -> FakturaFaPlatnoscTerminPlatnosci: ...


@overload
def to_spec(
    request: PaymentTermDescription,
) -> FakturaFaPlatnoscTerminPlatnosciTerminOpis: ...


@overload
def to_spec(request: BankAccount) -> TrachunekBankowy: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a payment domain model into the FA(3) payment schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: InvoicePayment) -> FakturaFaPlatnosc:
    payment_date = request.payment_date.isoformat() if request.payment_date else None
    partial_payment_status = (
        _map_partial_payment_status(request.partial_payment_status)
        if request.partial_payment_status
        else None
    )
    partial_payments = [to_spec(payment) for payment in request.partial_payments]
    payment_terms = [to_spec(term) for term in request.payment_terms]
    payment_form = (
        _map_payment_form(request.payment_form) if request.payment_form else None
    )
    bank_accounts = [to_spec(account) for account in request.bank_accounts]
    factor_bank_accounts = [
        to_spec(account) for account in request.factor_bank_accounts
    ]
    discount = (
        FakturaFaPlatnoscSkonto(
            warunki_skonta=request.discount_terms,
            wysokosc_skonta=request.discount_amount,
        )
        if request.discount_terms is not None and request.discount_amount is not None
        else None
    )

    return FakturaFaPlatnosc(
        zaplacono=Twybor1.VALUE_1 if request.paid else None,
        data_zaplaty=payment_date,
        znacznik_zaplaty_czesciowej=partial_payment_status,
        zaplata_czesciowa=partial_payments,
        termin_platnosci=payment_terms,
        forma_platnosci=payment_form,
        platnosc_inna=Twybor1.VALUE_1 if request.other_payment_form else None,
        opis_platnosci=request.payment_description,
        rachunek_bankowy=bank_accounts,
        rachunek_bankowy_faktora=factor_bank_accounts,
        skonto=discount,
        link_do_platnosci=request.payment_link,
        ipkse_f=request.ipksef,
    )


@_to_spec.register
def _(request: PartialPayment) -> FakturaFaPlatnoscZaplataCzesciowa:
    payment_form = (
        _map_payment_form(request.payment_form) if request.payment_form else None
    )

    return FakturaFaPlatnoscZaplataCzesciowa(
        kwota_zaplaty_czesciowej=_format_decimal(request.amount),
        data_zaplaty_czesciowej=request.payment_date.isoformat(),
        forma_platnosci=payment_form,
        platnosc_inna=Twybor1.VALUE_1 if request.other_payment_form else None,
        opis_platnosci=request.payment_description,
    )


@_to_spec.register
def _(request: PaymentTerm) -> FakturaFaPlatnoscTerminPlatnosci:
    due_date = request.due_date.isoformat() if request.due_date else None
    due_date_description = (
        to_spec(request.due_date_description) if request.due_date_description else None
    )

    return FakturaFaPlatnoscTerminPlatnosci(
        termin=due_date,
        termin_opis=due_date_description,
    )


@_to_spec.register
def _(request: PaymentTermDescription) -> FakturaFaPlatnoscTerminPlatnosciTerminOpis:
    return FakturaFaPlatnoscTerminPlatnosciTerminOpis(
        ilosc=request.quantity,
        jednostka=request.unit,
        zdarzenie_poczatkowe=request.starting_event,
    )


@_to_spec.register
def _(request: BankAccount) -> TrachunekBankowy:
    own_bank_account_type = (
        _map_bank_account_type(request.own_bank_account_type)
        if request.own_bank_account_type
        else None
    )

    return TrachunekBankowy(
        nr_rb=request.account_number,
        swift=request.swift,
        rachunek_wlasny_banku=own_bank_account_type,
        nazwa_banku=request.bank_name,
        opis_rachunku=request.account_description,
    )


@overload
def from_spec(schema: FakturaFaPlatnosc) -> InvoicePayment: ...


@overload
def from_spec(schema: FakturaFaPlatnoscZaplataCzesciowa) -> PartialPayment: ...


@overload
def from_spec(schema: FakturaFaPlatnoscTerminPlatnosci) -> PaymentTerm: ...


@overload
def from_spec(
    schema: FakturaFaPlatnoscTerminPlatnosciTerminOpis,
) -> PaymentTermDescription: ...


@overload
def from_spec(schema: TrachunekBankowy) -> BankAccount: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert an FA(3) payment schema model into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: FakturaFaPlatnosc) -> InvoicePayment:
    payment_date = (
        date.fromisoformat(schema.data_zaplaty) if schema.data_zaplaty else None
    )
    partial_payment_status = (
        _from_partial_payment_status(schema.znacznik_zaplaty_czesciowej)
        if schema.znacznik_zaplaty_czesciowej
        else None
    )
    partial_payments = [from_spec(payment) for payment in schema.zaplata_czesciowa]
    payment_terms = [from_spec(term) for term in schema.termin_platnosci]
    payment_form = (
        _from_payment_form(schema.forma_platnosci) if schema.forma_platnosci else None
    )
    bank_accounts = [from_spec(account) for account in schema.rachunek_bankowy]
    factor_bank_accounts = [
        from_spec(account) for account in schema.rachunek_bankowy_faktora
    ]
    discount_terms = schema.skonto.warunki_skonta if schema.skonto else None
    discount_amount = schema.skonto.wysokosc_skonta if schema.skonto else None

    return InvoicePayment(
        paid=schema.zaplacono == Twybor1.VALUE_1,
        payment_date=payment_date,
        partial_payment_status=partial_payment_status,
        partial_payments=partial_payments,
        payment_terms=payment_terms,
        payment_form=payment_form,
        other_payment_form=schema.platnosc_inna == Twybor1.VALUE_1,
        payment_description=schema.opis_platnosci,
        bank_accounts=bank_accounts,
        factor_bank_accounts=factor_bank_accounts,
        discount_terms=discount_terms,
        discount_amount=discount_amount,
        payment_link=schema.link_do_platnosci,
        ipksef=schema.ipkse_f,
    )


@_from_spec.register
def _(schema: FakturaFaPlatnoscZaplataCzesciowa) -> PartialPayment:
    payment_form = (
        _from_payment_form(schema.forma_platnosci) if schema.forma_platnosci else None
    )

    return PartialPayment(
        amount=Decimal(schema.kwota_zaplaty_czesciowej),
        payment_date=date.fromisoformat(schema.data_zaplaty_czesciowej),
        payment_form=payment_form,
        other_payment_form=schema.platnosc_inna == Twybor1.VALUE_1,
        payment_description=schema.opis_platnosci,
    )


@_from_spec.register
def _(schema: FakturaFaPlatnoscTerminPlatnosci) -> PaymentTerm:
    due_date = date.fromisoformat(schema.termin) if schema.termin else None
    due_date_description = from_spec(schema.termin_opis) if schema.termin_opis else None

    return PaymentTerm(
        due_date=due_date,
        due_date_description=due_date_description,
    )


@_from_spec.register
def _(schema: FakturaFaPlatnoscTerminPlatnosciTerminOpis) -> PaymentTermDescription:
    return PaymentTermDescription(
        quantity=schema.ilosc,
        unit=schema.jednostka,
        starting_event=schema.zdarzenie_poczatkowe,
    )


@_from_spec.register
def _(schema: TrachunekBankowy) -> BankAccount:
    own_bank_account_type = (
        _from_bank_account_type(schema.rachunek_wlasny_banku)
        if schema.rachunek_wlasny_banku
        else None
    )

    return BankAccount(
        account_number=schema.nr_rb,
        swift=schema.swift,
        own_bank_account_type=own_bank_account_type,
        bank_name=schema.nazwa_banku,
        account_description=schema.opis_rachunku,
    )
