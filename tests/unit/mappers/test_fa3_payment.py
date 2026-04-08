from datetime import date
from decimal import Decimal

from ksef2.domain.models.fa3.body.payment import (
    BankAccount,
    InvoicePayment,
    PartialPayment,
    PaymentTerm,
    PaymentTermDescription,
)
from ksef2.infra.mappers.invoices.fa3.domain.payment import from_spec, to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaPlatnosc,
    FakturaFaPlatnoscTerminPlatnosci,
    FakturaFaPlatnoscTerminPlatnosciTerminOpis,
    TformaPlatnosci,
    TrachunekBankowy,
)


def make_payment() -> InvoicePayment:
    return InvoicePayment(
        paid=True,
        payment_date=date(2026, 4, 3),
        partial_payment_status="partial",
        partial_payments=[
            PartialPayment(
                amount=Decimal("100.00"),
                payment_date=date(2026, 4, 1),
                payment_form="card",
                other_payment_form=True,
                payment_description="Gift-card mixed payment",
            )
        ],
        payment_terms=[
            PaymentTerm(
                due_date=date(2026, 4, 10),
                due_date_description=PaymentTermDescription(
                    quantity=14,
                    unit="dni",
                    starting_event="delivery",
                ),
            )
        ],
        payment_form="bank_transfer",
        other_payment_form=True,
        payment_description="Installment schedule agreed with buyer",
        bank_accounts=[
            BankAccount(
                account_number="PL10114020040000300201355387",
                swift="BREXPLPWXXX",
                own_bank_account_type="factor_collection",
                bank_name="mBank",
                account_description="Main settlement account",
            )
        ],
        factor_bank_accounts=[
            BankAccount(account_number="PL12114020040000300201355388")
        ],
        discount_terms="2% within 7 days",
        discount_amount="2%",
        payment_link="https://pay.example.com/invoice?IPKSeF=123ABCDEFGHIJ",
        ipksef="123ABCDEFGHIJ",
    )


def test_payment_to_spec_maps_nested_payment_data() -> None:
    output = to_spec(make_payment())

    assert isinstance(output, FakturaFaPlatnosc)
    assert output.zaplacono == Twybor1.VALUE_1
    assert output.data_zaplaty == "2026-04-03"
    assert output.znacznik_zaplaty_czesciowej == Twybor12.VALUE_1
    assert output.zaplata_czesciowa[0].kwota_zaplaty_czesciowej == "100.00"
    assert output.zaplata_czesciowa[0].forma_platnosci == TformaPlatnosci.VALUE_2
    assert output.forma_platnosci == TformaPlatnosci.VALUE_6
    assert output.rachunek_bankowy[0].nazwa_banku == "mBank"
    assert output.skonto is not None
    assert output.skonto.warunki_skonta == "2% within 7 days"
    assert (
        output.link_do_platnosci
        == "https://pay.example.com/invoice?IPKSeF=123ABCDEFGHIJ"
    )
    assert output.ipkse_f == "123ABCDEFGHIJ"


def test_payment_from_spec_restores_domain_model() -> None:
    mapped = from_spec(to_spec(make_payment()))

    assert isinstance(mapped, InvoicePayment)
    assert mapped.paid is True
    assert mapped.payment_date == date(2026, 4, 3)
    assert mapped.partial_payment_status == "partial"
    assert mapped.partial_payments[0].payment_form == "card"
    assert mapped.partial_payments[0].other_payment_form is True
    assert mapped.payment_terms[0].due_date == date(2026, 4, 10)
    assert mapped.payment_terms[0].due_date_description is not None
    assert mapped.payment_terms[0].due_date_description.starting_event == "delivery"
    assert mapped.payment_form == "bank_transfer"
    assert mapped.bank_accounts[0].own_bank_account_type == "factor_collection"
    assert mapped.discount_amount == "2%"


def test_payment_to_spec_matches_brochure_example_25_paid_transfer() -> None:
    payment = InvoicePayment(
        paid=True,
        payment_date=date(2026, 5, 20),
        payment_form="bank_transfer",
    )

    output = to_spec(payment)

    assert output.zaplacono == Twybor1.VALUE_1
    assert output.data_zaplaty == "2026-05-20"
    assert output.forma_platnosci == TformaPlatnosci.VALUE_6
    assert output.zaplata_czesciowa == []
    assert output.rachunek_bankowy == []


def test_payment_to_spec_matches_brochure_example_26_partial_payments() -> None:
    payment = InvoicePayment(
        partial_payment_status="final",
        partial_payments=[
            PartialPayment(
                amount=Decimal("300.00"),
                payment_date=date(2026, 6, 21),
                payment_form="cash",
            ),
            PartialPayment(
                amount=Decimal("400.00"),
                payment_date=date(2026, 6, 24),
                payment_form="card",
            ),
            PartialPayment(
                amount=Decimal("500.00"),
                payment_date=date(2026, 6, 28),
                payment_form="bank_transfer",
            ),
        ],
        bank_accounts=[
            BankAccount(
                account_number="11111111111111111111111111",
                bank_name="XYZ",
                account_description="Rachunek prowadzony w walucie krajowej (PLN)",
            )
        ],
    )

    output = to_spec(payment)

    assert output.znacznik_zaplaty_czesciowej == Twybor12.VALUE_2
    assert [item.kwota_zaplaty_czesciowej for item in output.zaplata_czesciowa] == [
        "300.00",
        "400.00",
        "500.00",
    ]
    assert [item.data_zaplaty_czesciowej for item in output.zaplata_czesciowa] == [
        "2026-06-21",
        "2026-06-24",
        "2026-06-28",
    ]
    assert [item.forma_platnosci for item in output.zaplata_czesciowa] == [
        TformaPlatnosci.VALUE_1,
        TformaPlatnosci.VALUE_2,
        TformaPlatnosci.VALUE_6,
    ]
    assert output.rachunek_bankowy[0].nr_rb == "11111111111111111111111111"
    assert output.rachunek_bankowy[0].nazwa_banku == "XYZ"
    assert (
        output.rachunek_bankowy[0].opis_rachunku
        == "Rachunek prowadzony w walucie krajowej (PLN)"
    )


def test_payment_from_spec_matches_brochure_example_27_payment_term() -> None:
    schema = FakturaFaPlatnosc(
        termin_platnosci=[
            FakturaFaPlatnoscTerminPlatnosci(
                termin_opis=FakturaFaPlatnoscTerminPlatnosciTerminOpis(
                    ilosc=14,
                    jednostka="dni",
                    zdarzenie_poczatkowe="od wystawienia faktury",
                )
            )
        ],
        forma_platnosci=TformaPlatnosci.VALUE_6,
        rachunek_bankowy=[
            TrachunekBankowy(
                nr_rb="11111111111111111111111111",
                nazwa_banku="XYZ",
            )
        ],
    )

    mapped = from_spec(schema)

    assert mapped.payment_form == "bank_transfer"
    assert mapped.payment_terms[0].due_date is None
    assert mapped.payment_terms[0].due_date_description is not None
    assert mapped.payment_terms[0].due_date_description.quantity == 14
    assert mapped.payment_terms[0].due_date_description.unit == "dni"
    assert (
        mapped.payment_terms[0].due_date_description.starting_event
        == "od wystawienia faktury"
    )
    assert mapped.bank_accounts[0].account_number == "11111111111111111111111111"
    assert mapped.bank_accounts[0].bank_name == "XYZ"
