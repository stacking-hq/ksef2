from datetime import date, datetime
from decimal import Decimal

from ksef2.domain.models.fa3 import (
    InvoiceAddress,
    InvoiceDetails,
    InvoiceEntity,
    InvoiceLine,
    InvoiceHeader,
    KsefInvoice,
)
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
            details=InvoiceDetails(
                invoice_number="FV/1/2026",
                issue_date=date(2026, 3, 29),
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
            lines=[
                InvoiceLine(
                    name="Consulting service",
                    quantity=Decimal("10"),
                    unit_price_net=Decimal("100.00"),
                    net_amount=Decimal("1000.00"),
                    vat_rate="23",
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
    assert output.fa.fa_wiersz[0].p_8_a == "szt"
    assert output.fa.fa_wiersz[0].p_8_b == "10"
    assert output.fa.fa_wiersz[0].p_9_a == "100.00"
    assert output.fa.fa_wiersz[0].p_11 == "1000.00"
    assert output.fa.fa_wiersz[0].p_11_vat == "230.00"
    assert output.fa.fa_wiersz[0].p_12 == TstawkaPodatku.VALUE_23
    assert output.fa.adnotacje.p_16 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_17 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_18 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_18_a == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_23 == Twybor12.VALUE_2
    assert output.fa.adnotacje.zwolnienie.p_19_n == Twybor1.VALUE_1
    assert output.fa.adnotacje.nowe_srodki_transportu.p_22_n == Twybor1.VALUE_1
    assert output.fa.adnotacje.pmarzy.p_pmarzy_n == Twybor1.VALUE_1
