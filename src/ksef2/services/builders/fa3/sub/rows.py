from datetime import date
from decimal import Decimal
from typing import Annotated, Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import InvoiceRow
from ksef2.domain.models.fa3.body import (
    GtuCode,
    InvoiceProcedure,
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
)
from ksef2.domain.models.fa3.body.tax import coerce_vat_classification
from ksef2.services.builders.fa3.metadata import builder_param


class RowsState(TypedDict):
    rows: list[InvoiceRow]


adapter = TypeAdapter(RowsState)


_ZERO_DISCOUNT = Decimal("0.00")

RowNameParam = Annotated[
    str,
    builder_param(
        "Description of the goods or service shown on the invoice line.",
        examples=["Monthly accounting service", "Laptop 14 inch"],
    ),
]
RowQuantityParam = Annotated[
    Decimal,
    builder_param(
        "Quantity billed on this line.",
        examples=["1", "2.5"],
        format="decimal-string",
    ),
]
RowUnitPriceNetParam = Annotated[
    Decimal,
    builder_param(
        "Net unit price for one item or one service unit.",
        examples=["100.00", "2499.99"],
        format="decimal-string",
    ),
]
RowVatRateParam = Annotated[
    VatRate | str | None,
    builder_param(
        "VAT rate used for the line when a standard VAT indicator is enough.",
        examples=["23", "8", "0", "zw"],
        format="enum-string",
    ),
]
RowVatClassificationParam = Annotated[
    VatClassification | dict[str, object] | None,
    builder_param(
        "Detailed VAT classification for non-standard cases such as WDT, export, exempt, or reverse charge.",
        examples=[{"treatment": "zero_wdt", "rate": "0"}],
        format="object",
        priority="advanced",
        schema_ref="ksef2.domain.models.fa3.body.tax.VatClassification",
    ),
]
RowUnitOfMeasureParam = Annotated[
    str,
    builder_param(
        "Unit of measure shown on the invoice line.",
        examples=["szt", "h", "kg"],
    ),
]
RowSupplyDateParam = Annotated[
    date | None,
    builder_param(
        "Supply or service date specific to this invoice line.",
        examples=["2026-04-08"],
        format="date",
        priority="advanced",
    ),
]
RowDiscountAmountParam = Annotated[
    Decimal | None,
    builder_param(
        "Discount amount applied to the line.",
        examples=["0.00", "15.50"],
        format="decimal-string",
        priority="advanced",
    ),
]
RowSaleCategoryParam = Annotated[
    SaleCategory | str | None,
    builder_param(
        "Sale category used when the invoice line must distinguish between zero-rated, exempt, reverse-charge, or other sale contexts.",
        examples=["rate_23", "zero_wdt", "exempt"],
        format="enum-string",
        priority="advanced",
    ),
]
RowTaxRegimeParam = Annotated[
    TaxRegime | str,
    builder_param(
        "Tax regime applied to the line, for example the standard regime, margin procedure, or special Title XII procedure.",
        examples=["standard", "margin", "special_xii"],
        format="enum-string",
        priority="advanced",
    ),
]
RowOverrideAmountParam = Annotated[
    Decimal | None,
    builder_param(
        "Explicit line amount. Usually computed automatically; set it only when you intentionally need to override the builder's calculation.",
        examples=["100.00", "123.00"],
        format="decimal-string",
        priority="override",
    ),
]
RowVatRateXiiParam = Annotated[
    Decimal | None,
    builder_param(
        "VAT rate used for special Title XII scenarios.",
        examples=["8.50"],
        format="decimal-string",
        priority="advanced",
    ),
]
RowAnnex15Param = Annotated[
    bool | None,
    builder_param(
        "Set when the line is covered by Annex 15 reporting.",
        examples=[True],
        priority="advanced",
    ),
]
RowExciseAmountParam = Annotated[
    Decimal | None,
    builder_param(
        "Excise amount linked to the line when required by the invoice scenario.",
        examples=["12.30"],
        format="decimal-string",
        priority="advanced",
    ),
]
RowOptionalTextParam = Annotated[
    str | None,
    builder_param(
        "Optional reference stored for the line.",
        examples=["SKU-001"],
        priority="advanced",
    ),
]
RowGtuCodeParam = Annotated[
    GtuCode | None,
    builder_param(
        "GTU code assigned to the line when the goods or service falls under GTU reporting.",
        examples=["GTU_06"],
        format="enum-string",
        priority="advanced",
    ),
]
RowProcedureParam = Annotated[
    InvoiceProcedure | None,
    builder_param(
        "Special invoice procedure marker assigned to the line.",
        examples=["I_42", "B_SPV"],
        format="enum-string",
        priority="advanced",
    ),
]
RowCurrencyExchangeRateParam = Annotated[
    Decimal | None,
    builder_param(
        "Currency exchange rate used for this line when the line requires its own rate.",
        examples=["4.2512"],
        format="decimal-string",
        priority="advanced",
    ),
]
RowBeforeCorrectionParam = Annotated[
    bool,
    builder_param(
        "Marks the line as a before-correction value on correction invoices.",
        examples=[False],
        priority="advanced",
    ),
]


def _default_state() -> RowsState:
    return {"rows": []}


def _coerce_vat_rate(vat_rate: VatRate | str | None) -> VatRate | None:
    if vat_rate is None or isinstance(vat_rate, VatRate):
        return vat_rate
    return VatRate(vat_rate)


def _coerce_sale_category(
    sale_category: SaleCategory | str | None,
) -> SaleCategory | None:
    if sale_category is None:
        return None
    if isinstance(sale_category, SaleCategory):
        return sale_category
    return SaleCategory(sale_category)


def _coerce_tax_regime(tax_regime: TaxRegime | str) -> TaxRegime:
    if isinstance(tax_regime, TaxRegime):
        return tax_regime
    return TaxRegime(tax_regime)


def _coerce_vat_classification(
    vat_classification: VatClassification | dict[str, object] | None,
) -> VatClassification | None:
    return coerce_vat_classification(vat_classification)


class RowsBuilder[TParent]:
    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[list[InvoiceRow]], None],
        existing_rows: list[InvoiceRow] | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._state: RowsState = adapter.validate_python(
            {"rows": list(existing_rows)} if existing_rows else _default_state()
        )

    def from_model(self, rows: list[InvoiceRow]) -> Self:
        self._state = adapter.validate_python({"rows": list(rows)})
        return self

    def add_row(
        self,
        *,
        name: RowNameParam,
        quantity: RowQuantityParam,
        unit_price_net: RowUnitPriceNetParam,
        vat_rate: RowVatRateParam = None,
        vat_classification: RowVatClassificationParam = None,
        unit_of_measure: RowUnitOfMeasureParam = "szt",
        supply_date: RowSupplyDateParam = None,
        discount_amount: RowDiscountAmountParam = _ZERO_DISCOUNT,
        sale_category: RowSaleCategoryParam = None,
        tax_regime: RowTaxRegimeParam = TaxRegime.STANDARD,
        net_amount: RowOverrideAmountParam = None,
        vat_amount: RowOverrideAmountParam = None,
        gross_amount: RowOverrideAmountParam = None,
        unit_price_gross: RowOverrideAmountParam = None,
        vat_rate_xii: RowVatRateXiiParam = None,
        annex_15_marker: RowAnnex15Param = None,
        excise_amount: RowExciseAmountParam = None,
        unique_id: RowOptionalTextParam = None,
        sku: RowOptionalTextParam = None,
        gtin: RowOptionalTextParam = None,
        pkwiu: RowOptionalTextParam = None,
        cn: RowOptionalTextParam = None,
        pkob: RowOptionalTextParam = None,
        gtu_code: RowGtuCodeParam = None,
        procedure: RowProcedureParam = None,
        currency_exchange_rate: RowCurrencyExchangeRateParam = None,
        before_correction: RowBeforeCorrectionParam = False,
    ) -> Self:
        self._state["rows"].append(
            InvoiceRow(
                name=name,
                quantity=quantity,
                unit_price_net=unit_price_net,
                vat_rate=_coerce_vat_rate(vat_rate),
                vat_classification=_coerce_vat_classification(vat_classification),
                unit_of_measure=unit_of_measure,
                supply_date=supply_date,
                discount_amount=discount_amount,
                sale_category=_coerce_sale_category(sale_category),
                tax_regime=_coerce_tax_regime(tax_regime),
                net_amount=net_amount,
                vat_amount=vat_amount,
                gross_amount=gross_amount,
                unit_price_gross=unit_price_gross,
                vat_rate_xii=vat_rate_xii,
                annex_15_marker=annex_15_marker,
                excise_amount=excise_amount,
                unique_id=unique_id,
                sku=sku,
                gtin=gtin,
                pkwiu=pkwiu,
                cn=cn,
                pkob=pkob,
                gtu_code=gtu_code,
                procedure=procedure,
                currency_exchange_rate=currency_exchange_rate,
                before_correction=before_correction,
            )
        )
        return self

    def add_line(
        self,
        *,
        name: RowNameParam,
        quantity: RowQuantityParam,
        unit_price_net: RowUnitPriceNetParam,
        vat_rate: RowVatRateParam = None,
        vat_classification: RowVatClassificationParam = None,
        unit_of_measure: RowUnitOfMeasureParam = "szt",
        supply_date: RowSupplyDateParam = None,
        discount_amount: RowDiscountAmountParam = _ZERO_DISCOUNT,
        sale_category: RowSaleCategoryParam = None,
        tax_regime: RowTaxRegimeParam = TaxRegime.STANDARD,
        net_amount: RowOverrideAmountParam = None,
        vat_amount: RowOverrideAmountParam = None,
        gross_amount: RowOverrideAmountParam = None,
        unit_price_gross: RowOverrideAmountParam = None,
        vat_rate_xii: RowVatRateXiiParam = None,
        annex_15_marker: RowAnnex15Param = None,
        excise_amount: RowExciseAmountParam = None,
        unique_id: RowOptionalTextParam = None,
        sku: RowOptionalTextParam = None,
        gtin: RowOptionalTextParam = None,
        pkwiu: RowOptionalTextParam = None,
        cn: RowOptionalTextParam = None,
        pkob: RowOptionalTextParam = None,
        gtu_code: RowGtuCodeParam = None,
        procedure: RowProcedureParam = None,
        currency_exchange_rate: RowCurrencyExchangeRateParam = None,
        before_correction: RowBeforeCorrectionParam = False,
    ) -> Self:
        return self.add_row(
            name=name,
            quantity=quantity,
            unit_price_net=unit_price_net,
            vat_rate=vat_rate,
            vat_classification=vat_classification,
            unit_of_measure=unit_of_measure,
            supply_date=supply_date,
            discount_amount=discount_amount,
            sale_category=sale_category,
            tax_regime=tax_regime,
            net_amount=net_amount,
            vat_amount=vat_amount,
            gross_amount=gross_amount,
            unit_price_gross=unit_price_gross,
            vat_rate_xii=vat_rate_xii,
            annex_15_marker=annex_15_marker,
            excise_amount=excise_amount,
            unique_id=unique_id,
            sku=sku,
            gtin=gtin,
            pkwiu=pkwiu,
            cn=cn,
            pkob=pkob,
            gtu_code=gtu_code,
            procedure=procedure,
            currency_exchange_rate=currency_exchange_rate,
            before_correction=before_correction,
        )

    def add_row_model(self, row: InvoiceRow) -> Self:
        self._state["rows"].append(row)
        return self

    def add_line_model(self, line: InvoiceRow) -> Self:
        self._state["rows"].append(line)
        return self

    def replace_lines(self, rows: list[InvoiceRow]) -> Self:
        self._state["rows"] = list(rows)
        return self

    def clear_lines(self) -> Self:
        self._state["rows"].clear()
        return self

    def build(self) -> list[InvoiceRow]:
        return list(self._state["rows"])

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError("Invoice rows are empty. Add at least one line.")
        self._on_done(self.build())
        return self._parent


class RowsBuilderMixin:
    _rows: list[InvoiceRow] = []

    def rows(self) -> RowsBuilder[Self]:
        return RowsBuilder(self, self._set_rows, self._rows)

    def _set_rows(self, value: list[InvoiceRow]) -> None:
        self._rows = list(value)
