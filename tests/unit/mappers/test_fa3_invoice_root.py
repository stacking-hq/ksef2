from datetime import date, datetime
from decimal import Decimal

from ksef2.domain.models.fa3 import (
    InvoiceAddress,
    InvoiceEntity,
    InvoiceHeader,
    InvoiceLine,
    KsefInvoiceBody,
    KsefInvoice,
)
from ksef2.domain.models.fa3.body.payment import InvoicePayment
from ksef2.infra.mappers.invoices.fa3.invoice import to_spec as invoice_to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import (
    Faktura,
    TrodzajFaktury,
    TstawkaPodatku,
)


def make_polish_address() -> InvoiceAddress:
    return InvoiceAddress(
        country_code="PL",
        address_line_1="Marszalkowska 10/5",
        address_line_2="00-001 Warszawa",
    )


def test_invoice_to_spec_assembles_root_faktura() -> None:
    output = invoice_to_spec(
        KsefInvoice(
            invoice_header=InvoiceHeader(
                generation_timestamp=datetime(2026, 2, 1, 12, 30, 45),
                system_info="ACME ERP",
            ),
            seller=InvoiceEntity(
                tax_id="1234567890",
                name="Seller Sp. z o.o.",
                address=make_polish_address(),
            ),
            buyer=InvoiceEntity(
                name="Buyer GmbH",
                address=InvoiceAddress(
                    country_code="DE",
                    address_line_1="Unter den Linden 1",
                ),
            ),
            body=KsefInvoiceBody(
                issue_date=date(2026, 3, 29),
                invoice_number="FV/1/2026",
                lines=[
                    InvoiceLine(
                        name="Consulting service",
                        supply_date=date(2026, 3, 28),
                        quantity=Decimal("10"),
                        unit_price_net=Decimal("100.00"),
                        unit_price_gross=Decimal("123.00"),
                        net_amount=Decimal("1000.00"),
                        gross_amount=Decimal("1230.00"),
                        vat_rate="23",
                        annex_15_marker=True,
                        gtu_code="GTU_12",
                        procedure="TT_D",
                        currency_exchange_rate=Decimal("4.123456"),
                        before_correction=True,
                        vat_amount=Decimal("230.00"),
                    ),
                    InvoiceLine(
                        name="Support service",
                        unit_of_measure="h",
                        quantity=Decimal("5"),
                        unit_price_net=Decimal("50.00"),
                        net_amount=Decimal("250.00"),
                        vat_rate="23",
                        vat_amount=Decimal("57.50"),
                    ),
                ],
                payment=InvoicePayment(
                    paid=True,
                    payment_form="bank_transfer",
                ),
            ),
        )
    )

    assert isinstance(output, Faktura)
    assert output.naglowek.system_info == "ACME ERP"
    assert output.podmiot1.dane_identyfikacyjne.nazwa == "Seller Sp. z o.o."
    assert output.podmiot2.dane_identyfikacyjne.nazwa == "Buyer GmbH"
    assert output.fa.p_1 == "2026-03-29"
    assert output.fa.p_2 == "FV/1/2026"
    assert output.fa.p_13_1 == "1250.00"
    assert output.fa.p_14_1 == "287.50"
    assert output.fa.p_15 == "1537.50"
    assert output.fa.rodzaj_faktury == TrodzajFaktury.VAT
    assert len(output.fa.fa_wiersz) == 2
    assert output.fa.fa_wiersz[0].nr_wiersza_fa == 1
    assert output.fa.fa_wiersz[0].p_7 == "Consulting service"
    assert output.fa.fa_wiersz[0].p_6_a == "2026-03-28"
    assert output.fa.fa_wiersz[0].p_8_a == "szt"
    assert output.fa.fa_wiersz[0].p_8_b == "10"
    assert output.fa.fa_wiersz[0].p_9_a == "100.00"
    assert output.fa.fa_wiersz[0].p_9_b == "123.00"
    assert output.fa.fa_wiersz[0].p_11 == "1000.00"
    assert output.fa.fa_wiersz[0].p_11_a == "1230.00"
    assert output.fa.fa_wiersz[0].p_11_vat == "230.00"
    assert output.fa.fa_wiersz[0].p_12 == TstawkaPodatku.VALUE_23
    assert output.fa.fa_wiersz[0].p_12_zal_15 == Twybor1.VALUE_1
    assert output.fa.fa_wiersz[0].gtu.name == "GTU_12"
    assert output.fa.fa_wiersz[0].procedura.name == "TT_D"
    assert output.fa.fa_wiersz[0].kurs_waluty == "4.123456"
    assert output.fa.fa_wiersz[0].stan_przed == Twybor1.VALUE_1
    assert output.fa.platnosc is not None
    assert output.fa.platnosc.zaplacono == Twybor1.VALUE_1
    assert output.fa.adnotacje.p_16 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_17 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_18 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_18_a == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_23 == Twybor12.VALUE_2
    assert output.fa.adnotacje.zwolnienie.p_19_n == Twybor1.VALUE_1
    assert output.fa.adnotacje.nowe_srodki_transportu.p_22_n == Twybor1.VALUE_1
    assert output.fa.adnotacje.pmarzy.p_pmarzy_n == Twybor1.VALUE_1
