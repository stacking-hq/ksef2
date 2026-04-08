"""Mappings from FA(3) buyer schema models to domain objects."""

from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3 import ContactInfo, InvoiceEntity
from ksef2.infra.mappers.invoices.fa3.spec.subject import from_spec as subject_from_spec
from ksef2.infra.schema.fa3.models.schemat import FakturaPodmiot2


@overload
def from_spec(schema: FakturaPodmiot2) -> InvoiceEntity: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert an FA(3) buyer schema model into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: FakturaPodmiot2) -> InvoiceEntity:
    identity = schema.dane_identyfikacyjne
    eu_vat_id = (
        f"{identity.kod_ue.value}{identity.nr_vat_ue}"
        if identity.kod_ue is not None and identity.nr_vat_ue is not None
        else None
    )
    contact = None
    if schema.dane_kontaktowe:
        first = schema.dane_kontaktowe[0]
        if first.email is not None or first.telefon is not None:
            contact = ContactInfo(email=first.email, phone=first.telefon)

    return InvoiceEntity(
        tax_id=identity.nip,
        eu_vat_id=eu_vat_id,
        other_id=identity.nr_id,
        name=identity.nazwa,
        address=subject_from_spec(schema.adres) if schema.adres else None,
        contact=contact,
        customer_number=schema.nr_klienta,
        buyer_id=schema.idnabywcy,
        eori_number=schema.nr_eori,
        jst_subordinate_unit=schema.jst.name == "VALUE_1" if schema.jst else False,
        vat_group_member=schema.gv.name == "VALUE_1" if schema.gv else False,
    )
