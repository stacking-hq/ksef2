"""FA(3) invoice footer domain models."""

from pydantic import Field, field_validator
from ksef2.domain.models import KSeFBaseModel


class FooterRegistry(KSeFBaseModel):
    """FA(3) invoice footer registry.

    References:
        schemat.FakturaStopka.FakturaStopkaRejestry

    Maps:
        full_name - pelna_nazwa
        krs - krs
        regon - regon
        bdo - bdo

    """

    full_name: str | None = Field(
        default=None,
        description="Maps to FakturaStopka.FakturaStopkaRejestry.PelnaNazwa",
        min_length=1,
        max_length=256,
    )
    krs: str | None = Field(
        default=None,
        description="Maps to FakturaStopka.FakturaStopkaRejestry.KRS",
        pattern=r"\d{10}",
    )
    regon: str | None = Field(
        default=None,
        description="Maps to FakturaStopka.FakturaStopkaRejestry.REGON",
        pattern=r"\d{9}|\d{14}",
    )
    bdo: str | None = Field(
        default=None,
        description="Maps to FakturaStopka.FakturaStopkaRejestry.BDO",
        min_length=1,
        max_length=9,
    )


class InvoiceFooter(KSeFBaseModel):
    """FA(3) invoice footer.

    References:
        schemat.FakturaStopka

    Maps:
        additional_informations - informacje = []
        registries - rejestry = []
    """

    additional_informations: list[str] = Field(
        default_factory=list,
        description="Maps to List[FakturaStopka.FakturaStopkaInformacje",
        max_length=3,
    )

    registries: list[FooterRegistry] = Field(
        default_factory=list,
        description="Maps to List[FakturaStopka.FakturaStopkaRejestry",
        max_length=100,
    )

    @field_validator("additional_informations")
    @classmethod
    def _validate_informations(cls, value: list[str]) -> list[str]:
        if any(len(x) > 3500 for x in value):
            raise ValueError(
                "Informations must not have elements longer than 3500 characters"
            )

        return value
