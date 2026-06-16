"""FA(3) additional description entry models."""

from pydantic import Field

from ksef2.domain.models import KSeFBaseModel


class AdditionalDescriptionEntry(KSeFBaseModel):
    """FA(3) additional invoice description entry.

    References:
        schemat.TkluczWartosc

    Maps:
        row_number - nr_wiersza (int)
        key - klucz (str)
        value - wartosc (str)
    """

    row_number: int | None = Field(
        default=None,
        gt=0,
        description="nr_wiersza: Optional invoice row number this entry refers to.",
    )
    key: str = Field(
        min_length=1,
        max_length=256,
        description="klucz: Additional description key.",
    )
    value: str = Field(
        min_length=1,
        max_length=256,
        description="wartosc: Additional description value.",
    )
