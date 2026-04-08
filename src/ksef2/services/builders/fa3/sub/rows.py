from datetime import date
from decimal import Decimal
from typing import Callable, Self, TypedDict

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


class RowsState(TypedDict):
    rows: list[InvoiceRow]


adapter = TypeAdapter(RowsState)


_ZERO_DISCOUNT = Decimal("0.00")


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
        name: str,
        quantity: Decimal,
        unit_price_net: Decimal,
        vat_rate: VatRate | str | None = None,
        vat_classification: VatClassification | dict[str, object] | None = None,
        unit_of_measure: str = "szt",
        supply_date: date | None = None,
        discount_amount: Decimal | None = _ZERO_DISCOUNT,
        sale_category: SaleCategory | str | None = None,
        tax_regime: TaxRegime | str = TaxRegime.STANDARD,
        net_amount: Decimal | None = None,
        vat_amount: Decimal | None = None,
        gross_amount: Decimal | None = None,
        unit_price_gross: Decimal | None = None,
        vat_rate_xii: Decimal | None = None,
        annex_15_marker: bool | None = None,
        excise_amount: Decimal | None = None,
        unique_id: str | None = None,
        sku: str | None = None,
        gtin: str | None = None,
        pkwiu: str | None = None,
        cn: str | None = None,
        pkob: str | None = None,
        gtu_code: GtuCode | None = None,
        procedure: InvoiceProcedure | None = None,
        currency_exchange_rate: Decimal | None = None,
        before_correction: bool = False,
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
        name: str,
        quantity: Decimal,
        unit_price_net: Decimal,
        vat_rate: VatRate | str | None = None,
        vat_classification: VatClassification | dict[str, object] | None = None,
        unit_of_measure: str = "szt",
        supply_date: date | None = None,
        discount_amount: Decimal | None = _ZERO_DISCOUNT,
        sale_category: SaleCategory | str | None = None,
        tax_regime: TaxRegime | str = TaxRegime.STANDARD,
        net_amount: Decimal | None = None,
        vat_amount: Decimal | None = None,
        gross_amount: Decimal | None = None,
        unit_price_gross: Decimal | None = None,
        vat_rate_xii: Decimal | None = None,
        annex_15_marker: bool | None = None,
        excise_amount: Decimal | None = None,
        unique_id: str | None = None,
        sku: str | None = None,
        gtin: str | None = None,
        pkwiu: str | None = None,
        cn: str | None = None,
        pkob: str | None = None,
        gtu_code: GtuCode | None = None,
        procedure: InvoiceProcedure | None = None,
        currency_exchange_rate: Decimal | None = None,
        before_correction: bool = False,
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
