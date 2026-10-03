"""FA(3) additional description entry models."""

from pydantic import Field

from ksef2._domain.models import KSeFBaseModel


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
    """Number of the invoice row the entry refers to; ``None`` for the whole invoice (``NrWiersza``)."""
    key: str = Field(
        min_length=1,
        max_length=256,
        description="klucz: Additional description key.",
    )
    """Label of the entry (``Klucz``, 1–256 characters)."""
    value: str = Field(
        min_length=1,
        max_length=256,
        description="wartosc: Additional description value.",
    )
    """Value of the entry (``Wartosc``, 1–256 characters)."""
