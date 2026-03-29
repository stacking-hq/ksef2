"""Mappings from FA(3) buyer domain models to generated schema models."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import ContactInfo, InvoiceEntity
from ksef2.infra.mappers.invoices.fa3.subject import to_spec as subject_to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaPodmiot2,
    FakturaPodmiot2DaneKontaktowe,
    FakturaPodmiot2Gv,
    FakturaPodmiot2Jst,
    TkodyKrajowUe,
    Tpodmiot2,
)


def _map_contact_details(
    contact: ContactInfo | None,
) -> list[FakturaPodmiot2DaneKontaktowe]:
    if contact is None or (contact.email is None and contact.phone is None):
        return []

    return [
        FakturaPodmiot2DaneKontaktowe(
            # Buyer contact e-mail exposed in the repeated FA(3) contact block.
            email=contact.email,
            # Buyer contact phone exposed in the repeated FA(3) contact block.
            telefon=contact.phone,
        )
    ]


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


@overload
def to_spec(request: InvoiceEntity) -> FakturaPodmiot2: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a buyer domain model into the FA(3) buyer schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: InvoiceEntity) -> FakturaPodmiot2:
    kod_ue, nr_vat_ue = _split_eu_vat_id(request.eu_vat_id)

    return FakturaPodmiot2(
        dane_identyfikacyjne=Tpodmiot2(
            # Polish NIP used when the buyer has a domestic tax identifier.
            nip=request.tax_id,
            # EU VAT prefix extracted from a cross-border buyer VAT number.
            kod_ue=kod_ue,
            # EU VAT number body stored separately from the country prefix in FA(3).
            nr_vat_ue=nr_vat_ue,
            # KSeF flag meaning "buyer identifier missing on the invoice".
            brak_id=Twybor1.VALUE_1 if request.tax_id is None else None,
            nazwa=request.name,
        ),
        adres=subject_to_spec(request.address),
        # Repeated FA(3) contact block used to publish buyer e-mail/phone details.
        dane_kontaktowe=_map_contact_details(request.contact),
        # ERP/customer contract identifier exposed as the FA(3) buyer customer number.
        nr_klienta=request.customer_number,
        # TODO: To support JST (Local Gov) and GV (VAT Groups), we must first implement
        # a 'Podmiot3' (Third Party/Recipient) domain model.
        # FA(3) flag value "2" means this invoice does not concern a JST sub-unit.
        jst=FakturaPodmiot2Jst.VALUE_2,
        # FA(3) flag value "2" means this invoice does not concern a VAT group member.
        gv=FakturaPodmiot2Gv.VALUE_2,
    )
