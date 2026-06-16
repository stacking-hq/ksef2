"""FA(3) order and advance-order body models."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Self

from pydantic import Field, field_validator, model_validator

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


class InvoiceOrderLine(KSeFBaseModel):
    """FA(3) order line used inside the invoice order block."""

    name: str | None = Field(default=None, description="p_7_z")
    quantity: Decimal | None = Field(default=None, description="p_8_bz")
    unit_of_measure: str | None = Field(default=None, description="p_8_az")
    gross_amount: Decimal | None = Field(
        default=None, description="Gross value of the order row"
    )
    vat_rate: VatRate | None = Field(default=None, description="p_12_z")
    vat_classification: VatClassification | None = Field(
        default=None,
        description="Structured VAT classification for the order row.",
    )
    sale_category: SaleCategory | None = Field(default=None)
    tax_regime: TaxRegime = Field(default=TaxRegime.STANDARD)
    unit_price_net: Decimal | None = Field(default=None, description="p_9_az")
    net_amount: Decimal | None = Field(default=None, description="p_11_netto_z")
    vat_amount: Decimal | None = Field(default=None, description="p_11_vat_z")
    vat_rate_xii: Decimal | None = Field(default=None, description="p_12_z_xii")
    annex_15_marker: bool | None = Field(default=None, description="p_12_z_zal_15")
    unique_id: str | None = Field(default=None, description="uu_idz")
    sku: str | None = Field(default=None, description="indeks_z")
    gtin: str | None = Field(default=None, description="gtinz")
    pkwiu: str | None = Field(default=None, description="pkwi_uz")
    cn: str | None = Field(default=None, description="cnz")
    pkob: str | None = Field(default=None, description="pkobz")
    gtu_code: str | None = Field(default=None, description="gtuz")
    procedure: str | None = Field(default=None, description="procedura_z")
    currency_exchange_rate: Decimal | None = Field(
        default=None, description="kurs_waluty_z: Currency exchange rate"
    )
    excise_amount: Decimal | None = Field(default=None, description="kwota_akcyzy_z")
    before_correction: bool = Field(default=False, description="stan_przed_z")

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

    @field_validator("gross_amount")
    @classmethod
    def validate_gross_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if value <= Decimal("0.00"):
            raise ValueError("gross_amount must be greater than zero")
        return round_pln(value)

    @model_validator(mode="after")
    def compute_financial_fields(self) -> Self:
        vat_percent = self._vat_percent()
        if self.gross_amount is not None:
            if self.net_amount is None:
                if vat_percent is None:
                    self.net_amount = self.gross_amount
                else:
                    divisor = Decimal("1.00") + vat_percent
                    self.net_amount = round_pln(self.gross_amount / divisor)

            if self.vat_amount is None:
                assert self.net_amount is not None
                self.vat_amount = round_pln(self.gross_amount - self.net_amount)

        if (
            self.gross_amount is None
            and self.net_amount is not None
            and self.vat_amount is not None
        ):
            self.gross_amount = round_pln(self.net_amount + self.vat_amount)

        if (
            self.unit_price_net is None
            and self.quantity not in {None, Decimal("0.00")}
            and self.net_amount is not None
        ):
            assert self.quantity is not None, "quantity must be provided"
            self.unit_price_net = self.net_amount / self.quantity

        self._validate_tax_logic()
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

    def _validate_tax_logic(self) -> None:
        if self.tax_regime is TaxRegime.MARGIN:
            if (
                self.vat_classification is not None
                or self.vat_rate is not None
                or self.sale_category is not None
            ):
                raise ValueError(
                    "margin order lines must not define vat_classification, vat_rate, or sale_category"
                )
            return

        if self.tax_regime is TaxRegime.SPECIAL_XII:
            if self.vat_rate_xii is None:
                raise ValueError("special_xii tax_regime requires vat_rate_xii")
            return

        if (
            self.vat_classification is None
            or self.sale_category is None
            or self.vat_rate is None
        ):
            raise ValueError(
                "vat classification is required unless the order line uses a margin or Title XII regime"
            )

        if (
            self.tax_regime is TaxRegime.TAXI_FLAT_RATE
            and self.sale_category != SaleCategory.RATE_4
        ):
            raise ValueError(
                "taxi flat-rate order lines must use sale_category='rate_4'"
            )


class InvoiceOrder(KSeFBaseModel):
    """FA(3) order block with one or more order lines."""

    total_value: Decimal | None = None
    order_lines: list[InvoiceOrderLine] = Field(min_length=1)

    @field_validator("total_value")
    @classmethod
    def round_total_value(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if value <= Decimal("0.00"):
            raise ValueError("total_value must be greater than zero")
        return round_pln(value)

    @model_validator(mode="after")
    def validate_and_populate_total(self) -> Self:
        after_lines = [line for line in self.order_lines if not line.before_correction]
        lines_for_total = after_lines if after_lines else self.order_lines

        computed_gross_total = sum(
            (
                line.gross_amount
                for line in lines_for_total
                if line.gross_amount is not None
            ),
            start=Decimal("0.00"),
        )
        computed_net_total = sum(
            (
                line.net_amount
                for line in lines_for_total
                if line.net_amount is not None
            ),
            start=Decimal("0.00"),
        )

        if self.total_value is not None and self.total_value not in {
            computed_gross_total,
            computed_net_total,
        }:
            raise ValueError(
                "gross amount must equal the sum of order line gross amounts"
            )

        if self.total_value is None:
            if computed_gross_total > Decimal("0.00"):
                self.total_value = computed_gross_total
            else:
                self.total_value = computed_net_total

        return self


AdvanceOrderLine = InvoiceOrderLine
