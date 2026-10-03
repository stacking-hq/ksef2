"""FA(3) invoice header domain models."""

from datetime import datetime
from importlib.metadata import PackageNotFoundError, version

from pydantic import Field

from ksef2._domain.models import KSeFBaseModel


def _default_system_info() -> str:
    try:
        package_version = version("ksef2")
    except PackageNotFoundError:
        package_version = "unknown"
    return f"ksef2 sdk version: {package_version}"


class InvoiceHeader(KSeFBaseModel):
    """FA(3) invoice header.

    References:
        schemat.Tnaglowek

    Maps:
        generation_timestamp - data_wytworzenia_fa
        system_info - system_info
        <absent> - wariant_formularza = KodFormularza.VALUE_3
        <absent> - kod_systemowy = "FA (3)"
        <absent> - wersja_schemy = "1-0E"
    """

    generation_timestamp: datetime = Field(
        default_factory=datetime.now, description="Maps to Tnaglowek.DataWytworzeniaFA"
    )
    """When the invoice was generated (``DataWytworzeniaFa``). Defaults to the current time."""

    system_info: str | None = Field(
        default=None,
        max_length=256,
        description="Maps to Tnaglowek.SystemInfo",
    )
    """Name of the system that generated the invoice (``SystemInfo``, up to 256 characters)."""
