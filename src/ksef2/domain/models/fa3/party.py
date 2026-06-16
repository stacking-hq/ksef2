"""Public FA(3) party domain models."""

import re
from typing import NamedTuple

from pydantic import field_validator, model_validator

from ksef2.domain.models.base import KSeFBaseModel


class ContactInfoTuple(NamedTuple):
    """Tuple representation of party contact email and phone."""

    email: str
    phone: str


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
    other_id: str | None = None
    eori_number: str | None = None
    customer_number: str | None = None
    buyer_id: str | None = None
    jst_subordinate_unit: bool = False
    vat_group_member: bool = False
    vat_prefix: str | None = None
    name: str | None = None
    address: InvoiceAddress | None = None
    contact: ContactInfo | None = None

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
