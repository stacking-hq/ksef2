"""FA(3) correction invoice context models."""

import re
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ksef2.domain.models import KSeFBaseModel
from ksef2.domain.models.fa3.references import CorrectedInvoiceReference
from ksef2.domain.models.fa3.party import InvoiceAddress

CorrectionEffectType = Literal[
    "original_entry_date",
    "correction_issue_date",
    "other_date",
]


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


class CorrectionInvoiceContext(KSeFBaseModel):
    """FA(3) correction-specific body data.

    References:
        schemat.FakturaFa

    Maps:
        correction_reason - przyczyna_korekty (str)
        correction_effect_type - typ_korekty (CorrectionEffectType)
        corrected_invoices - dane_fa_korygowanej (list[CorrectedInvoiceReference])
        corrected_invoice_period - okres_fa_korygowanej (str)
        corrected_invoice_number_override - nr_fa_korygowany (str)
        corrected_seller - podmiot1_k (CorrectedSellerEntity)
        corrected_buyers - podmiot2_k (list[CorrectedBuyerEntity])
    """

    correction_reason: str | None = Field(
        default=None,
        description="przyczyna_korekty: Optional correction reason.",
    )
    correction_effect_type: CorrectionEffectType | None = Field(
        default=None,
        description="typ_korekty: VAT register impact timing for the correction.",
    )
    corrected_invoices: list[CorrectedInvoiceReference] = Field(
        default_factory=list,
        description="dane_fa_korygowanej: References to corrected invoices.",
    )
    corrected_invoice_period: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="okres_fa_korygowanej: Period to which the discount/reduction applies.",
    )
    corrected_invoice_number_override: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="nr_fa_korygowany: Correct invoice number replacing an incorrect one.",
    )
    corrected_seller: CorrectedSellerEntity | None = Field(
        default=None,
        description="podmiot1_k: Seller data from the corrected invoice.",
    )
    corrected_buyers: list[CorrectedBuyerEntity] = Field(
        default_factory=list,
        description="podmiot2_k: Buyer data from the corrected invoice.",
    )
