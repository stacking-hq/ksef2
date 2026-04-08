from datetime import date, datetime, timezone
from decimal import Decimal

from xsdata.models.datatype import XmlDateTime

from ksef2.domain.models.fa3.body.transaction import (
    TransactionAddress,
    TransactionConditions,
    TransactionIdentity,
    TransactionOrder,
    TransactionTransport,
)
from ksef2.infra.mappers.invoices.fa3.domain.transaction import from_spec, to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaWarunkiTransakcji,
    FakturaFaWarunkiTransakcjiTransport,
    FakturaFaWarunkiTransakcjiTransportPrzewoznik,
    FakturaFaWarunkiTransakcjiZamowienia,
    Tadres,
    Tladunek,
    Tpodmiot2,
    TrodzajTransportu,
)


def make_transaction_conditions() -> TransactionConditions:
    return TransactionConditions(
        orders=[
            TransactionOrder(
                order_date=date(2026, 9, 15),
                order_number="ZAM/182/2026",
            )
        ],
        lot_numbers=["LOT-01", "LOT-02"],
        delivery_terms="DAP",
        contract_exchange_rate=Decimal("4.500000"),
        contract_currency="EUR",
        transports=[
            TransactionTransport(
                transport_type="road",
                carrier_identity=TransactionIdentity(
                    tax_id="9999999999",
                    name="Jan Nowak",
                ),
                carrier_address=TransactionAddress(
                    country_code="PL",
                    address_line_1="ul. Pomaranczowa 12",
                    address_line_2="33-333 Gliwice",
                ),
                transport_order_number="TR/09/26",
                cargo_type="carton",
                packaging_unit="1 karton/40 sztuk",
                transport_start=datetime(2026, 9, 25, 7, 34, tzinfo=timezone.utc),
                transport_end=datetime(2026, 9, 25, 21, 40, tzinfo=timezone.utc),
                shipping_from=TransactionAddress(
                    country_code="PL",
                    address_line_1="ul. Zielona 5",
                    address_line_2="11-111 Katowice",
                ),
                shipping_via=[
                    TransactionAddress(
                        country_code="PL",
                        address_line_1="ul. Niebieska 27",
                        address_line_2='55-555 Lodz, Magazyn "B"',
                    )
                ],
                shipping_to=TransactionAddress(
                    country_code="PL",
                    address_line_1="ul. Szara 25",
                    address_line_2="22-222 Gdynia",
                ),
            )
        ],
        intermediary_entity=True,
    )


def test_transaction_to_spec_matches_brochure_example_28() -> None:
    output = to_spec(make_transaction_conditions())

    assert isinstance(output, FakturaFaWarunkiTransakcji)
    assert output.zamowienia[0].data_zamowienia == "2026-09-15"
    assert output.zamowienia[0].nr_zamowienia == "ZAM/182/2026"
    assert output.nr_partii_towaru == ["LOT-01", "LOT-02"]
    assert output.kurs_umowny == "4.500000"
    assert output.waluta_umowna is not None
    assert output.waluta_umowna.value == "EUR"
    assert output.transport[0].rodzaj_transportu == TrodzajTransportu.VALUE_3
    assert output.transport[0].przewoznik is not None
    assert output.transport[0].przewoznik.dane_identyfikacyjne.nip == "9999999999"
    assert output.transport[0].przewoznik.dane_identyfikacyjne.nazwa == "Jan Nowak"
    assert output.transport[0].opis_ladunku == Tladunek.VALUE_4
    assert output.transport[0].jednostka_opakowania == "1 karton/40 sztuk"
    assert output.transport[0].data_godz_rozp_transportu == XmlDateTime.from_string(
        "2026-09-25T07:34:00Z"
    )
    assert output.transport[0].data_godz_zak_transportu == XmlDateTime.from_string(
        "2026-09-25T21:40:00Z"
    )
    assert output.transport[0].wysylka_z is not None
    assert output.transport[0].wysylka_z.adres_l1 == "ul. Zielona 5"
    assert output.transport[0].wysylka_przez[0].adres_l1 == "ul. Niebieska 27"
    assert output.transport[0].wysylka_do is not None
    assert output.transport[0].wysylka_do.adres_l1 == "ul. Szara 25"
    assert output.podmiot_posredniczacy == Twybor1.VALUE_1


def test_transaction_from_spec_restores_domain_model() -> None:
    schema = FakturaFaWarunkiTransakcji(
        zamowienia=[
            FakturaFaWarunkiTransakcjiZamowienia(
                data_zamowienia="2026-09-15",
                nr_zamowienia="ZAM/182/2026",
            )
        ],
        nr_partii_towaru=["LOT-01"],
        warunki_dostawy="DAP",
        transport=[
            FakturaFaWarunkiTransakcjiTransport(
                rodzaj_transportu=TrodzajTransportu.VALUE_3,
                przewoznik=FakturaFaWarunkiTransakcjiTransportPrzewoznik(
                    dane_identyfikacyjne=Tpodmiot2(
                        nip="9999999999",
                        nazwa="Jan Nowak",
                    ),
                    adres_przewoznika=Tadres(
                        kod_kraju=TkodKraju.PL,
                        adres_l1="ul. Pomaranczowa 12",
                        adres_l2="33-333 Gliwice",
                    ),
                ),
                nr_zlecenia_transportu="TR/09/26",
                opis_ladunku=Tladunek.VALUE_4,
                jednostka_opakowania="1 karton/40 sztuk",
                data_godz_rozp_transportu=XmlDateTime.from_string(
                    "2026-09-25T07:34:00Z"
                ),
                data_godz_zak_transportu=XmlDateTime.from_string(
                    "2026-09-25T21:40:00Z"
                ),
                wysylka_z=Tadres(
                    kod_kraju=TkodKraju.PL,
                    adres_l1="ul. Zielona 5",
                    adres_l2="11-111 Katowice",
                ),
                wysylka_przez=[
                    Tadres(
                        kod_kraju=TkodKraju.PL,
                        adres_l1="ul. Niebieska 27",
                        adres_l2='55-555 Lodz, Magazyn "B"',
                    )
                ],
                wysylka_do=Tadres(
                    kod_kraju=TkodKraju.PL,
                    adres_l1="ul. Szara 25",
                    adres_l2="22-222 Gdynia",
                ),
            )
        ],
        podmiot_posredniczacy=Twybor1.VALUE_1,
    )

    mapped = from_spec(schema)

    assert mapped.orders[0].order_date == date(2026, 9, 15)
    assert mapped.orders[0].order_number == "ZAM/182/2026"
    assert mapped.delivery_terms == "DAP"
    assert mapped.transports[0].transport_type == "road"
    assert mapped.transports[0].carrier_identity is not None
    assert mapped.transports[0].carrier_identity.tax_id == "9999999999"
    assert mapped.transports[0].carrier_identity.name == "Jan Nowak"
    assert mapped.transports[0].carrier_address is not None
    assert mapped.transports[0].carrier_address.address_line_1 == "ul. Pomaranczowa 12"
    assert mapped.transports[0].cargo_type == "carton"
    assert mapped.transports[0].packaging_unit == "1 karton/40 sztuk"
    assert mapped.transports[0].shipping_from is not None
    assert mapped.transports[0].shipping_from.address_line_2 == "11-111 Katowice"
    assert mapped.transports[0].shipping_via[0].address_line_1 == "ul. Niebieska 27"
    assert mapped.transports[0].shipping_to is not None
    assert mapped.transports[0].shipping_to.address_line_2 == "22-222 Gdynia"
    assert mapped.transports[0].transport_start == datetime(
        2026, 9, 25, 7, 34, tzinfo=timezone.utc
    )
    assert mapped.intermediary_entity is True
