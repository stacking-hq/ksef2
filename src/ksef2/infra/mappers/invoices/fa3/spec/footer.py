"""Mappings from FA(3) footer schema models to domain objects."""

from ksef2.domain.models.fa3.footer import FooterRegistry, InvoiceFooter
from ksef2.infra.schema.fa3.models.schemat import FakturaStopka


def from_spec(schema: FakturaStopka) -> InvoiceFooter:
    informations = [
        info.stopka_faktury
        for info in schema.informacje
        if info.stopka_faktury is not None
    ]
    registries = [
        FooterRegistry(
            full_name=registry.pelna_nazwa,
            krs=registry.krs,
            regon=registry.regon,
            bdo=registry.bdo,
        )
        for registry in schema.rejestry
    ]
    return InvoiceFooter(
        additional_informations=informations,
        registries=registries,
    )
