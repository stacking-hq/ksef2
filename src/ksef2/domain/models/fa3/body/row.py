"""FA(3) invoice row domain models and financial calculations."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Self

from pydantic import Field, model_validator

from ksef2.domain.models import KSeFBaseModel
from ksef2.domain.models.fa3.body.tax import (
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
    coerce_vat_classification,
    coerce_vat_rate,
    parse_sale_category,
)


def round_pln(value: Decimal) -> Decimal:
    """Round a monetary amount using standard PLN precision."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


GtuCode = Literal[
    "GTU_01",
    "GTU_02",
    "GTU_03",
    "GTU_04",
    "GTU_05",
    "GTU_06",
    "GTU_07",
    "GTU_08",
    "GTU_09",
    "GTU_10",
    "GTU_11",
    "GTU_12",
    "GTU_13",
]
InvoiceProcedure = Literal[
    "WSTO_EE",
    "IED",
    "TT_D",
    "I_42",
    "I_63",
    "B_SPV",
    "B_SPV_DOSTAWA",
    "B_MPV_PROWIZJA",
]


class InvoiceRow(KSeFBaseModel):
    """Line item stored in the FA(3) ``Fa/FaWiersz`` block."""

    name: str | None = Field(default=None, description="p_7: Name of good/service")
    supply_date: date | None = Field(default=None, description="p_6_a: Date of supply")
    unit_price_net: Decimal | None = Field(
        default=None, description="p_9_a: Net unit price"
    )
    vat_rate: VatRate | None = Field(
        default=None,
        description="Legacy raw VAT rate marker used by the FA(3) schema serializer.",
    )
    vat_classification: VatClassification | None = Field(
        default=None,
        description=(
            "Structured VAT classification separating legal treatment from numeric rate. "
            "Prefer this over manually mixing rate and sale category values."
        ),
    )
    unit_of_measure: str = Field(default="szt", description="p_8_a: Unit of measure")
    quantity: Decimal | None = Field(default=None, description="p_8_b: Quantity")
    discount_amount: Decimal | None = Field(
        default=Decimal("0.00"), description="p_10: Discount amount"
    )

    # --- computed fields ---
    unit_price_gross: Decimal | None = Field(
        default=None, description="p_9_b: Price with VAT"
    )
    gross_amount: Decimal | None = Field(
        default=None, description="p_11_a: Gross value of the line"
    )
    net_amount: Decimal | None = Field(
        default=None, description="p_11: Net value of the line"
    )
    vat_amount: Decimal | None = Field(
        default=None, description="p_11_vat: VAT amount of the line"
    )

    vat_rate_xii: Decimal | None = Field(
        default=None, description="p_12_XII: VAT rate XII"
    )
    annex_15_marker: bool | None = Field(
        default=None, description="p_12_ZAL_15: Annex 15 marker"
    )

    sale_category: SaleCategory | None = Field(
        default=None,
        description=(
            "Strict classification mapped 1:1 to TstawkaPodatku values when the line uses "
            "normal FA(3) VAT markers."
        ),
    )
    tax_regime: TaxRegime = Field(
        default=TaxRegime.STANDARD,
        description=(
            "Separate tax-regime context for cases that are not pure TstawkaPodatku categories, "
            "such as taxi flat-rate, Title XII, or margin invoices."
        ),
    )

    excise_amount: Decimal | None = Field(
        default=None, description="kwota_akcyzy: Excise amount"
    )
    unique_id: str | None = Field(default=None, description="uu_id: Unique ID")
    sku: str | None = Field(
        default=None, description="indeks: Internal SKU or additional description"
    )
    gtin: str | None = Field(default=None, description="gtin: Global Trade Item Number")
    pkwiu: str | None = Field(
        default=None, description="pkwi_u: Polish Goods Classification"
    )
    cn: str | None = Field(default=None, description="cn: Nomenclature Code")
    pkob: str | None = Field(
        default=None, description="pkob: Polish Construction Object Classification"
    )

    gtu_code: GtuCode | None = Field(default=None, description="gtu: GTU code")
    procedure: InvoiceProcedure | None = Field(
        default=None, description="procedura: Procedure code"
    )
    currency_exchange_rate: Decimal | None = Field(
        default=None, description="kurs_waluty: Currency exchange rate"
    )
    before_correction: bool = Field(
        default=False,
        description="stan_przed: Marks the row as representing state before correction",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_tax_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        raw_vat_classification = data.get("vat_classification")
        raw_vat_rate = data.get("vat_rate")
        raw_sale_category = data.get("sale_category")
        raw_tax_regime = data.get("tax_regime")

        vat_classification = coerce_vat_classification(raw_vat_classification)
        vat_rate = coerce_vat_rate(raw_vat_rate)
        sale_category, inferred_tax_regime = parse_sale_category(
            raw_sale_category,
            vat_rate=vat_rate,
        )

        if isinstance(raw_tax_regime, TaxRegime):
            tax_regime = raw_tax_regime
        elif raw_tax_regime is None:
            tax_regime = inferred_tax_regime or TaxRegime.STANDARD
        else:
            tax_regime = TaxRegime(str(raw_tax_regime))

        if vat_classification is None:
            if sale_category is not None:
                vat_classification = VatClassification.from_sale_category(sale_category)
            elif vat_rate is not None and tax_regime is not TaxRegime.MARGIN:
                vat_classification = VatClassification.from_vat_rate(vat_rate)
        else:
            if sale_category is None:
                sale_category = vat_classification.sale_category
            elif sale_category != vat_classification.sale_category:
                raise ValueError(
                    "sale_category does not match the supplied vat_classification"
                )

            if vat_rate is None:
                vat_rate = vat_classification.vat_rate
            elif vat_rate != vat_classification.vat_rate:
                raise ValueError(
                    "vat_rate does not match the supplied vat_classification"
                )

        if sale_category is None and vat_classification is not None:
            sale_category = vat_classification.sale_category
        if vat_rate is None and vat_classification is not None:
            vat_rate = vat_classification.vat_rate

        data["vat_classification"] = vat_classification
        data["vat_rate"] = vat_rate
        data["sale_category"] = sale_category
        data["tax_regime"] = tax_regime
        return data

    @model_validator(mode="after")
    def compute_financial_field(self) -> Self:
        rate = self._vat_percent()

        if (
            self.gross_amount is None
            and self.net_amount is None
            and self.unit_price_net is None
            and self.unit_price_gross is not None
            and self.quantity is not None
        ):
            base_gross = self.unit_price_gross * self.quantity
            self.gross_amount = round_pln(base_gross) - (
                self.discount_amount or Decimal("0.00")
            )

        if self.gross_amount is not None:
            if self.net_amount is None:
                if rate is None:
                    self.net_amount = self.gross_amount
                else:
                    divisor = Decimal("1.00") + rate
                    self.net_amount = round_pln(self.gross_amount / divisor)

            if self.vat_amount is None:
                assert self.net_amount is not None
                self.vat_amount = round_pln(self.gross_amount - self.net_amount)

        if (
            self.net_amount is None
            and self.unit_price_net is not None
            and self.quantity is not None
        ):
            base_net = self.unit_price_net * self.quantity
            self.net_amount = round_pln(base_net) - (
                self.discount_amount or Decimal("0.00")
            )

        if self.vat_amount is None and self.net_amount is not None:
            if rate is None:
                self.vat_amount = Decimal("0.00")
            else:
                self.vat_amount = round_pln(self.net_amount * rate)

        if (
            self.gross_amount is None
            and self.net_amount is not None
            and self.vat_amount is not None
        ):
            self.gross_amount = round_pln(self.net_amount + self.vat_amount)

        _ = self.validate_tax_logic()
        return self

    def validate_tax_logic(self) -> Self:
        """Validate VAT classification and amount consistency for this row."""
        self._validate_quantity()
        self._validate_tax_classification_rules()
        self._validate_gross_amount_consistency()
        return self

    def _vat_percent(self) -> Decimal | None:
        if self.tax_regime is TaxRegime.SPECIAL_XII:
            if self.vat_rate_xii is None:
                return None
            return self.vat_rate_xii / Decimal("100")

        if (
            self.vat_classification is None
            or self.vat_classification.numeric_rate is None
        ):
            return None

        return self.vat_classification.numeric_rate / Decimal("100")

    def _validate_quantity(self) -> None:
        if self.quantity == 0:
            raise ValueError("quantity cannot be zero")

    def _validate_tax_classification_rules(self) -> None:
        if self.tax_regime is TaxRegime.MARGIN:
            self._validate_margin()
            return

        if self.tax_regime is TaxRegime.SPECIAL_XII:
            self._validate_special_xii()
            return

        if self._is_descriptive_only():
            return

        if (
            self.vat_classification is None
            or self.sale_category is None
            or self.vat_rate is None
        ):
            raise ValueError(
                "vat classification is required unless the line uses a margin or Title XII regime"
            )

        if self.tax_regime is TaxRegime.TAXI_FLAT_RATE:
            if self.sale_category != SaleCategory.RATE_4:
                raise ValueError("taxi flat-rate lines must use sale_category='rate_4'")
            if self.vat_rate != VatRate.VAT_4:
                raise ValueError("taxi flat-rate lines must use vat_rate='4'")
            return

        if self.sale_category != self.vat_classification.sale_category:
            raise ValueError("sale_category must match vat_classification")
        if self.vat_rate != self.vat_classification.vat_rate:
            raise ValueError("vat_rate must match vat_classification")

    def _is_descriptive_only(self) -> bool:
        return (
            self.tax_regime is TaxRegime.STANDARD
            and self.vat_classification is None
            and self.sale_category is None
            and self.vat_rate is None
            and self.vat_rate_xii is None
            and self.unit_price_net is None
            and self.unit_price_gross is None
            and self.net_amount is None
            and self.gross_amount is None
            and self.vat_amount is None
            and self.discount_amount in {None, Decimal("0.00")}
        )

    def _validate_margin(self) -> None:
        if (
            self.vat_classification is not None
            or self.vat_rate is not None
            or self.sale_category is not None
        ):
            raise ValueError(
                "margin lines must not define vat_classification, vat_rate, or sale_category"
            )

    def _validate_special_xii(self) -> None:
        if self.vat_rate_xii is None:
            raise ValueError("special_xii tax_regime requires vat_rate_xii")

    def _validate_gross_amount_consistency(self) -> None:
        if self.gross_amount is not None:
            assert self.net_amount is not None and self.vat_amount is not None, (
                "net_amount and vat_amount must be set when gross_amount is provided"
            )
            expected_gross = self.net_amount + self.vat_amount
            if self.gross_amount != expected_gross:
                raise ValueError(
                    f"gross_amount must equal net_amount + vat_amount ({expected_gross})"
                )
