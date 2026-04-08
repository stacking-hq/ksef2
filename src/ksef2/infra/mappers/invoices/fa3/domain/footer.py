from ksef2.domain.models.fa3.footer import InvoiceFooter
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaStopka,
    FakturaStopkaRejestry,
    FakturaStopkaInformacje,
)


def to_spec(request: InvoiceFooter) -> FakturaStopka:
    return FakturaStopka(
        informacje=[
            FakturaStopkaInformacje(stopka_faktury=info)
            for info in request.additional_informations
        ],
        rejestry=[
            FakturaStopkaRejestry(
                pelna_nazwa=registry.full_name,
                krs=registry.krs,
                regon=registry.regon,
                bdo=registry.bdo,
            )
            for registry in request.registries
        ],
    )
