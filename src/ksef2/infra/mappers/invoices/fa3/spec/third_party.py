"""Mappings from FA(3) third-party schema models to domain objects."""

from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3.party import ContactInfo
from ksef2.domain.models.fa3.third_party import InvoiceThirdParty, ThirdPartyRole
from ksef2.infra.mappers.invoices.fa3.spec.subject import from_spec as subject_from_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.schemat import FakturaPodmiot3, TrolaPodmiotu3


@overload
def from_spec(schema: FakturaPodmiot3) -> InvoiceThirdParty: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert an FA(3) third-party schema model into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: FakturaPodmiot3) -> InvoiceThirdParty:
    identity = schema.dane_identyfikacyjne
    if identity.nazwa is None:
        raise ValueError("Third-party name is required for FA(3) mapping")
    eu_vat_id = (
        f"{identity.kod_ue.value}{identity.nr_vat_ue}"
        if identity.kod_ue is not None and identity.nr_vat_ue is not None
        else None
    )
    contact = None
    if schema.dane_kontaktowe:
        contacts = [
            ContactInfo(email=item.email, phone=item.telefon)
            for item in schema.dane_kontaktowe
            if item.email is not None or item.telefon is not None
        ]
        if contacts:
            contact = contacts[0] if len(contacts) == 1 else contacts

    role: ThirdPartyRole | None = None
    if schema.rola is not None:
        role_map: dict[TrolaPodmiotu3, ThirdPartyRole] = {
            TrolaPodmiotu3.VALUE_1: "factor",
            TrolaPodmiotu3.VALUE_2: "recipient",
            TrolaPodmiotu3.VALUE_3: "original_subject",
            TrolaPodmiotu3.VALUE_4: "additional_buyer",
            TrolaPodmiotu3.VALUE_5: "issuer",
            TrolaPodmiotu3.VALUE_6: "payer",
            TrolaPodmiotu3.VALUE_7: "jst_issuer",
            TrolaPodmiotu3.VALUE_8: "jst_recipient",
            TrolaPodmiotu3.VALUE_9: "vat_group_issuer",
            TrolaPodmiotu3.VALUE_10: "vat_group_recipient",
            TrolaPodmiotu3.VALUE_11: "employee",
        }
        role = role_map[schema.rola]

    return InvoiceThirdParty(
        tax_id=identity.nip,
        internal_id=identity.idwew,
        eu_vat_id=eu_vat_id,
        country_code=identity.kod_kraju.value if identity.kod_kraju else None,
        other_id=identity.nr_id,
        no_id=identity.brak_id == Twybor1.VALUE_1,
        name=identity.nazwa,
        address=subject_from_spec(schema.adres) if schema.adres else None,
        correspondence_address=subject_from_spec(schema.adres_koresp)
        if schema.adres_koresp
        else None,
        contact=contact,
        role=role,
        other_role=schema.rola_inna == Twybor1.VALUE_1,
        role_description=schema.opis_roli,
        share_percentage=schema.udzial,
        customer_number=schema.nr_klienta,
        eori_number=schema.nr_eori,
        buyer_id=schema.idnabywcy,
    )
