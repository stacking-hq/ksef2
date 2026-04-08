from typing import Callable

from ksef2.domain.models.fa3.body import InvoiceType
from ksef2.domain.models.fa3.body.root import KsefInvoiceBody
from ksef2.services.builders.fa3.body.base import BaseBodyBuilder
from ksef2.services.builders.fa3.sub.advance import AdvanceBuilderMixin
from ksef2.services.builders.fa3.sub.annotations import AnnotationsBuilderMixin
from ksef2.services.builders.fa3.sub.correction import CorrectionBuilderMixin
from ksef2.services.builders.fa3.sub.order import OrderBuilderMixin
from ksef2.services.builders.fa3.sub.payment import PaymentBuilderMixin
from ksef2.services.builders.fa3.sub.transaction import TransactionBuilderMixin


class CorrectionAdvanceBodyBuilder[TParent](
    BaseBodyBuilder,
    OrderBuilderMixin,
    PaymentBuilderMixin,
    AnnotationsBuilderMixin,
    TransactionBuilderMixin,
    CorrectionBuilderMixin,
    AdvanceBuilderMixin,
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
        self._order = (
            existing_state.order.model_copy(deep=True)
            if existing_state and existing_state.order is not None
            else None
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
        self._correction = (
            existing_state.correction.model_copy(deep=True)
            if existing_state and existing_state.correction is not None
            else None
        )
        self._advance = (
            existing_state.advance.model_copy(deep=True)
            if existing_state and existing_state.advance is not None
            else None
        )

    def build(self) -> KsefInvoiceBody:
        return KsefInvoiceBody(
            **self._state,
            invoice_type=InvoiceType.CORRECTING_ZAL,
            order=self._order,
            payment=self._payment,
            annotations=self._annotations,
            transaction_conditions=self._transaction_conditions,
            correction=self._correction,
            advance=self._advance,
        )

    def done(self) -> TParent:
        if self._parent is None or self._on_done is None:
            raise ValueError(
                "CorrectionAdvanceBodyBuilder requires a parent to call done()."
            )
        self._on_done(self.build())
        return self._parent
