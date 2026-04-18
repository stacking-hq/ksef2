"""Mappings from FA(3) third-party domain models to generated schema models."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3.party import ContactInfo
from ksef2.domain.models.fa3.third_party import InvoiceThirdParty, ThirdPartyRole
from ksef2.infra.mappers.invoices.fa3.domain.subject import to_spec as subject_to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.kody_krajow_v10_0_e import TkodKraju
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaPodmiot3,
    FakturaPodmiot3DaneKontaktowe,
    TkodyKrajowUe,
    Tpodmiot3,
    TrolaPodmiotu3,
)


def _to_country_code(value: str) -> TkodKraju:
    try:
        return TkodKraju[value.upper()]
    except KeyError:
        raise ValueError(f"Unsupported FA(3) country code: {value}") from None


def _map_contact_details(
    contact: ContactInfo | list[ContactInfo] | None,
) -> list[FakturaPodmiot3DaneKontaktowe]:
    if contact is None:
        return []
    contacts = contact if isinstance(contact, list) else [contact]
    result: list[FakturaPodmiot3DaneKontaktowe] = []
    for item in contacts:
        if item.email is None and item.phone is None:
            continue
        result.append(
            FakturaPodmiot3DaneKontaktowe(
                email=item.email,
                telefon=item.phone,
            )
        )
    return result


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


def _map_identity_fields(
    request: InvoiceThirdParty,
) -> tuple[
    str | None,
    str | None,
    TkodyKrajowUe | None,
    str | None,
    TkodKraju | None,
    str | None,
    Twybor1 | None,
]:
    if request.tax_id is not None and request.country_code == "PL":
        return request.tax_id, None, None, None, None, None, None

    if request.internal_id is not None:
        return None, request.internal_id, None, None, None, None, None

    if request.eu_vat_id is not None:
        kod_ue, nr_vat_ue = _split_eu_vat_id(request.eu_vat_id)
        return None, None, kod_ue, nr_vat_ue, None, None, None

    if request.other_id is not None:
        country_code = request.country_code
        if country_code is None:
            raise ValueError("country_code is required when other_id is provided")
        return (
            None,
            None,
            None,
            None,
            _to_country_code(country_code),
            request.other_id,
            None,
        )

    if request.tax_id is not None:
        return request.tax_id, None, None, None, None, None, None

    if request.no_id:
        return None, None, None, None, None, None, Twybor1.VALUE_1

    return None, None, None, None, None, None, Twybor1.VALUE_1


def _map_role(value: ThirdPartyRole | None) -> TrolaPodmiotu3 | None:
    if value is None:
        return None

    if value == "factor":
        return TrolaPodmiotu3.VALUE_1
    if value == "recipient":
        return TrolaPodmiotu3.VALUE_2
    if value == "original_subject":
        return TrolaPodmiotu3.VALUE_3
    if value == "additional_buyer":
        return TrolaPodmiotu3.VALUE_4
    if value == "issuer":
        return TrolaPodmiotu3.VALUE_5
    if value == "payer":
        return TrolaPodmiotu3.VALUE_6
    if value == "jst_issuer":
        return TrolaPodmiotu3.VALUE_7
    if value == "jst_recipient":
        return TrolaPodmiotu3.VALUE_8
    if value == "vat_group_issuer":
        return TrolaPodmiotu3.VALUE_9
    if value == "vat_group_recipient":
        return TrolaPodmiotu3.VALUE_10
    return TrolaPodmiotu3.VALUE_11


@overload
def to_spec(request: InvoiceThirdParty) -> FakturaPodmiot3: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a third-party domain model into the FA(3) third-party schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: InvoiceThirdParty) -> FakturaPodmiot3:
    nip, idwew, kod_ue, nr_vat_ue, kod_kraju, nr_id, brak_id = _map_identity_fields(
        request
    )

    return FakturaPodmiot3(
        idnabywcy=request.buyer_id,
        nr_eori=request.eori_number,
        dane_identyfikacyjne=Tpodmiot3(
            nip=nip,
            idwew=idwew,
            kod_ue=kod_ue,
            nr_vat_ue=nr_vat_ue,
            kod_kraju=kod_kraju,
            nr_id=nr_id,
            brak_id=brak_id,
            nazwa=request.name,
        ),
        adres=subject_to_spec(request.address) if request.address else None,
        adres_koresp=(
            subject_to_spec(request.correspondence_address)
            if request.correspondence_address
            else None
        ),
        dane_kontaktowe=_map_contact_details(request.contact),
        rola=_map_role(request.role),
        rola_inna=Twybor1.VALUE_1 if request.other_role else None,
        opis_roli=request.role_description,
        udzial=request.share_percentage,
        nr_klienta=request.customer_number,
    )
