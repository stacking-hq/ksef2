"""Public FA(3) invoice domain models."""

import re
from decimal import Decimal
from datetime import date, datetime
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from ksef2.domain.models.base import KSeFBaseModel
from ksef2.domain.models.fa3.body import KsefInvoiceBody
from ksef2 import __version__


class InvoiceDetails(KSeFBaseModel):
    """Minimal invoice details needed by the public FA(3) layer."""

    invoice_number: str
    issue_date: date
    currency: str = "PLN"


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
        default=f"ksef2 sdk version: {__version__.version}",
        min_length=1,
        max_length=256,
        description="Maps to Tnaglowek.SystemInfo",
    )


class ContactInfo(KSeFBaseModel):
    """Optional contact channels exposed on invoice parties."""

    email: str | None = None
    phone: str | None = None


class InvoiceAddress(KSeFBaseModel):
    """Address shape aligned with FA(3) ``schemat.Tadres``."""

    country_code: str
    address_line_1: str
    address_line_2: str | None = None
    gln: str | None = None

    @field_validator("country_code")
    @classmethod
    def _validate_country_code(cls, value: str) -> str:
        normalized = value.upper()
        if re.fullmatch(r"[A-Z]{2}", normalized) is None:
            raise ValueError("country_code must be a 2-letter ISO code")
        return normalized


class InvoiceEntity(KSeFBaseModel):
    """Seller or buyer domain entity used by the public FA(3) invoice API."""

    tax_id: str | None = None
    eu_vat_id: str | None = None
    customer_number: str | None = None
    name: str
    address: InvoiceAddress
    contact: ContactInfo | None = None

    @field_validator("eu_vat_id")
    @classmethod
    def _normalize_eu_vat_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.upper()

    @model_validator(mode="after")
    def _validate_polish_tax_id(self) -> "InvoiceEntity":
        if self.address.country_code == "PL" and self.tax_id is not None:
            if re.fullmatch(r"\d{10}", self.tax_id) is None:
                raise ValueError(
                    "tax_id must be exactly 10 digits when country_code is PL"
                )
        if (
            self.address.country_code != "PL"
            and self.tax_id is not None
            and self.eu_vat_id is None
        ):
            raise ValueError(
                "eu_vat_id is required when tax_id is provided for non-Polish entities"
            )
        return self


class KsefInvoice(KSeFBaseModel):
    """Root public aggregate for a minimal FA(3) invoice draft."""

    invoice_header: Annotated[
        InvoiceHeader, Field(description="Maps to Faktura.Naglowek")
    ]

    seller: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot1")]
    buyer: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot2")]

    body: Annotated[KsefInvoiceBody, Field(description="Maps to Faktura.Fa")]

    @property
    def total_gross(self) -> Decimal:
        return self.body.total_gross

    @property
    def total_net(self) -> Decimal:
        return self.body.total_net

    @property
    def total_vat(self) -> Decimal:
        return self.body.total_vat

    @model_validator(mode="after")
    def _validate_seller_tax_id(self) -> "KsefInvoice":
        if not self.seller.tax_id:
            raise ValueError("seller tax_id is required")
        return self
