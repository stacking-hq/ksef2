"""Mappings from FA(3) seller domain models to generated schema models."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.domain.models.fa3 import ContactInfo, InvoiceEntity
from ksef2.infra.mappers.invoices.fa3.domain.subject import to_spec as subject_to_spec
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaPodmiot1,
    FakturaPodmiot1DaneKontaktowe,
    TkodyKrajowUe,
    Tpodmiot1,
)


def _map_contact_details(
    contact: ContactInfo | None,
) -> list[FakturaPodmiot1DaneKontaktowe]:
    if contact is None or (contact.email is None and contact.phone is None):
        return []

    return [
        FakturaPodmiot1DaneKontaktowe(
            # Seller contact e-mail exposed in the repeated FA(3) contact block.
            email=contact.email,
            # Seller contact phone exposed in the repeated FA(3) contact block.
            telefon=contact.phone,
        )
    ]


def _map_vat_prefix(prefix: str | None) -> TkodyKrajowUe | None:
    if prefix is None:
        return None
    try:
        return TkodyKrajowUe[prefix.upper()]
    except KeyError:
        raise ValueError(f"Unsupported FA(3) VAT prefix: {prefix}") from None


@overload
def to_spec(request: InvoiceEntity) -> FakturaPodmiot1: ...


@overload
def to_spec(request: BaseModel) -> object: ...


def to_spec(request: BaseModel) -> object:
    """Convert a seller domain model into the FA(3) seller schema."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: InvoiceEntity) -> FakturaPodmiot1:
    if request.tax_id is None:
        raise ValueError("Seller tax_id is required for FA(3) mapping")
    if request.name is None:
        raise ValueError("Seller name is required for FA(3) mapping")
    if request.address is None:
        raise ValueError("Seller address is required for FA(3) mapping")

    return FakturaPodmiot1(
        prefiks_podatnika=_map_vat_prefix(request.vat_prefix),
        nr_eori=request.eori_number,
        dane_identyfikacyjne=Tpodmiot1(
            nip=request.tax_id,
            nazwa=request.name,
        ),
        adres=subject_to_spec(request.address),
        # Repeated FA(3) contact block used to publish seller e-mail/phone details.
        dane_kontaktowe=_map_contact_details(request.contact),
    )
