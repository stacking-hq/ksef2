"""Fluent builder for FA(3) order blocks."""

from decimal import Decimal
from collections.abc import Sequence
from typing import Annotated, Self, TypedDict
from collections.abc import Callable

from pydantic import TypeAdapter

from ksef2.domain.models.fa3.body import (
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
)
from ksef2.domain.models.fa3.body.order import InvoiceOrder, InvoiceOrderLine
from ksef2.domain.models.fa3.body.tax import coerce_vat_classification
from ksef2.services.builders.fa3.metadata import builder_param


class OrderState(TypedDict):
    """Typed state for Order fields."""

    total_value: Decimal | None
    order_lines: list[InvoiceOrderLine]


adapter = TypeAdapter(OrderState)

OrderAmountParam = Annotated[
    Decimal | None,
    builder_param(
        "Monetary value used in the order section.",
        examples=["1000.00"],
        format="decimal-string",
    ),
]


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
    """Fluent builder for FA(3) order details."""

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
        """Replace the builder state from an existing domain model."""
        self._state = adapter.validate_python(order.model_dump())
        return self

    def total_value(self, amount: OrderAmountParam) -> Self:
        """Set the declared total value for the order."""
        self._state["total_value"] = amount
        return self

    def add_line(
        self,
        *,
        gross_amount: Annotated[
            Decimal,
            builder_param(
                "Gross amount for the order line.",
                examples=["123.00"],
                format="decimal-string",
            ),
        ],
        vat_rate: Annotated[
            VatRate | str | None,
            builder_param(
                "VAT rate used for the order line.",
                examples=["23", "8", "0", "zw"],
                format="enum-string",
            ),
        ],
        vat_classification: Annotated[
            VatClassification | dict[str, object] | None,
            builder_param(
                "Detailed VAT classification for non-standard order line cases.",
                examples=[{"treatment": "zero_export", "rate": "0"}],
                format="object",
                priority="advanced",
                schema_ref="ksef2.domain.models.fa3.body.tax.VatClassification",
            ),
        ] = None,
        name: Annotated[
            str | None,
            builder_param(
                "Order line description.",
                examples=["Prepayment for consulting service"],
            ),
        ] = None,
        quantity: Annotated[
            Decimal | None,
            builder_param(
                "Quantity recorded on the order line.",
                examples=["1", "2.5"],
                format="decimal-string",
            ),
        ] = None,
        unit_of_measure: Annotated[
            str | None,
            builder_param(
                "Unit of measure recorded on the order line.",
                examples=["szt", "h"],
            ),
        ] = None,
        unit_price_net: Annotated[
            Decimal | None,
            builder_param(
                "Net unit price recorded on the order line.",
                examples=["100.00"],
                format="decimal-string",
            ),
        ] = None,
        sale_category: Annotated[
            SaleCategory | str | None,
            builder_param(
                "Sale category used for the order line when a more detailed sales context is needed.",
                examples=["rate_23", "zero_wdt"],
                format="enum-string",
                priority="advanced",
            ),
        ] = None,
        tax_regime: Annotated[
            TaxRegime | str,
            builder_param(
                "Tax regime used for the order line.",
                examples=["standard", "margin"],
                format="enum-string",
                priority="advanced",
            ),
        ] = TaxRegime.STANDARD,
        vat_rate_xii: Annotated[
            Decimal | None,
            builder_param(
                "VAT rate for Title XII order lines.",
                examples=["8.50"],
                format="decimal-string",
                priority="advanced",
            ),
        ] = None,
        annex_15_marker: Annotated[
            bool | None,
            builder_param(
                "Set when the order line is covered by Annex 15 reporting.",
                examples=[True],
                priority="advanced",
            ),
        ] = None,
        unique_id: Annotated[
            str | None,
            builder_param(
                "Unique identifier of the order line.",
                examples=["ORDER-LINE-1"],
                priority="advanced",
            ),
        ] = None,
        sku: Annotated[
            str | None,
            builder_param(
                "Stock keeping unit stored on the order line.",
                examples=["SKU-001"],
                priority="advanced",
            ),
        ] = None,
        gtin: Annotated[
            str | None,
            builder_param(
                "GTIN stored on the order line.",
                examples=["05901234123457"],
                priority="advanced",
            ),
        ] = None,
        pkwiu: Annotated[
            str | None,
            builder_param(
                "PKWiU classification stored on the order line.",
                examples=["62.02.30.0"],
                priority="advanced",
            ),
        ] = None,
        cn: Annotated[
            str | None,
            builder_param(
                "CN code stored on the order line.",
                examples=["84713000"],
                priority="advanced",
            ),
        ] = None,
        pkob: Annotated[
            str | None,
            builder_param(
                "PKOB code stored on the order line.",
                examples=["1122"],
                priority="advanced",
            ),
        ] = None,
        gtu_code: Annotated[
            str | None,
            builder_param(
                "GTU code stored on the order line.",
                examples=["GTU_06"],
                priority="advanced",
            ),
        ] = None,
        procedure: Annotated[
            str | None,
            builder_param(
                "Special procedure marker stored on the order line.",
                examples=["I_42"],
                priority="advanced",
            ),
        ] = None,
        excise_amount: Annotated[
            Decimal | None,
            builder_param(
                "Excise amount stored on the order line when required.",
                examples=["12.30"],
                format="decimal-string",
                priority="advanced",
            ),
        ] = None,
        before_correction: Annotated[
            bool,
            builder_param(
                "Marks the order line as a before-correction value.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
    ) -> Self:
        """Add a line entry."""
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
        """Add an existing invoice line domain model."""
        self._state["order_lines"].append(line)
        return self

    def replace_lines(self, lines: Sequence[InvoiceOrderLine]) -> Self:
        """Replace all invoice lines."""
        self._state["order_lines"] = list(lines)
        return self

    def clear_lines(self) -> Self:
        """Remove all invoice lines."""
        self._state["order_lines"].clear()
        return self

    def build(self) -> InvoiceOrder:
        """Build the corresponding FA(3) domain model."""
        return InvoiceOrder(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        """Attach the built order details to the parent builder and return it.

        Raises:
            ValueError: If order details are empty.
        """
        if self._is_empty():
            raise ValueError(
                "Order details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class OrderBuilderMixin:
    """Mixin exposing the Order sub-builder."""

    _order: InvoiceOrder | None = None

    def order(self, *, declared_total: Decimal | None = None) -> OrderBuilder[Self]:
        """Start an order sub-builder."""
        return OrderBuilder(
            self, self._set_order, self._order, declared_total=declared_total
        )

    def _set_order(self, value: InvoiceOrder) -> None:
        self._order = value
