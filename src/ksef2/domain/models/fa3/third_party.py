"""Public FA(3) third-party domain models mapped to ``Faktura/Podmiot3``."""

import re
from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ksef2.domain.models.base import KSeFBaseModel
from ksef2.domain.models.fa3.party import ContactInfo, InvoiceAddress

ThirdPartyRole = Literal[
    "factor",
    "recipient",
    "original_subject",
    "additional_buyer",
    "issuer",
    "payer",
    "jst_issuer",
    "jst_recipient",
    "vat_group_issuer",
    "vat_group_recipient",
    "employee",
]


class InvoiceThirdParty(KSeFBaseModel):
    """Additional FA(3) subject stored in the repeated ``Faktura/Podmiot3`` block."""

    tax_id: str | None = None
    internal_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="dane_identyfikacyjne/idwew: Internal identifier paired with NIP.",
    )
    eu_vat_id: str | None = None
    country_code: str | None = Field(
        default=None,
        description="dane_identyfikacyjne/kod_kraju: Country of a non-EU alternate identifier.",
    )
    other_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="dane_identyfikacyjne/nr_id: Alternate tax identifier.",
    )
    no_id: bool = False
    name: str
    address: InvoiceAddress | None = None
    correspondence_address: InvoiceAddress | None = Field(
        default=None,
        description="adres_koresp: Optional mailing address for the third party.",
    )
    contact: list[ContactInfo] | ContactInfo | None = None
    role: ThirdPartyRole | None = Field(
        default=None,
        description="rola: Enumerated role of the third party on the invoice.",
    )
    other_role: bool = Field(
        default=False,
        description="rola_inna: Marks the third party as an unlisted custom role.",
    )
    role_description: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="opis_roli: Description required when other_role is selected.",
    )
    share_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        description="udzial: Participation share of an additional buyer.",
    )
    customer_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="nr_klienta: Customer number used for the third party.",
    )
    eori_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="nr_eori: EORI number of the third party.",
    )
    buyer_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        description="idnabywcy: Buyer linkage key used for additional buyers and corrections.",
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
    def _validate_identity_and_role_fields(self) -> "InvoiceThirdParty":
        if self.no_id and any(
            value is not None
            for value in (
                self.tax_id,
                self.internal_id,
                self.eu_vat_id,
                self.other_id,
            )
        ):
            raise ValueError("no_id cannot be combined with other identifiers")

        if self.country_code == "PL" and self.tax_id is not None:
            if re.fullmatch(r"\d{10}", self.tax_id) is None:
                raise ValueError(
                    "tax_id must be exactly 10 digits when country_code is PL"
                )

        if self.other_id is not None and self.country_code is None:
            raise ValueError("country_code is required when other_id is provided")

        if self.other_role and self.role_description is None:
            raise ValueError("role_description is required when other_role is True")

        if not self.other_role and self.role_description is not None:
            raise ValueError("role_description requires other_role to be True")

        return self
