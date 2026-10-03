"""Public FA(3) party domain models."""

import re
from typing import NamedTuple

from pydantic import field_validator, model_validator

from ksef2._domain.models.base import KSeFBaseModel


class ContactInfoTuple(NamedTuple):
    """Tuple representation of party contact email and phone."""

    email: str
    """Email address."""
    phone: str
    """Phone number."""


class ContactInfo(KSeFBaseModel):
    """Optional contact channels exposed on invoice parties."""

    email: str | None = None
    """Email address."""
    phone: str | None = None
    """Phone number."""


class InvoiceAddress(KSeFBaseModel):
    """Address shape aligned with FA(3) ``schemat.Tadres``."""

    country_code: str
    """Two-letter ISO 3166 country code."""
    address_line_1: str
    """First address line, usually street and building number."""
    address_line_2: str | None = None
    """Second address line, usually postal code and city."""
    gln: str | None = None
    """Global Location Number of the address."""

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
    """Polish NIP of the entity."""
    eu_vat_id: str | None = None
    """EU VAT identifier of the entity, including the country prefix."""
    other_id: str | None = None
    """Identifier of another kind, for entities without a NIP or EU VAT number."""
    eori_number: str | None = None
    """EORI number of the entity."""
    customer_number: str | None = None
    """Customer number assigned by the seller."""
    buyer_id: str | None = None
    """Unique identifier of the buyer assigned by the seller."""
    jst_subordinate_unit: bool = False
    """Whether the invoice is issued for a subordinate unit of a local government (JST)."""
    vat_group_member: bool = False
    """Whether the invoice is issued for a member of a VAT group."""
    vat_prefix: str | None = None
    """Country prefix of the EU VAT identifier."""
    name: str | None = None
    """Full name of the entity."""
    address: InvoiceAddress | None = None
    """Address of the entity."""
    contact: ContactInfo | None = None
    """Contact details of the entity."""

    @field_validator("eu_vat_id")
    @classmethod
    def _normalize_eu_vat_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.upper()

    @field_validator("vat_prefix")
    @classmethod
    def _normalize_vat_prefix(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.upper()
        if re.fullmatch(r"[A-Z]{2}", normalized) is None:
            raise ValueError("vat_prefix must be a 2-letter country code")
        return normalized

    @model_validator(mode="after")
    def _validate_polish_tax_id(self) -> "InvoiceEntity":
        if self.address is None:
            return self
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
