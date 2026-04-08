from datetime import datetime
from importlib.metadata import PackageNotFoundError, version

from pydantic import Field

from ksef2.domain.models import KSeFBaseModel


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

    system_info: str = Field(
        default_factory=_default_system_info,
        min_length=1,
        max_length=256,
        description="Maps to Tnaglowek.SystemInfo",
    )
