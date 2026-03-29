"""Public FA(3) invoice domain models."""

import re
from decimal import Decimal
from datetime import date, datetime
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from ksef2.domain.models.base import KSeFBaseModel


class InvoiceDetails(KSeFBaseModel):
    """Minimal invoice details needed by the public FA(3) layer."""

    invoice_number: str
    issue_date: date
    currency: str = "PLN"


class InvoiceLine(KSeFBaseModel):
    """Public FA(3) invoice-line model covering the full row payload."""

    name: str
    unit_of_measure: str = "szt"
    quantity: Decimal
    unit_price_net: Decimal
    net_amount: Decimal
    vat_rate: str
    vat_amount: Decimal
    unique_id: str | None = None
    supply_date: date | None = None
    sku: str | None = None
    gtin: str | None = None
    pkwiu: str | None = None
    cn: str | None = None
    pkob: str | None = None
    unit_price_gross: Decimal | None = None
    discount_amount: Decimal | None = None
    gross_amount: Decimal | None = None
    vat_rate_xii: Decimal | None = None
    annex_15_marker: bool | None = None
    excise_amount: Decimal | None = None
    gtu_code: str | None = None
    procedure: str | None = None
    currency_exchange_rate: Decimal | None = None
    before_correction: bool | None = None


class InvoiceHeader(KSeFBaseModel):
    generation_timestamp: datetime = Field(
        default_factory=datetime.now, description="Maps to Tnaglowek.DataWytworzeniaFA"
    )

    system_info: str = Field(
        default="ksef2-mcp server",
        max_length=250,
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


class KsefInvoiceBody(KSeFBaseModel):
    pass


class KsefInvoice(KSeFBaseModel):
    """Root public aggregate for a minimal FA(3) invoice draft."""

    invoice_header: Annotated[
        InvoiceHeader, Field(description="Maps to Faktura.Naglowek")
    ]

    seller: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot1")]
    buyer: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot2")]

    details: Annotated[
        InvoiceDetails, Field(description="Maps to selected Faktura.Fa fields")
    ]

    lines: Annotated[
        list[InvoiceLine],
        Field(min_length=1, description="Maps to Faktura.Fa.FaWiersz"),
    ]

    @property
    def total_gross(self) -> Decimal:
        return sum(
            (line.net_amount + line.vat_amount for line in self.lines),
            start=Decimal("0"),
        )

    @property
    def total_net(self) -> Decimal:
        return sum((line.net_amount for line in self.lines), start=Decimal("0"))

    @property
    def total_vat(self) -> Decimal:
        return sum((line.vat_amount for line in self.lines), start=Decimal("0"))

    @model_validator(mode="after")
    def _validate_seller_tax_id(self) -> "KsefInvoice":
        if not self.seller.tax_id:
            raise ValueError("seller tax_id is required")
        return self
