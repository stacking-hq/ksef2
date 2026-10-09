"""Unit tests for the branches of FA(3) schema-to-domain mapping not covered by samples."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from ksef2._domain.models.fa3.body import MarginProcedure, TaxRegime
from ksef2._domain.models.fa3.header import _default_system_info
from ksef2._infra.mappers.invoices.fa3.spec.annotations import (
    from_spec as annotations_from_spec,
)
from ksef2._infra.mappers.invoices.fa3.spec.buyer import from_spec as buyer_from_spec
from ksef2._infra.mappers.invoices.fa3.spec.correction_party import (
    from_spec as correction_party_from_spec,
)
from ksef2._infra.mappers.invoices.fa3.spec.footer import from_spec as footer_from_spec
from ksef2._infra.mappers.invoices.fa3.spec.header import from_spec as header_from_spec
from ksef2._infra.mappers.invoices.fa3.spec.invoice import (
    from_spec as invoice_from_spec,
)
from ksef2._infra.mappers.invoices.fa3.spec.lines import from_spec as line_from_spec
from ksef2._infra.mappers.invoices.fa3.spec.seller import from_spec as seller_from_spec
from ksef2._infra.mappers.invoices.fa3.spec.subject import (
    from_spec as address_from_spec,
)
from ksef2._infra.mappers.invoices.fa3.spec.third_party import (
    from_spec as third_party_from_spec,
)
from ksef2._infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor1,
    Twybor12,
)
from ksef2._infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2._infra.schema.fa3.models.schemat import (
    FakturaFaAdnotacje,
    FakturaFaAdnotacjeNoweSrodkiTransportu,
    FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu,
    FakturaFaAdnotacjePmarzy,
    FakturaFaAdnotacjeZwolnienie,
    FakturaFaFaWiersz,
    FakturaFaPodmiot2K,
    FakturaPodmiot1,
    FakturaPodmiot2,
    FakturaPodmiot3,
    FakturaStopka,
    FakturaStopkaInformacje,
    FakturaStopkaRejestry,
    Tadres,
    TkodyKrajowUe,
    Tpodmiot1,
    Tpodmiot2,
    Tpodmiot3,
    TrolaPodmiotu3,
)
from tests.unit.mappers.test_fa3_spec_invoice import load_sample

# Some FA(3) elements are mandatory in the generated models while the mapper
# reads a missing element as absent; UNSET stands in for those.
UNSET: Any = None

ADDRESS = Tadres(kod_kraju=TkodKraju.PL, adres_l1="Marszalkowska 10/5")


def adnotacje(**overrides: Any) -> FakturaFaAdnotacje:
    """Build an annotation block with every unmentioned element left empty."""
    elements: dict[str, Any] = {
        "p_16": None,
        "p_17": None,
        "p_18": None,
        "p_18_a": None,
        "zwolnienie": None,
        "nowe_srodki_transportu": None,
        "p_23": None,
        "pmarzy": None,
    }
    elements.update(overrides)
    return FakturaFaAdnotacje(**elements)


def wiersz(**overrides: Any) -> FakturaFaFaWiersz:
    """Build an invoice line with only the elements the test cares about."""
    elements: dict[str, Any] = {"nr_wiersza_fa": 1, "p_7": "Consulting"}
    elements.update(overrides)
    return FakturaFaFaWiersz(**elements)


@pytest.mark.parametrize(
    "mapper",
    [
        address_from_spec,
        annotations_from_spec,
        buyer_from_spec,
        correction_party_from_spec,
        header_from_spec,
        invoice_from_spec,
        line_from_spec,
        seller_from_spec,
        third_party_from_spec,
    ],
)
def test_mapper_without_registered_schema_type_raises_not_implemented(
    mapper,
) -> None:
    with pytest.raises(NotImplementedError, match="No mapper registered"):
        mapper(object())


def transport_item(
    available_from: object,
    *,
    row_number: int,
    **elements: Any,
) -> FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu:
    item = FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu(
        p_22_a="1970-01-01", p_nr_wiersza_nst=row_number, **elements
    )
    # The mapper also accepts values a looser parser leaves unconverted.
    setattr(item, "p_22_a", available_from)
    return item


def test_annotations_absent_is_mapped_to_none() -> None:
    assert annotations_from_spec(adnotacje()) is None


@pytest.mark.parametrize(
    ("pmarzy", "expected"),
    [
        (
            FakturaFaAdnotacjePmarzy(p_pmarzy_2=Twybor1.VALUE_1),
            MarginProcedure.TRAVEL_AGENCY,
        ),
        (
            FakturaFaAdnotacjePmarzy(p_pmarzy_3_1=Twybor1.VALUE_1),
            MarginProcedure.USED_GOODS,
        ),
        (
            FakturaFaAdnotacjePmarzy(p_pmarzy_3_2=Twybor1.VALUE_1),
            MarginProcedure.ARTWORKS,
        ),
        (
            FakturaFaAdnotacjePmarzy(p_pmarzy_3_3=Twybor1.VALUE_1),
            MarginProcedure.COLLECTIBLES_AND_ANTIQUES,
        ),
    ],
)
def test_margin_procedure_maps_from_the_first_matching_marker(
    pmarzy: FakturaFaAdnotacjePmarzy,
    expected: MarginProcedure,
) -> None:
    annotations = annotations_from_spec(adnotacje(pmarzy=pmarzy))

    assert annotations is not None
    assert annotations.margin_procedure is expected


def test_annotations_map_flags_and_tax_exemption() -> None:
    annotations = annotations_from_spec(
        adnotacje(
            p_16=Twybor12.VALUE_1,
            p_17=Twybor12.VALUE_1,
            p_18=Twybor12.VALUE_1,
            p_18_a=Twybor12.VALUE_1,
            p_23=Twybor12.VALUE_1,
            zwolnienie=FakturaFaAdnotacjeZwolnienie(
                p_19=Twybor1.VALUE_1,
                p_19_b="art. 132 Dyrektywy 2006/112/WE",
            ),
        )
    )

    assert annotations is not None
    assert annotations.cash_accounting is True
    assert annotations.self_billing is True
    assert annotations.reverse_charge_annotation is True
    assert annotations.split_payment is True
    assert annotations.simplified_procedure is True
    assert annotations.tax_exemption is not None
    assert annotations.tax_exemption.legal_basis_act is None
    assert annotations.tax_exemption.legal_basis_eu_directive == (
        "art. 132 Dyrektywy 2006/112/WE"
    )
    assert annotations.tax_exemption.legal_basis_other is None


def test_maps_the_domestic_tax_exemption_basis() -> None:
    annotations = annotations_from_spec(
        adnotacje(
            zwolnienie=FakturaFaAdnotacjeZwolnienie(
                p_19=Twybor1.VALUE_1,
                p_19_a="art. 43 ust. 1 pkt 10 ustawy",
            )
        )
    )

    assert annotations is not None
    assert annotations.tax_exemption is not None
    assert annotations.tax_exemption.legal_basis_act == "art. 43 ust. 1 pkt 10 ustawy"


def test_several_exemption_bases_break_the_domain_rule() -> None:
    """The domain model accepts exactly one basis while the spec carries three."""
    with pytest.raises(ValidationError, match="Exactly one exemption legal basis"):
        annotations_from_spec(
            adnotacje(
                zwolnienie=FakturaFaAdnotacjeZwolnienie(
                    p_19=Twybor1.VALUE_1,
                    p_19_a="art. 43 ust. 1 pkt 10 ustawy",
                    p_19_b="art. 132 Dyrektywy 2006/112/WE",
                    p_19_c="umowa miedzynarodowa",
                )
            )
        )


def test_new_transport_supply_maps_items_and_the_article_42_5_marker() -> None:
    annotations = annotations_from_spec(
        adnotacje(
            nowe_srodki_transportu=FakturaFaAdnotacjeNoweSrodkiTransportu(
                p_22=Twybor1.VALUE_1,
                p_42_5=Twybor12.VALUE_1,
                nowy_srodek_transportu=[
                    transport_item(
                        date(2026, 3, 1),
                        row_number=1,
                        p_22_bmk="Volvo",
                        p_22_b1="YV2RT40A1KA123456",
                    ),
                    transport_item(
                        datetime(2026, 3, 2, 6, 30),
                        row_number=2,
                        p_22_b="1250",
                        p_22_c="17",
                        p_22_d="8",
                    ),
                    transport_item("2026-03-03", row_number=3),
                    transport_item("2026-03-04T06:30:00", row_number=4),
                ],
            )
        )
    )

    assert annotations is not None
    supply = annotations.new_transport_supply
    assert supply is not None
    assert supply.article_42_5_required is True
    assert [item.available_from for item in supply.items] == [
        date(2026, 3, 1),
        date(2026, 3, 2),
        date(2026, 3, 3),
        date(2026, 3, 4),
    ]
    assert supply.items[0].brand == "Volvo"
    assert supply.items[0].vin == "YV2RT40A1KA123456"
    assert supply.items[1].land_vehicle_mileage == "1250"
    assert supply.items[1].vessel_working_hours == "17"
    assert supply.items[1].aircraft_working_hours == "8"
    assert supply.items[2].brand is None


def test_new_transport_supply_without_items_or_marker_is_skipped() -> None:
    annotations = annotations_from_spec(
        adnotacje(
            p_16=Twybor12.VALUE_1,
            nowe_srodki_transportu=FakturaFaAdnotacjeNoweSrodkiTransportu(),
        )
    )

    assert annotations is not None
    assert annotations.new_transport_supply is None


def test_line_supply_date_accepts_datetime_date_and_iso_text() -> None:
    assert line_from_spec(wiersz(p_6_a=datetime(2026, 3, 4, 23, 59))).supply_date == (
        date(2026, 3, 4)
    )
    assert line_from_spec(wiersz(p_6_a=date(2026, 3, 5))).supply_date == date(
        2026, 3, 5
    )
    assert line_from_spec(wiersz(p_6_a="2026-03-06")).supply_date == date(2026, 3, 6)
    assert line_from_spec(wiersz(p_6_a="2026-03-06T00:00:00+01:00")).supply_date == (
        date(2026, 3, 5)
    )


def test_line_tax_regime_prefers_the_special_xii_rate() -> None:
    row = line_from_spec(
        wiersz(p_12_xii=Decimal("0.0730")),
        margin_procedure=MarginProcedure.USED_GOODS,
    )

    assert row.vat_rate_xii == Decimal("0.0730")
    assert row.tax_regime is TaxRegime.SPECIAL_XII


def test_line_tax_regime_falls_back_to_margin_without_a_vat_class() -> None:
    row = line_from_spec(
        wiersz(),
        margin_procedure=MarginProcedure.TRAVEL_AGENCY,
    )

    assert row.tax_regime is TaxRegime.MARGIN
    assert row.vat_rate is None


def test_line_maps_margin_when_no_procedure_is_given() -> None:
    row = line_from_spec(wiersz())

    assert row.tax_regime is TaxRegime.STANDARD


def test_body_accepts_datetime_and_date_supply_values() -> None:
    spec = load_sample("KSEF_01_VAT_STANDARD.xml")
    setattr(spec.fa, "p_6", datetime(2025, 12, 11, 8, 0))
    assert invoice_from_spec(spec).body.date_of_supply == date(2025, 12, 11)

    setattr(spec.fa, "p_6", date(2025, 12, 12))
    assert invoice_from_spec(spec).body.date_of_supply == date(2025, 12, 12)


def test_non_textual_currency_is_rejected() -> None:
    spec = load_sample("KSEF_01_VAT_STANDARD.xml")
    setattr(spec.fa, "kod_waluty", 123)

    with pytest.raises(
        ValueError, match="kod_waluty must be a string-compatible schema value"
    ):
        invoice_from_spec(spec)


def test_already_boolean_outside_ksef_marker_is_accepted() -> None:
    spec = load_sample("KSEF_02_KOR.xml")
    reference = spec.fa.dane_fa_korygowanej[0]
    setattr(reference, "nr_kse_fn", True)
    reference.nr_kse_ffa_korygowanej = None

    invoice = invoice_from_spec(spec)

    correction = invoice.body.correction
    assert correction is not None
    assert correction.corrected_invoices[0].outside_ksef is True


def test_third_party_without_name_is_rejected() -> None:
    schema = FakturaPodmiot3(
        dane_identyfikacyjne=Tpodmiot3(nazwa=None),
        adres=ADDRESS,
    )

    with pytest.raises(
        ValueError, match="Third-party name is required for FA\\(3\\) mapping"
    ):
        third_party_from_spec(schema)


def test_third_party_maps_role_and_correspondence_address() -> None:
    third_party = third_party_from_spec(
        FakturaPodmiot3(
            dane_identyfikacyjne=Tpodmiot3(nazwa="Spedycja Sp. z o.o."),
            adres=ADDRESS,
            adres_koresp=Tadres(kod_kraju=TkodKraju.DE, adres_l1="Unter den Linden 1"),
            nr_eori="PL123456789000",
            nr_klienta="K-1",
            rola=TrolaPodmiotu3.VALUE_5,
            rola_inna=Twybor1.VALUE_1,
            opis_roli="Wystawca",
        )
    )

    assert third_party.name == "Spedycja Sp. z o.o."
    assert third_party.eori_number == "PL123456789000"
    assert third_party.customer_number == "K-1"
    assert third_party.role == "issuer"
    assert third_party.other_role is True
    assert third_party.role_description == "Wystawca"
    assert third_party.correspondence_address is not None
    assert third_party.correspondence_address.country_code == "DE"


def test_corrected_buyer_without_name_is_rejected() -> None:
    schema = FakturaFaPodmiot2K(dane_identyfikacyjne=Tpodmiot2(nazwa=None))

    with pytest.raises(
        ValueError, match="Corrected buyer name is required for FA\\(3\\) mapping"
    ):
        correction_party_from_spec(schema)


def test_corrected_buyer_maps_eu_vat_and_country_identifiers() -> None:
    buyer = correction_party_from_spec(
        FakturaFaPodmiot2K(
            dane_identyfikacyjne=Tpodmiot2(
                kod_ue=TkodyKrajowUe.DE,
                nr_vat_ue="123456789",
                kod_kraju=TkodKraju.DE,
                nr_id="ALT-1",
                brak_id=None,
                nazwa="Old Buyer GmbH",
            ),
            adres=None,
            idnabywcy="BUYER-1",
        )
    )

    assert buyer.eu_vat_id == "DE123456789"
    assert buyer.country_code == "DE"
    assert buyer.other_id == "ALT-1"
    assert buyer.no_id is False
    assert buyer.address is None
    assert buyer.buyer_id == "BUYER-1"


def test_buyer_and_seller_map_without_an_entity_name() -> None:
    buyer = buyer_from_spec(
        FakturaPodmiot2(
            dane_identyfikacyjne=Tpodmiot2(nazwa=None, brak_id=Twybor1.VALUE_1),
            adres=ADDRESS,
            jst=UNSET,
            gv=UNSET,
        )
    )
    seller = seller_from_spec(
        FakturaPodmiot1(
            dane_identyfikacyjne=Tpodmiot1(nip="1234567890", nazwa=UNSET),
            adres=ADDRESS,
        )
    )

    assert buyer.name is None
    assert buyer.jst_subordinate_unit is False
    assert seller.name is None
    assert seller.tax_id == "1234567890"


def test_header_parses_textual_timestamp_and_defaults_system_info() -> None:
    spec = load_sample("KSEF_01_VAT_STANDARD.xml")
    setattr(spec.naglowek, "data_wytworzenia_fa", "2025-12-15T10:30:00+00:00")
    spec.naglowek.system_info = None

    header = header_from_spec(spec.naglowek)

    assert header.generation_timestamp == datetime(
        2025, 12, 15, 10, 30, tzinfo=timezone.utc
    )
    assert header.system_info == _default_system_info()


def test_footer_maps_informations_and_registries() -> None:
    footer = footer_from_spec(
        FakturaStopka(
            informacje=[
                FakturaStopkaInformacje(stopka_faktury="Informacja"),
                FakturaStopkaInformacje(stopka_faktury=None),
            ],
            rejestry=[
                FakturaStopkaRejestry(
                    pelna_nazwa="Seller Sp. z o.o.",
                    krs="0000123456",
                    regon="146025969",
                    bdo=None,
                )
            ],
        )
    )

    assert footer.additional_informations == ["Informacja"]
    assert footer.registries is not None
    assert footer.registries[0].full_name == "Seller Sp. z o.o."
    assert footer.registries[0].krs == "0000123456"
    assert footer.registries[0].bdo is None
