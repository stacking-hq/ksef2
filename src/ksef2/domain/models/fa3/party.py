"""Public FA(3) party domain models."""

import re

from pydantic import Field, field_validator, model_validator

from ksef2.domain.models.base import KSeFBaseModel


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


class CorrectedSellerEntity(KSeFBaseModel):
    """FA(3) corrected seller data stored in ``Fa/Podmiot1K``.

    References:
        schemat.FakturaFaPodmiot1K

    Maps:
        vat_prefix - prefiks_podatnika (TkodyKrajowUe)
        tax_id - dane_identyfikacyjne/nip (str)
        name - dane_identyfikacyjne/nazwa (str)
        address - adres (Tadres)
    """

    vat_prefix: str | None = Field(
        default=None,
        description="prefiks_podatnika: EU VAT prefix used in special correction cases.",
    )
    tax_id: str = Field(description="dane_identyfikacyjne/nip: Seller NIP.")
    name: str = Field(
        description="dane_identyfikacyjne/nazwa: Seller name from the corrected invoice."
    )
    address: InvoiceAddress = Field(description="adres: Seller address.")

    @field_validator("vat_prefix")
    @classmethod
    def _normalize_vat_prefix(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.upper()
        if re.fullmatch(r"[A-Z]{2}", normalized) is None:
            raise ValueError("vat_prefix must be a 2-letter country code")
        return normalized

    @field_validator("tax_id")
    @classmethod
    def _validate_tax_id(cls, value: str) -> str:
        if re.fullmatch(r"\d{10}", value) is None:
            raise ValueError("tax_id must be exactly 10 digits")
        return value


class CorrectedBuyerEntity(KSeFBaseModel):
    """FA(3) corrected buyer data stored in ``Fa/Podmiot2K``.

    References:
        schemat.FakturaFaPodmiot2K

    Maps:
        tax_id - dane_identyfikacyjne/nip (str)
        eu_vat_id - dane_identyfikacyjne/kod_ue + nr_vat_ue (str)
        country_code - dane_identyfikacyjne/kod_kraju (str)
        other_id - dane_identyfikacyjne/nr_id (str)
        no_id - dane_identyfikacyjne/brak_id (bool)
        name - dane_identyfikacyjne/nazwa (str)
        address - adres (Tadres)
        buyer_id - idnabywcy (str)
    """

    tax_id: str | None = None
    eu_vat_id: str | None = None
    country_code: str | None = None
    other_id: str | None = None
    no_id: bool = False
    name: str
    address: InvoiceAddress | None = None
    buyer_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        description="idnabywcy: Buyer linkage key used on corrections.",
    )

    @field_validator("eu_vat_id")
    @classmethod
    def _normalize_eu_vat_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.upper()

    @field_validator("country_code")
    @classmethod
    def _normalize_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.upper()
        if re.fullmatch(r"[A-Z]{2}", normalized) is None:
            raise ValueError("country_code must be a 2-letter ISO code")
        return normalized

    @model_validator(mode="after")
    def _validate_identifiers(self) -> "CorrectedBuyerEntity":
        if self.no_id and any(
            value is not None
            for value in (self.tax_id, self.eu_vat_id, self.country_code, self.other_id)
        ):
            raise ValueError("no_id cannot be combined with other identifiers")

        if self.country_code == "PL" and self.tax_id is not None:
            if re.fullmatch(r"\d{10}", self.tax_id) is None:
                raise ValueError(
                    "tax_id must be exactly 10 digits when country_code is PL"
                )

        return self
