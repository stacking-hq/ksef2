from decimal import Decimal
from collections.abc import Sequence
from typing import Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3.body import (
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
)
from ksef2.domain.models.fa3.body.order import InvoiceOrder, InvoiceOrderLine
from ksef2.domain.models.fa3.body.tax import coerce_vat_classification


class OrderState(TypedDict):
    total_value: Decimal | None
    order_lines: list[InvoiceOrderLine]


adapter = TypeAdapter(OrderState)


def _default_state() -> OrderState:
    return {"total_value": None, "order_lines": []}


def _coerce_vat_rate(value: VatRate | str | None) -> VatRate | None:
    if value is None:
        return None
    if isinstance(value, VatRate):
        return value
    return VatRate(value)


def _coerce_sale_category(value: SaleCategory | str | None) -> SaleCategory | None:
    if value is None:
        return None
    if isinstance(value, SaleCategory):
        return value
    return SaleCategory(value)


def _coerce_tax_regime(value: TaxRegime | str) -> TaxRegime:
    if isinstance(value, TaxRegime):
        return value
    return TaxRegime(value)


def _coerce_vat_classification(
    value: VatClassification | dict[str, object] | None,
) -> VatClassification | None:
    return coerce_vat_classification(value)


class OrderBuilder[TParent]:
    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[InvoiceOrder], None],
        existing_state: InvoiceOrder | None = None,
        declared_total: Decimal | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        if existing_state is None:
            self._state = adapter.validate_python(_default_state())
        else:
            self._state = adapter.validate_python(existing_state.model_dump())
        if declared_total is not None:
            self._state["total_value"] = declared_total

    def from_model(self, order: InvoiceOrder) -> Self:
        self._state = adapter.validate_python(order.model_dump())
        return self

    def total_value(self, amount: Decimal | None) -> Self:
        self._state["total_value"] = amount
        return self

    def add_line(
        self,
        *,
        gross_amount: Decimal,
        vat_rate: VatRate | str | None,
        vat_classification: VatClassification | dict[str, object] | None = None,
        name: str | None = None,
        quantity: Decimal | None = None,
        unit_of_measure: str | None = None,
        unit_price_net: Decimal | None = None,
        sale_category: SaleCategory | str | None = None,
        tax_regime: TaxRegime | str = TaxRegime.STANDARD,
        vat_rate_xii: Decimal | None = None,
        annex_15_marker: bool | None = None,
        unique_id: str | None = None,
        sku: str | None = None,
        gtin: str | None = None,
        pkwiu: str | None = None,
        cn: str | None = None,
        pkob: str | None = None,
        gtu_code: str | None = None,
        procedure: str | None = None,
        excise_amount: Decimal | None = None,
        before_correction: bool = False,
    ) -> Self:
        self._state["order_lines"].append(
            InvoiceOrderLine(
                gross_amount=gross_amount,
                vat_rate=_coerce_vat_rate(vat_rate),
                vat_classification=_coerce_vat_classification(vat_classification),
                name=name,
                quantity=quantity,
                unit_of_measure=unit_of_measure,
                unit_price_net=unit_price_net,
                sale_category=_coerce_sale_category(sale_category),
                tax_regime=_coerce_tax_regime(tax_regime),
                vat_rate_xii=vat_rate_xii,
                annex_15_marker=annex_15_marker,
                unique_id=unique_id,
                sku=sku,
                gtin=gtin,
                pkwiu=pkwiu,
                cn=cn,
                pkob=pkob,
                gtu_code=gtu_code,
                procedure=procedure,
                excise_amount=excise_amount,
                before_correction=before_correction,
            )
        )
        return self

    def add_line_model(self, line: InvoiceOrderLine) -> Self:
        self._state["order_lines"].append(line)
        return self

    def replace_lines(self, lines: Sequence[InvoiceOrderLine]) -> Self:
        self._state["order_lines"] = list(lines)
        return self

    def clear_lines(self) -> Self:
        self._state["order_lines"].clear()
        return self

    def build(self) -> InvoiceOrder:
        return InvoiceOrder(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Order details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class OrderBuilderMixin:
    _order: InvoiceOrder | None = None

    def order(self, *, declared_total: Decimal | None = None) -> OrderBuilder[Self]:
        return OrderBuilder(
            self, self._set_order, self._order, declared_total=declared_total
        )

    def _set_order(self, value: InvoiceOrder) -> None:
        self._order = value
