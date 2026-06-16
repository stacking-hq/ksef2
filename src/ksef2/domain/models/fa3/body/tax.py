"""VAT classification helpers used by FA(3) rows and summaries."""

from decimal import Decimal
from enum import StrEnum
from typing import Any, Self

from pydantic import Field, model_validator

from ksef2.domain.models import KSeFBaseModel


class VatRate(StrEnum):
    """FA(3) schema VAT rate markers."""

    VAT_23 = "23"
    VAT_22 = "22"
    VAT_8 = "8"
    VAT_7 = "7"
    VAT_5 = "5"
    VAT_4 = "4"
    VAT_3 = "3"
    VAT_0 = "0"
    EXEMPT = "zw"
    NOT_SUBJECT = "np"
    REVERSE_CHARGE = "oo"


class VatTreatment(StrEnum):
    """Legal VAT treatment categories used by the domain model."""

    TAXABLE = "taxable"
    ZERO_DOMESTIC = "zero_domestic"
    ZERO_WDT = "zero_wdt"
    ZERO_EXPORT = "zero_export"
    EXEMPT = "exempt"
    REVERSE_CHARGE = "reverse_charge"
    OUT_OF_SCOPE_OUTSIDE_TERRITORY = "out_of_scope_outside_territory"
    OUT_OF_SCOPE_ARTICLE_100 = "out_of_scope_article_100"


class SaleCategory(StrEnum):
    """Strict FA(3) sale category mapped to schema VAT codes."""

    RATE_23 = "rate_23"
    RATE_22 = "rate_22"
    RATE_8 = "rate_8"
    RATE_7 = "rate_7"
    RATE_5 = "rate_5"
    RATE_4 = "rate_4"
    RATE_3 = "rate_3"
    ZERO_DOMESTIC = "zero_domestic"
    ZERO_WDT = "zero_wdt"
    ZERO_EXPORT = "zero_export"
    EXEMPT = "exempt"
    REVERSE_CHARGE = "reverse_charge"
    OUT_OF_SCOPE_OUTSIDE_TERRITORY = "out_of_scope_outside_territory"
    OUT_OF_SCOPE_ARTICLE_100 = "out_of_scope_article_100"


class TaxRegime(StrEnum):
    """Additional tax regime context for non-standard line calculations."""

    STANDARD = "standard"
    TAXI_FLAT_RATE = "taxi_flat_rate"
    SPECIAL_XII = "special_xii"
    MARGIN = "margin"


NUMERIC_RATE_BY_CATEGORY = {
    SaleCategory.RATE_23: Decimal("23"),
    SaleCategory.RATE_22: Decimal("22"),
    SaleCategory.RATE_8: Decimal("8"),
    SaleCategory.RATE_7: Decimal("7"),
    SaleCategory.RATE_5: Decimal("5"),
    SaleCategory.RATE_4: Decimal("4"),
    SaleCategory.RATE_3: Decimal("3"),
    SaleCategory.ZERO_DOMESTIC: Decimal("0"),
    SaleCategory.ZERO_WDT: Decimal("0"),
    SaleCategory.ZERO_EXPORT: Decimal("0"),
}

TREATMENT_BY_CATEGORY = {
    SaleCategory.RATE_23: VatTreatment.TAXABLE,
    SaleCategory.RATE_22: VatTreatment.TAXABLE,
    SaleCategory.RATE_8: VatTreatment.TAXABLE,
    SaleCategory.RATE_7: VatTreatment.TAXABLE,
    SaleCategory.RATE_5: VatTreatment.TAXABLE,
    SaleCategory.RATE_4: VatTreatment.TAXABLE,
    SaleCategory.RATE_3: VatTreatment.TAXABLE,
    SaleCategory.ZERO_DOMESTIC: VatTreatment.ZERO_DOMESTIC,
    SaleCategory.ZERO_WDT: VatTreatment.ZERO_WDT,
    SaleCategory.ZERO_EXPORT: VatTreatment.ZERO_EXPORT,
    SaleCategory.EXEMPT: VatTreatment.EXEMPT,
    SaleCategory.REVERSE_CHARGE: VatTreatment.REVERSE_CHARGE,
    SaleCategory.OUT_OF_SCOPE_OUTSIDE_TERRITORY: VatTreatment.OUT_OF_SCOPE_OUTSIDE_TERRITORY,
    SaleCategory.OUT_OF_SCOPE_ARTICLE_100: VatTreatment.OUT_OF_SCOPE_ARTICLE_100,
}

CATEGORY_BY_TREATMENT_AND_RATE: dict[
    tuple[VatTreatment, Decimal | None], SaleCategory
] = {
    (VatTreatment.TAXABLE, Decimal("23")): SaleCategory.RATE_23,
    (VatTreatment.TAXABLE, Decimal("22")): SaleCategory.RATE_22,
    (VatTreatment.TAXABLE, Decimal("8")): SaleCategory.RATE_8,
    (VatTreatment.TAXABLE, Decimal("7")): SaleCategory.RATE_7,
    (VatTreatment.TAXABLE, Decimal("5")): SaleCategory.RATE_5,
    (VatTreatment.TAXABLE, Decimal("4")): SaleCategory.RATE_4,
    (VatTreatment.TAXABLE, Decimal("3")): SaleCategory.RATE_3,
    (VatTreatment.ZERO_DOMESTIC, Decimal("0")): SaleCategory.ZERO_DOMESTIC,
    (VatTreatment.ZERO_WDT, Decimal("0")): SaleCategory.ZERO_WDT,
    (VatTreatment.ZERO_EXPORT, Decimal("0")): SaleCategory.ZERO_EXPORT,
    (VatTreatment.EXEMPT, None): SaleCategory.EXEMPT,
    (VatTreatment.REVERSE_CHARGE, None): SaleCategory.REVERSE_CHARGE,
    (
        VatTreatment.OUT_OF_SCOPE_OUTSIDE_TERRITORY,
        None,
    ): SaleCategory.OUT_OF_SCOPE_OUTSIDE_TERRITORY,
    (
        VatTreatment.OUT_OF_SCOPE_ARTICLE_100,
        None,
    ): SaleCategory.OUT_OF_SCOPE_ARTICLE_100,
}

VAT_RATE_BY_CATEGORY = {
    SaleCategory.RATE_23: VatRate.VAT_23,
    SaleCategory.RATE_22: VatRate.VAT_22,
    SaleCategory.RATE_8: VatRate.VAT_8,
    SaleCategory.RATE_7: VatRate.VAT_7,
    SaleCategory.RATE_5: VatRate.VAT_5,
    SaleCategory.RATE_4: VatRate.VAT_4,
    SaleCategory.RATE_3: VatRate.VAT_3,
    SaleCategory.ZERO_DOMESTIC: VatRate.VAT_0,
    SaleCategory.ZERO_WDT: VatRate.VAT_0,
    SaleCategory.ZERO_EXPORT: VatRate.VAT_0,
    SaleCategory.EXEMPT: VatRate.EXEMPT,
    SaleCategory.REVERSE_CHARGE: VatRate.REVERSE_CHARGE,
    SaleCategory.OUT_OF_SCOPE_OUTSIDE_TERRITORY: VatRate.NOT_SUBJECT,
    SaleCategory.OUT_OF_SCOPE_ARTICLE_100: VatRate.NOT_SUBJECT,
}

DEFAULT_CATEGORY_BY_VAT_RATE = {
    VatRate.VAT_23: SaleCategory.RATE_23,
    VatRate.VAT_22: SaleCategory.RATE_22,
    VatRate.VAT_8: SaleCategory.RATE_8,
    VatRate.VAT_7: SaleCategory.RATE_7,
    VatRate.VAT_5: SaleCategory.RATE_5,
    VatRate.VAT_4: SaleCategory.RATE_4,
    VatRate.VAT_3: SaleCategory.RATE_3,
    VatRate.VAT_0: SaleCategory.ZERO_DOMESTIC,
    VatRate.EXEMPT: SaleCategory.EXEMPT,
    VatRate.REVERSE_CHARGE: SaleCategory.REVERSE_CHARGE,
    VatRate.NOT_SUBJECT: SaleCategory.OUT_OF_SCOPE_OUTSIDE_TERRITORY,
}

LEGACY_SALE_CATEGORY_ALIASES = {
    "standard": None,
    "taxi_flat_rate": TaxRegime.TAXI_FLAT_RATE,
    "special_xii": TaxRegime.SPECIAL_XII,
    "margin": TaxRegime.MARGIN,
    "zero_domestic": SaleCategory.ZERO_DOMESTIC,
    "zero_wdt": SaleCategory.ZERO_WDT,
    "zero_export": SaleCategory.ZERO_EXPORT,
    "exempt": SaleCategory.EXEMPT,
    "reverse_charge": SaleCategory.REVERSE_CHARGE,
    "out_of_territory": SaleCategory.OUT_OF_SCOPE_OUTSIDE_TERRITORY,
    "article_100": SaleCategory.OUT_OF_SCOPE_ARTICLE_100,
}

SCHEMA_CODE_BY_CATEGORY = {
    SaleCategory.RATE_23: "23",
    SaleCategory.RATE_22: "22",
    SaleCategory.RATE_8: "8",
    SaleCategory.RATE_7: "7",
    SaleCategory.RATE_5: "5",
    SaleCategory.RATE_4: "4",
    SaleCategory.RATE_3: "3",
    SaleCategory.ZERO_DOMESTIC: "0 KR",
    SaleCategory.ZERO_WDT: "0 WDT",
    SaleCategory.ZERO_EXPORT: "0 EX",
    SaleCategory.EXEMPT: "zw",
    SaleCategory.REVERSE_CHARGE: "oo",
    SaleCategory.OUT_OF_SCOPE_OUTSIDE_TERRITORY: "np I",
    SaleCategory.OUT_OF_SCOPE_ARTICLE_100: "np II",
}


def coerce_vat_rate(value: VatRate | str | None) -> VatRate | None:
    """Normalize raw VAT rate input to a ``VatRate`` enum member."""
    if value is None or isinstance(value, VatRate):
        return value
    if value == "":
        return None
    if value == "np":
        return VatRate.NOT_SUBJECT
    return VatRate(value)


def vat_rate_for_category(category: SaleCategory) -> VatRate:
    """Return the FA(3) VAT rate marker for a sale category."""
    return VAT_RATE_BY_CATEGORY[category]


def default_category_for_vat_rate(vat_rate: VatRate) -> SaleCategory:
    """Return the default sale category for a VAT rate marker."""
    return DEFAULT_CATEGORY_BY_VAT_RATE[vat_rate]


def schema_code_for_category(category: SaleCategory) -> str:
    """Return the exact FA(3) schema code for a sale category."""
    return SCHEMA_CODE_BY_CATEGORY[category]


def parse_sale_category(
    value: SaleCategory | str | None,
    *,
    vat_rate: VatRate | str | None = None,
) -> tuple[SaleCategory | None, TaxRegime | None]:
    """Parse modern and legacy sale-category inputs.

    Args:
        value: Sale category, legacy alias, or ``None``.
        vat_rate: Optional VAT rate used to resolve legacy aliases.

    Returns:
        A ``(sale_category, tax_regime)`` pair. Either value may be ``None``.

    Raises:
        ValueError: If the alias conflicts with the supplied VAT rate.
    """
    if value is None:
        return None, None
    if isinstance(value, SaleCategory):
        return value, None

    normalized = str(value)
    try:
        return SaleCategory(normalized), None
    except ValueError:
        alias = LEGACY_SALE_CATEGORY_ALIASES.get(normalized)
        if isinstance(alias, SaleCategory):
            return alias, None
        if isinstance(alias, TaxRegime):
            if alias is TaxRegime.TAXI_FLAT_RATE:
                normalized_vat_rate = coerce_vat_rate(vat_rate)
                if normalized_vat_rate not in {None, VatRate.VAT_4}:
                    raise ValueError(
                        "taxi_flat_rate is only valid with vat_rate='4' or an explicit RATE_4 category"
                    )
                return SaleCategory.RATE_4, alias
            return None, alias
        if normalized == "standard":
            normalized_vat_rate = coerce_vat_rate(vat_rate)
            if normalized_vat_rate is None:
                return None, TaxRegime.STANDARD
            return default_category_for_vat_rate(
                normalized_vat_rate
            ), TaxRegime.STANDARD
        raise


class VatClassification(KSeFBaseModel):
    """Structured VAT treatment and numeric rate pair."""

    treatment: VatTreatment = Field(
        description="Legal VAT treatment used by the domain model."
    )
    rate: Decimal | None = Field(
        default=None,
        description="Numeric VAT rate percentage when the treatment is taxable or zero-rated.",
    )

    @model_validator(mode="after")
    def validate_rate(self) -> Self:
        if self.treatment is VatTreatment.TAXABLE:
            if self.rate not in {
                Decimal("23"),
                Decimal("22"),
                Decimal("8"),
                Decimal("7"),
                Decimal("5"),
                Decimal("4"),
                Decimal("3"),
            }:
                raise ValueError(
                    "taxable classification requires rate equal to 23, 22, 8, 7, 5, 4, or 3"
                )
            return self

        if self.treatment in {
            VatTreatment.ZERO_DOMESTIC,
            VatTreatment.ZERO_WDT,
            VatTreatment.ZERO_EXPORT,
        }:
            if self.rate != Decimal("0"):
                raise ValueError("zero-rated classifications require rate equal to 0")
            return self

        if self.rate is not None:
            raise ValueError(
                "non-taxable classifications must not define a numeric rate"
            )
        return self

    @property
    def sale_category(self) -> SaleCategory:
        """Return the strict sale category matching this classification."""
        category = CATEGORY_BY_TREATMENT_AND_RATE.get((self.treatment, self.rate))
        if category is None:
            raise ValueError(
                f"Unsupported VAT classification combination: {self.treatment} / {self.rate}"
            )
        return category

    @property
    def vat_rate(self) -> VatRate:
        """Return the FA(3) VAT rate marker for this classification."""
        return vat_rate_for_category(self.sale_category)

    @property
    def numeric_rate(self) -> Decimal | None:
        """Return the numeric VAT rate when this treatment has one."""
        return self.rate

    @property
    def is_zero_rated(self) -> bool:
        """Return whether this classification is one of the zero-rate categories."""
        return self.treatment in {
            VatTreatment.ZERO_DOMESTIC,
            VatTreatment.ZERO_WDT,
            VatTreatment.ZERO_EXPORT,
        }

    @classmethod
    def from_sale_category(cls, category: SaleCategory) -> Self:
        """Build a classification from a strict sale category."""
        return cls(
            treatment=TREATMENT_BY_CATEGORY[category],
            rate=NUMERIC_RATE_BY_CATEGORY.get(category),
        )

    @classmethod
    def from_vat_rate(
        cls,
        vat_rate: VatRate | str,
        *,
        sale_category: SaleCategory | str | None = None,
    ) -> Self:
        """Build a classification from a VAT rate and optional sale category."""
        normalized_vat_rate = coerce_vat_rate(vat_rate)
        assert normalized_vat_rate is not None, "vat_rate must not be None"
        parsed_category, _ = parse_sale_category(
            sale_category,
            vat_rate=normalized_vat_rate,
        )
        category = parsed_category or default_category_for_vat_rate(normalized_vat_rate)
        if vat_rate_for_category(category) != normalized_vat_rate:
            raise ValueError(
                f"vat_rate '{normalized_vat_rate.value}' is not valid for sale_category '{category.value}'"
            )
        return cls.from_sale_category(category)

    @classmethod
    def from_schema_code(cls, code: str) -> Self:
        """Build a classification from a raw FA(3) schema VAT code."""
        for category, raw_code in SCHEMA_CODE_BY_CATEGORY.items():
            if raw_code == code:
                return cls.from_sale_category(category)
        raise ValueError(f"Unsupported FA(3) VAT classification: {code}")

    def to_schema_code(self) -> str:
        """Return the raw FA(3) schema VAT code for this classification."""
        return schema_code_for_category(self.sale_category)


def coerce_vat_classification(
    value: VatClassification | dict[str, Any] | None,
) -> VatClassification | None:
    """Normalize dictionaries and existing objects to ``VatClassification``."""
    if value is None or isinstance(value, VatClassification):
        return value
    return VatClassification.model_validate(value)
