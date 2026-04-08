from datetime import date, datetime
from decimal import Decimal

from ksef2.domain.models.fa3 import (
    CorrectedBuyerEntity,
    CorrectedInvoiceReference,
    CorrectedSellerEntity,
    InvoiceAddress,
    InvoiceAnnotationsContext,
    InvoiceEntity,
    InvoiceHeader,
    InvoiceTaxExemption,
    KsefInvoiceBody,
    KsefInvoice,
)
from ksef2.domain.models.fa3.body import (
    AdvancePaymentInvoiceContext,
    InvoiceRow,
    AdditionalDescriptionEntry,
    InvoiceType,
    NewTransportMeansItem,
    NewTransportSupply,
    PartialAdvancePayment,
    TaxRegime,
    VatRate,
)
from ksef2.domain.models.fa3.body import CorrectionInvoiceContext
from ksef2.domain.models.fa3.body.payment import InvoicePayment
from ksef2.domain.models.fa3.body.transaction import (
    TransactionAddress,
    TransactionConditions,
    TransactionTransport,
)
from ksef2.infra.mappers.invoices.fa3.domain.invoice import to_spec as invoice_to_spec
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
            header=InvoiceHeader(
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
                issue_place=None,
                invoice_number="FV/1/2026",
                rows=[
                    InvoiceRow(
                        name="Consulting service",
                        supply_date=date(2026, 3, 28),
                        quantity=Decimal("10"),
                        unit_price_net=Decimal("100.00"),
                        unit_price_gross=Decimal("123.00"),
                        net_amount=Decimal("1000.00"),
                        gross_amount=Decimal("1230.00"),
                        vat_rate=VatRate.VAT_23,
                        annex_15_marker=True,
                        gtu_code="GTU_12",
                        procedure="TT_D",
                        currency_exchange_rate=Decimal("4.123456"),
                        before_correction=True,
                        vat_amount=Decimal("230.00"),
                    ),
                    InvoiceRow(
                        name="Support service",
                        unit_of_measure="h",
                        quantity=Decimal("5"),
                        unit_price_net=Decimal("50.00"),
                        net_amount=Decimal("250.00"),
                        vat_rate=VatRate.VAT_23,
                        vat_amount=Decimal("57.50"),
                    ),
                ],
                payment=InvoicePayment(
                    paid=True,
                    payment_form="bank_transfer",
                ),
                fp_invoice=True,
                related_party_transaction=True,
                additional_description=[
                    AdditionalDescriptionEntry(
                        row_number=2,
                        key="ContractReference",
                        value="A-2026-04",
                    )
                ],
                transaction_conditions=TransactionConditions(
                    transports=[
                        TransactionTransport(
                            transport_type="road",
                            shipping_from=TransactionAddress(
                                country_code="PL",
                                address_line_1="Marszalkowska 10/5",
                            ),
                        )
                    ]
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
    assert output.fa.fa_wiersz[0].gtu is not None
    assert output.fa.fa_wiersz[0].gtu.name == "GTU_12"
    assert output.fa.fa_wiersz[0].procedura is not None
    assert output.fa.fa_wiersz[0].procedura.name == "TT_D"
    assert output.fa.fa_wiersz[0].kurs_waluty == "4.123456"
    assert output.fa.fa_wiersz[0].stan_przed == Twybor1.VALUE_1
    assert output.fa.platnosc is not None
    assert output.fa.platnosc.zaplacono == Twybor1.VALUE_1
    assert output.fa.fp == Twybor1.VALUE_1
    assert output.fa.tp == Twybor1.VALUE_1
    assert len(output.fa.dodatkowy_opis) == 1
    assert output.fa.dodatkowy_opis[0].nr_wiersza == 2
    assert output.fa.dodatkowy_opis[0].klucz == "ContractReference"
    assert output.fa.dodatkowy_opis[0].wartosc == "A-2026-04"
    assert output.fa.warunki_transakcji is not None
    assert len(output.fa.warunki_transakcji.transport) == 1
    assert output.fa.warunki_transakcji.transport[0].rodzaj_transportu is not None
    assert output.fa.warunki_transakcji.transport[0].rodzaj_transportu.name == "VALUE_3"
    assert output.fa.adnotacje.p_16 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_17 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_18 == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_18_a == Twybor12.VALUE_2
    assert output.fa.adnotacje.p_23 == Twybor12.VALUE_2
    assert output.fa.adnotacje.zwolnienie.p_19_n == Twybor1.VALUE_1
    assert output.fa.adnotacje.nowe_srodki_transportu.p_22_n == Twybor1.VALUE_1
    assert output.fa.adnotacje.pmarzy.p_pmarzy_n == Twybor1.VALUE_1


def test_invoice_to_spec_maps_correction_party_blocks() -> None:
    output = invoice_to_spec(
        KsefInvoice(
            header=InvoiceHeader(
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
                issue_place=None,
                invoice_number="FK/1/2026",
                invoice_type=InvoiceType.CORRECTING,
                correction=CorrectionInvoiceContext(
                    correction_reason="Buyer data correction",
                    correction_effect_type="other_date",
                    corrected_invoice_period="March 2026",
                    corrected_invoice_number_override="FV/1/2026/OK",
                    corrected_invoices=[
                        CorrectedInvoiceReference(
                            issue_date=date(2026, 3, 1),
                            invoice_number="FV/1/2026",
                            ksef_id="1234567890-20260301-ABCDEF-ABCDEF-FF",
                        )
                    ],
                    corrected_seller=CorrectedSellerEntity(
                        vat_prefix="DE",
                        tax_id="1234567890",
                        name="Old Seller Sp. z o.o.",
                        address=make_polish_address(),
                    ),
                    corrected_buyers=[
                        CorrectedBuyerEntity(
                            eu_vat_id="DE123456789",
                            name="Old Buyer GmbH",
                            buyer_id="BUYER-1",
                        )
                    ],
                ),
                rows=[
                    InvoiceRow(
                        name="Consulting service",
                        quantity=Decimal("1"),
                        unit_price_net=Decimal("100.00"),
                        net_amount=Decimal("100.00"),
                        vat_rate=VatRate.VAT_23,
                        vat_amount=Decimal("23.00"),
                    )
                ],
            ),
        )
    )

    assert output.fa.podmiot1_k is not None
    assert output.fa.typ_korekty is not None
    assert output.fa.typ_korekty.name == "VALUE_3"
    assert output.fa.okres_fa_korygowanej == "March 2026"
    assert output.fa.nr_fa_korygowany == "FV/1/2026/OK"
    assert output.fa.podmiot1_k.prefiks_podatnika is not None
    assert output.fa.podmiot1_k.prefiks_podatnika.name == "DE"
    assert output.fa.podmiot1_k.dane_identyfikacyjne.nazwa == "Old Seller Sp. z o.o."
    assert len(output.fa.podmiot2_k) == 1
    assert output.fa.podmiot2_k[0].dane_identyfikacyjne.kod_ue is not None
    assert output.fa.podmiot2_k[0].dane_identyfikacyjne.kod_ue.name == "DE"
    assert output.fa.podmiot2_k[0].dane_identyfikacyjne.nr_vat_ue == "123456789"
    assert output.fa.podmiot2_k[0].idnabywcy == "BUYER-1"


def test_invoice_to_spec_maps_foreign_currency_vat_and_annotations() -> None:
    output = invoice_to_spec(
        KsefInvoice(
            header=InvoiceHeader(
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
                currency="EUR",
                issue_date=date(2026, 3, 29),
                issue_place=None,
                invoice_number="FV/2/2026",
                vat_currency_exchange_rate=Decimal("4.500000"),
                annotations=InvoiceAnnotationsContext(
                    cash_accounting=True,
                    self_billing=True,
                    reverse_charge_annotation=True,
                    split_payment=True,
                    tax_exemption=InvoiceTaxExemption(
                        legal_basis_act="art. 43 ust. 1 pkt 2 ustawy"
                    ),
                    new_transport_supply=NewTransportSupply(
                        article_42_5_required=True,
                        items=[
                            NewTransportMeansItem(
                                available_from=date(2026, 3, 1),
                                row_number=2,
                                brand="Volvo",
                                model="FH",
                                registration_number="WX12345",
                                land_vehicle_mileage="1250",
                                vin="YV2RT40A1KA123456",
                            )
                        ],
                    ),
                    simplified_procedure=True,
                ),
                rows=[
                    InvoiceRow(
                        name="Standard service",
                        quantity=Decimal("1"),
                        unit_price_net=Decimal("100.00"),
                        net_amount=Decimal("100.00"),
                        vat_rate=VatRate.VAT_23,
                        vat_amount=Decimal("23.00"),
                    ),
                    InvoiceRow(
                        name="Reduced service",
                        quantity=Decimal("1"),
                        unit_price_net=Decimal("100.00"),
                        net_amount=Decimal("100.00"),
                        vat_rate=VatRate.VAT_8,
                        vat_amount=Decimal("8.00"),
                    ),
                    InvoiceRow(
                        name="Second reduced service",
                        quantity=Decimal("1"),
                        unit_price_net=Decimal("100.00"),
                        net_amount=Decimal("100.00"),
                        vat_rate=VatRate.VAT_5,
                        vat_amount=Decimal("5.00"),
                    ),
                    InvoiceRow(
                        name="Taxi service",
                        quantity=Decimal("1"),
                        unit_price_net=Decimal("100.00"),
                        net_amount=Decimal("100.00"),
                        vat_rate=VatRate.VAT_4,
                        vat_amount=Decimal("4.00"),
                        tax_regime=TaxRegime.TAXI_FLAT_RATE,
                    ),
                ],
            ),
        )
    )

    assert output.fa.kurs_waluty_z == "4.500000"
    assert output.fa.p_14_1_w == "103.50"
    assert output.fa.p_14_2_w == "36.00"
    assert output.fa.p_14_3_w == "22.50"
    assert output.fa.p_14_4_w == "18.00"
    assert output.fa.adnotacje.p_16 == Twybor12.VALUE_1
    assert output.fa.adnotacje.p_17 == Twybor12.VALUE_1
    assert output.fa.adnotacje.p_18 == Twybor12.VALUE_1
    assert output.fa.adnotacje.p_18_a == Twybor12.VALUE_1
    assert output.fa.adnotacje.p_23 == Twybor12.VALUE_1
    assert output.fa.adnotacje.zwolnienie.p_19 == Twybor1.VALUE_1
    assert output.fa.adnotacje.zwolnienie.p_19_a == "art. 43 ust. 1 pkt 2 ustawy"
    assert output.fa.adnotacje.nowe_srodki_transportu.p_22 == Twybor1.VALUE_1
    assert output.fa.adnotacje.nowe_srodki_transportu.p_42_5 == Twybor12.VALUE_1
    assert len(output.fa.adnotacje.nowe_srodki_transportu.nowy_srodek_transportu) == 1
    assert (
        output.fa.adnotacje.nowe_srodki_transportu.nowy_srodek_transportu[0].p_22_bmk
        == "Volvo"
    )
    assert (
        output.fa.adnotacje.nowe_srodki_transportu.nowy_srodek_transportu[0].p_22_b1
        == "YV2RT40A1KA123456"
    )


def test_invoice_to_spec_maps_advance_before_correction_and_partial_payments() -> None:
    output = invoice_to_spec(
        KsefInvoice(
            header=InvoiceHeader(
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
                currency="EUR",
                issue_date=date(2026, 3, 29),
                issue_place=None,
                invoice_number="FKZ/1/2026",
                invoice_type=InvoiceType.CORRECTING_ZAL,
                advance=AdvancePaymentInvoiceContext(
                    amount_before_correction=Decimal("1200.50"),
                    currency_exchange_rate_before_correction=Decimal("4.450001"),
                    advance_partial_payments=[
                        PartialAdvancePayment(
                            payment_date=date(2026, 3, 1),
                            amount=Decimal("500.00"),
                            currency_exchange_rate=Decimal("4.400001"),
                        )
                    ],
                ),
                rows=[
                    InvoiceRow(
                        name="Consulting service",
                        quantity=Decimal("1"),
                        unit_price_net=Decimal("100.00"),
                        net_amount=Decimal("100.00"),
                        vat_rate=VatRate.VAT_23,
                        vat_amount=Decimal("23.00"),
                    )
                ],
            ),
        )
    )

    assert output.fa.p_15_zk == "1200.50"
    assert output.fa.kurs_waluty_zk == "4.450001"
    assert len(output.fa.zaliczka_czesciowa) == 1
    assert output.fa.zaliczka_czesciowa[0].p_6_z == "2026-03-01"
    assert output.fa.zaliczka_czesciowa[0].p_15_z == "500.00"
    assert output.fa.zaliczka_czesciowa[0].kurs_waluty_zw == "4.400001"
