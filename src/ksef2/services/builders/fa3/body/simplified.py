from typing import Callable, Self

from ksef2.domain.models.fa3.body import InvoiceType
from ksef2.domain.models.fa3.body.root import KsefInvoiceBody
from ksef2.services.builders.fa3.body.base import BaseBodyBuilder
from ksef2.services.builders.fa3.sub.annotations import AnnotationsBuilderMixin
from ksef2.services.builders.fa3.sub.payment import PaymentBuilderMixin
from ksef2.services.builders.fa3.sub.rows import RowsBuilderMixin
from ksef2.services.builders.fa3.sub.settlement import SettlementBuilderMixin
from ksef2.services.builders.fa3.sub.transaction import TransactionBuilderMixin


class SimplifiedBodyBuilder[TParent](
    BaseBodyBuilder,
    RowsBuilderMixin,
    PaymentBuilderMixin,
    AnnotationsBuilderMixin,
    TransactionBuilderMixin,
    SettlementBuilderMixin,
):
    def __init__(
        self,
        parent: TParent | None = None,
        on_done: Callable[[KsefInvoiceBody], None] | None = None,
        existing_state: KsefInvoiceBody | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        BaseBodyBuilder.__init__(self, existing_state=existing_state)
        self._rows = (
            [row.model_copy(deep=True) for row in existing_state.rows]
            if existing_state
            else []
        )
        self._payment = (
            existing_state.payment.model_copy(deep=True)
            if existing_state and existing_state.payment is not None
            else None
        )
        self._annotations = (
            existing_state.annotations.model_copy(deep=True)
            if existing_state and existing_state.annotations is not None
            else None
        )
        self._transaction_conditions = (
            existing_state.transaction_conditions.model_copy(deep=True)
            if existing_state and existing_state.transaction_conditions is not None
            else None
        )
        self._settlement = (
            existing_state.settlement.model_copy(deep=True)
            if existing_state and existing_state.settlement is not None
            else None
        )

    def build(self) -> KsefInvoiceBody:
        return KsefInvoiceBody(
            **self._state,
            invoice_type=InvoiceType.UPR,
            rows=list(self._rows),
            payment=self._payment,
            annotations=self._annotations,
            transaction_conditions=self._transaction_conditions,
            settlement=self._settlement,
        )

    def from_model(self, body: KsefInvoiceBody) -> Self:
        BaseBodyBuilder.from_model(self, body)
        self._rows = [row.model_copy(deep=True) for row in body.rows]
        self._payment = body.payment.model_copy(deep=True) if body.payment else None
        self._annotations = (
            body.annotations.model_copy(deep=True) if body.annotations else None
        )
        self._transaction_conditions = (
            body.transaction_conditions.model_copy(deep=True)
            if body.transaction_conditions
            else None
        )
        self._settlement = (
            body.settlement.model_copy(deep=True) if body.settlement else None
        )
        return self

    def done(self) -> TParent:
        if self._parent is None or self._on_done is None:
            raise ValueError("SimplifiedBodyBuilder requires a parent to call done().")
        self._on_done(self.build())
        return self._parent
