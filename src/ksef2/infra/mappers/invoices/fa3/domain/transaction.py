"""Mappings between FA(3) transaction domain models and generated schema models."""

from datetime import date, datetime
from decimal import Decimal
from functools import singledispatch
from typing import overload

from pydantic import BaseModel
from xsdata.models.datatype import XmlDateTime

from ksef2.domain.models.fa3.body.transaction import (
    CargoType,
    TransactionAddress,
    TransactionConditions,
    TransactionContract,
    TransactionIdentity,
    TransactionOrder,
    TransactionTransport,
    TransportType,
)
from ksef2.infra.mappers.helpers import to_aware_datetime
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaWarunkiTransakcji,
    FakturaFaWarunkiTransakcjiTransport,
    FakturaFaWarunkiTransakcjiTransportPrzewoznik,
    FakturaFaWarunkiTransakcjiUmowy,
    FakturaFaWarunkiTransakcjiZamowienia,
    Tadres,
    TkodWaluty,
    TkodyKrajowUe,
    Tladunek,
    Tpodmiot2,
    TrodzajTransportu,
)


def _format_decimal(value: Decimal) -> str:
    return format(value, "f")


def _to_country_code(value: str) -> TkodKraju:
    try:
        return TkodKraju[value.upper()]
    except KeyError:
        raise ValueError(f"Unsupported FA(3) country code: {value}") from None


def _from_country_code(value: TkodKraju | str) -> str:
    if isinstance(value, str):
        return value
    return value.name


def _to_currency(value: str) -> TkodWaluty:
    try:
        return TkodWaluty(value.upper())
    except ValueError:
        raise ValueError(f"Unsupported FA(3) currency code: {value}") from None


def _split_eu_vat_id(eu_vat_id: str | None) -> tuple[TkodyKrajowUe | None, str | None]:
    if eu_vat_id is None:
        return None, None
    if len(eu_vat_id) < 3:
        raise ValueError("eu_vat_id must contain a 2-letter country prefix and number")

    country_prefix = eu_vat_id[:2].upper()
    vat_number = eu_vat_id[2:]

    try:
        return TkodyKrajowUe[country_prefix], vat_number
    except KeyError:
        raise ValueError(f"Unsupported FA(3) EU VAT prefix: {country_prefix}") from None


def _join_eu_vat_id(prefix: TkodyKrajowUe | None, vat_number: str | None) -> str | None:
    if prefix is None or vat_number is None:
        return None
    return f"{prefix.name}{vat_number}"


def _to_xml_datetime(value: datetime) -> XmlDateTime:
    return XmlDateTime.from_datetime(to_aware_datetime(value))


def _from_xml_datetime(value: XmlDateTime) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _map_transport_type(value: TransportType) -> TrodzajTransportu:
    transport_type_map: dict[TransportType, TrodzajTransportu] = {
        "sea": TrodzajTransportu.VALUE_1,
        "rail": TrodzajTransportu.VALUE_2,
        "road": TrodzajTransportu.VALUE_3,
        "air": TrodzajTransportu.VALUE_4,
        "postal": TrodzajTransportu.VALUE_5,
        "pipeline": TrodzajTransportu.VALUE_7,
        "inland_waterway": TrodzajTransportu.VALUE_8,
    }
    return transport_type_map[value]


def _from_transport_type(value: TrodzajTransportu) -> TransportType:
    transport_type_map: dict[TrodzajTransportu, TransportType] = {
        TrodzajTransportu.VALUE_1: "sea",
        TrodzajTransportu.VALUE_2: "rail",
        TrodzajTransportu.VALUE_3: "road",
        TrodzajTransportu.VALUE_4: "air",
        TrodzajTransportu.VALUE_5: "postal",
        TrodzajTransportu.VALUE_7: "pipeline",
        TrodzajTransportu.VALUE_8: "inland_waterway",
    }
    return transport_type_map[value]


def _map_cargo_type(value: CargoType) -> Tladunek:
    cargo_type_map: dict[CargoType, Tladunek] = {
        "demijohn": Tladunek.VALUE_1,
        "barrel": Tladunek.VALUE_2,
        "cylinder": Tladunek.VALUE_3,
        "carton": Tladunek.VALUE_4,
        "canister": Tladunek.VALUE_5,
        "crate": Tladunek.VALUE_6,
        "container": Tladunek.VALUE_7,
        "basket": Tladunek.VALUE_8,
        "punnet": Tladunek.VALUE_9,
        "bulk_package": Tladunek.VALUE_10,
        "parcel": Tladunek.VALUE_11,
        "bundle": Tladunek.VALUE_12,
        "pallet": Tladunek.VALUE_13,
        "bin": Tladunek.VALUE_14,
        "dry_bulk_container": Tladunek.VALUE_15,
        "liquid_bulk_container": Tladunek.VALUE_16,
        "box": Tladunek.VALUE_17,
        "can": Tladunek.VALUE_18,
        "chest": Tladunek.VALUE_19,
        "bag": Tladunek.VALUE_20,
    }
    return cargo_type_map[value]


def _from_cargo_type(value: Tladunek) -> CargoType:
    cargo_type_map: dict[Tladunek, CargoType] = {
        Tladunek.VALUE_1: "demijohn",
        Tladunek.VALUE_2: "barrel",
        Tladunek.VALUE_3: "cylinder",
        Tladunek.VALUE_4: "carton",
        Tladunek.VALUE_5: "canister",
        Tladunek.VALUE_6: "crate",
        Tladunek.VALUE_7: "container",
        Tladunek.VALUE_8: "basket",
        Tladunek.VALUE_9: "punnet",
        Tladunek.VALUE_10: "bulk_package",
        Tladunek.VALUE_11: "parcel",
        Tladunek.VALUE_12: "bundle",
        Tladunek.VALUE_13: "pallet",
        Tladunek.VALUE_14: "bin",
        Tladunek.VALUE_15: "dry_bulk_container",
        Tladunek.VALUE_16: "liquid_bulk_container",
        Tladunek.VALUE_17: "box",
        Tladunek.VALUE_18: "can",
        Tladunek.VALUE_19: "chest",
        Tladunek.VALUE_20: "bag",
    }
    return cargo_type_map[value]


@overload
def to_spec(request: TransactionConditions) -> FakturaFaWarunkiTransakcji: ...


@overload
def to_spec(request: TransactionContract) -> FakturaFaWarunkiTransakcjiUmowy: ...


@overload
def to_spec(request: TransactionOrder) -> FakturaFaWarunkiTransakcjiZamowienia: ...


@overload
def to_spec(
    request: TransactionTransport,
) -> FakturaFaWarunkiTransakcjiTransport: ...


@overload
def to_spec(request: TransactionIdentity) -> Tpodmiot2: ...


@overload
def to_spec(request: TransactionAddress) -> Tadres: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a transaction domain model into the FA(3) transaction schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: TransactionConditions) -> FakturaFaWarunkiTransakcji:
    contracts = [to_spec(contract) for contract in request.contracts]
    orders = [to_spec(order) for order in request.orders]
    contract_exchange_rate = (
        _format_decimal(request.contract_exchange_rate)
        if request.contract_exchange_rate is not None
        else None
    )
    contract_currency = (
        _to_currency(request.contract_currency) if request.contract_currency else None
    )
    transports = [to_spec(transport) for transport in request.transports]

    return FakturaFaWarunkiTransakcji(
        umowy=contracts,
        zamowienia=orders,
        nr_partii_towaru=request.lot_numbers,
        warunki_dostawy=request.delivery_terms,
        kurs_umowny=contract_exchange_rate,
        waluta_umowna=contract_currency,
        transport=transports,
        podmiot_posredniczacy=Twybor1.VALUE_1 if request.intermediary_entity else None,
    )


@_to_spec.register
def _(request: TransactionContract) -> FakturaFaWarunkiTransakcjiUmowy:
    contract_date = (
        request.contract_date.isoformat() if request.contract_date is not None else None
    )

    return FakturaFaWarunkiTransakcjiUmowy(
        data_umowy=contract_date,
        nr_umowy=request.contract_number,
    )


@_to_spec.register
def _(request: TransactionOrder) -> FakturaFaWarunkiTransakcjiZamowienia:
    order_date = (
        request.order_date.isoformat() if request.order_date is not None else None
    )

    return FakturaFaWarunkiTransakcjiZamowienia(
        data_zamowienia=order_date,
        nr_zamowienia=request.order_number,
    )


@_to_spec.register
def _(request: TransactionTransport) -> FakturaFaWarunkiTransakcjiTransport:
    transport_type = (
        _map_transport_type(request.transport_type) if request.transport_type else None
    )
    carrier = None
    if request.carrier_identity and request.carrier_address:
        carrier_identity = to_spec(request.carrier_identity)
        carrier_address = to_spec(request.carrier_address)
        carrier = FakturaFaWarunkiTransakcjiTransportPrzewoznik(
            dane_identyfikacyjne=carrier_identity,
            adres_przewoznika=carrier_address,
        )
    cargo_type = _map_cargo_type(request.cargo_type) if request.cargo_type else None
    transport_start = (
        _to_xml_datetime(request.transport_start) if request.transport_start else None
    )
    transport_end = (
        _to_xml_datetime(request.transport_end) if request.transport_end else None
    )
    shipping_from = to_spec(request.shipping_from) if request.shipping_from else None
    shipping_via = [to_spec(address) for address in request.shipping_via]
    shipping_to = to_spec(request.shipping_to) if request.shipping_to else None

    return FakturaFaWarunkiTransakcjiTransport(
        rodzaj_transportu=transport_type,
        transport_inny=Twybor1.VALUE_1 if request.other_transport else None,
        opis_innego_transportu=request.other_transport_description,
        przewoznik=carrier,
        nr_zlecenia_transportu=request.transport_order_number,
        opis_ladunku=cargo_type,
        ladunek_inny=Twybor1.VALUE_1 if request.other_cargo else None,
        opis_innego_ladunku=request.other_cargo_description,
        jednostka_opakowania=request.packaging_unit,
        data_godz_rozp_transportu=transport_start,
        data_godz_zak_transportu=transport_end,
        wysylka_z=shipping_from,
        wysylka_przez=shipping_via,
        wysylka_do=shipping_to,
    )


@_to_spec.register
def _(request: TransactionIdentity) -> Tpodmiot2:
    kod_ue, nr_vat_ue = _split_eu_vat_id(request.eu_vat_id)
    country_code = (
        _to_country_code(request.country_code) if request.country_code else None
    )

    return Tpodmiot2(
        nip=request.tax_id,
        kod_ue=kod_ue,
        nr_vat_ue=nr_vat_ue,
        kod_kraju=country_code,
        nr_id=request.other_id,
        brak_id=Twybor1.VALUE_1 if request.no_id else None,
        nazwa=request.name,
    )


@_to_spec.register
def _(request: TransactionAddress) -> Tadres:
    return Tadres(
        kod_kraju=_to_country_code(request.country_code),
        adres_l1=request.address_line_1,
        adres_l2=request.address_line_2,
        gln=request.gln,
    )


@overload
def from_spec(schema: FakturaFaWarunkiTransakcji) -> TransactionConditions: ...


@overload
def from_spec(schema: FakturaFaWarunkiTransakcjiUmowy) -> TransactionContract: ...


@overload
def from_spec(schema: FakturaFaWarunkiTransakcjiZamowienia) -> TransactionOrder: ...


@overload
def from_spec(
    schema: FakturaFaWarunkiTransakcjiTransport,
) -> TransactionTransport: ...


@overload
def from_spec(schema: Tpodmiot2) -> TransactionIdentity: ...


@overload
def from_spec(schema: Tadres) -> TransactionAddress: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert an FA(3) transaction schema model into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: FakturaFaWarunkiTransakcji) -> TransactionConditions:
    contracts = [from_spec(contract) for contract in schema.umowy]
    orders = [from_spec(order) for order in schema.zamowienia]
    contract_exchange_rate = (
        Decimal(schema.kurs_umowny) if schema.kurs_umowny is not None else None
    )
    contract_currency = schema.waluta_umowna.value if schema.waluta_umowna else None
    transports = [from_spec(transport) for transport in schema.transport]

    return TransactionConditions(
        contracts=contracts,
        orders=orders,
        lot_numbers=schema.nr_partii_towaru,
        delivery_terms=schema.warunki_dostawy,
        contract_exchange_rate=contract_exchange_rate,
        contract_currency=contract_currency,
        transports=transports,
        intermediary_entity=schema.podmiot_posredniczacy == Twybor1.VALUE_1,
    )


@_from_spec.register
def _(schema: FakturaFaWarunkiTransakcjiUmowy) -> TransactionContract:
    contract_date = (
        date.fromisoformat(schema.data_umowy) if schema.data_umowy is not None else None
    )

    return TransactionContract(
        contract_date=contract_date,
        contract_number=schema.nr_umowy,
    )


@_from_spec.register
def _(schema: FakturaFaWarunkiTransakcjiZamowienia) -> TransactionOrder:
    order_date = (
        date.fromisoformat(schema.data_zamowienia)
        if schema.data_zamowienia is not None
        else None
    )

    return TransactionOrder(
        order_date=order_date,
        order_number=schema.nr_zamowienia,
    )


@_from_spec.register
def _(schema: FakturaFaWarunkiTransakcjiTransport) -> TransactionTransport:
    transport_type = (
        _from_transport_type(schema.rodzaj_transportu)
        if schema.rodzaj_transportu
        else None
    )
    carrier_identity = None
    carrier_address = None
    if schema.przewoznik:
        carrier_identity = from_spec(schema.przewoznik.dane_identyfikacyjne)
        carrier_address = from_spec(schema.przewoznik.adres_przewoznika)
    cargo_type = _from_cargo_type(schema.opis_ladunku) if schema.opis_ladunku else None
    transport_start = (
        _from_xml_datetime(schema.data_godz_rozp_transportu)
        if schema.data_godz_rozp_transportu
        else None
    )
    transport_end = (
        _from_xml_datetime(schema.data_godz_zak_transportu)
        if schema.data_godz_zak_transportu
        else None
    )
    shipping_from = from_spec(schema.wysylka_z) if schema.wysylka_z else None
    shipping_via = [from_spec(address) for address in schema.wysylka_przez]
    shipping_to = from_spec(schema.wysylka_do) if schema.wysylka_do else None

    return TransactionTransport(
        transport_type=transport_type,
        other_transport=schema.transport_inny == Twybor1.VALUE_1,
        other_transport_description=schema.opis_innego_transportu,
        carrier_identity=carrier_identity,
        carrier_address=carrier_address,
        transport_order_number=schema.nr_zlecenia_transportu,
        cargo_type=cargo_type,
        other_cargo=schema.ladunek_inny == Twybor1.VALUE_1,
        other_cargo_description=schema.opis_innego_ladunku,
        packaging_unit=schema.jednostka_opakowania,
        transport_start=transport_start,
        transport_end=transport_end,
        shipping_from=shipping_from,
        shipping_via=shipping_via,
        shipping_to=shipping_to,
    )


@_from_spec.register
def _(schema: Tpodmiot2) -> TransactionIdentity:
    return TransactionIdentity(
        tax_id=schema.nip,
        eu_vat_id=_join_eu_vat_id(schema.kod_ue, schema.nr_vat_ue),
        country_code=_from_country_code(schema.kod_kraju) if schema.kod_kraju else None,
        other_id=schema.nr_id,
        no_id=schema.brak_id == Twybor1.VALUE_1,
        name=schema.nazwa,
    )


@_from_spec.register
def _(schema: Tadres) -> TransactionAddress:
    return TransactionAddress(
        country_code=_from_country_code(schema.kod_kraju),
        address_line_1=schema.adres_l1,
        address_line_2=schema.adres_l2,
        gln=schema.gln,
    )
