from datetime import date, datetime
from decimal import Decimal

from ksef2.domain.models.fa3 import (
    ContactInfo,
    InvoiceAddress,
    InvoiceEntity,
    InvoiceHeader,
    InvoiceThirdParty,
    KsefInvoice,
    KsefInvoiceBody,
)
from ksef2.domain.models.fa3.body import InvoiceRow
from ksef2.infra.mappers.invoices.fa3.domain.invoice import to_spec as invoice_to_spec
from ksef2.infra.mappers.invoices.fa3.domain.third_party import (
    to_spec as third_party_to_spec,
)
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2.infra.schema.fa3.models.schemat import FakturaPodmiot3


def make_polish_address() -> InvoiceAddress:
    return InvoiceAddress(
        country_code="PL",
        address_line_1="Marszalkowska 10/5",
        address_line_2="00-001 Warszawa",
    )


def test_third_party_to_spec_maps_additional_buyer() -> None:
    output = third_party_to_spec(
        InvoiceThirdParty(
            eu_vat_id="DE123456789",
            name="Shared Services GmbH",
            address=InvoiceAddress(
                country_code="DE",
                address_line_1="Unter den Linden 1",
                address_line_2="10117 Berlin",
            ),
            correspondence_address=InvoiceAddress(
                country_code="DE",
                address_line_1="Friedrichstrasse 10",
                address_line_2="10117 Berlin",
            ),
            contact=ContactInfo(
                email="ap@example.com",
                phone="+49301234567",
            ),
            role="additional_buyer",
            share_percentage=Decimal("25.5"),
            customer_number="CUST-3",
            eori_number="DE123456789000000",
            buyer_id="BUYER-EXTRA-1",
        )
    )

    assert isinstance(output, FakturaPodmiot3)
    assert output.idnabywcy == "BUYER-EXTRA-1"
    assert output.nr_eori == "DE123456789000000"
    assert output.dane_identyfikacyjne.kod_ue is not None
    assert output.dane_identyfikacyjne.kod_ue.name == "DE"
    assert output.dane_identyfikacyjne.nr_vat_ue == "123456789"
    assert output.dane_identyfikacyjne.nazwa == "Shared Services GmbH"
    assert output.adres is not None
    assert output.adres.adres_l1 == "Unter den Linden 1"
    assert output.adres_koresp is not None
    assert output.adres_koresp.adres_l1 == "Friedrichstrasse 10"
    assert output.dane_kontaktowe[0].email == "ap@example.com"
    assert output.dane_kontaktowe[0].telefon == "+49301234567"
    assert output.rola is not None
    assert output.rola.name == "VALUE_4"
    assert output.udzial == Decimal("25.5")
    assert output.nr_klienta == "CUST-3"


def test_third_party_to_spec_maps_other_role_and_other_identifier() -> None:
    output = third_party_to_spec(
        InvoiceThirdParty(
            country_code="US",
            other_id="US-TAX-9988",
            name="Paying Agent Inc.",
            other_role=True,
            role_description="Escrow payer",
        )
    )

    assert output.dane_identyfikacyjne.kod_kraju == TkodKraju.US
    assert output.dane_identyfikacyjne.nr_id == "US-TAX-9988"
    assert output.rola is None
    assert output.rola_inna == Twybor1.VALUE_1
    assert output.opis_roli == "Escrow payer"


def test_invoice_to_spec_maps_root_third_parties() -> None:
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
            third_parties=[
                InvoiceThirdParty(
                    tax_id="1111111111",
                    country_code="PL",
                    name="Oddzial Odbiorczy",
                    address=make_polish_address(),
                    role="recipient",
                    customer_number="REC-01",
                )
            ],
            body=KsefInvoiceBody(
                issue_date=date(2026, 3, 29),
                issue_place=None,
                invoice_number="FV/1/2026",
                rows=[
                    InvoiceRow(
                        name="Consulting service",
                        quantity=Decimal("1"),
                        unit_price_net=Decimal("100.00"),
                        net_amount=Decimal("100.00"),
                        vat_rate="23",  # pyright: ignore[reportArgumentType]
                        vat_amount=Decimal("23.00"),
                    )
                ],
            ),
        )
    )

    assert len(output.podmiot3) == 1
    assert output.podmiot3[0].dane_identyfikacyjne.nip == "1111111111"
    assert output.podmiot3[0].dane_identyfikacyjne.nazwa == "Oddzial Odbiorczy"
    assert output.podmiot3[0].rola is not None
    assert output.podmiot3[0].rola.name == "VALUE_2"
    assert output.podmiot3[0].nr_klienta == "REC-01"
