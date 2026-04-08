from datetime import date
from typing import Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import CorrectedInvoiceReference
from ksef2.domain.models.fa3.body.correction import (
    CorrectedBuyerEntity,
    CorrectedSellerEntity,
    CorrectionEffectType,
    CorrectionInvoiceContext,
)
from ksef2.domain.models.fa3.party import InvoiceAddress


class InvoiceCorrectionState(TypedDict):
    correction_reason: str | None
    correction_effect_type: CorrectionEffectType | None
    corrected_invoices: list[CorrectedInvoiceReference]
    corrected_invoice_period: str | None
    corrected_invoice_number_override: str | None
    corrected_seller: CorrectedSellerEntity | None
    corrected_buyers: list[CorrectedBuyerEntity]


adapter = TypeAdapter(InvoiceCorrectionState)


def _default_state() -> InvoiceCorrectionState:
    return {
        "correction_reason": None,
        "correction_effect_type": None,
        "corrected_invoices": [],
        "corrected_invoice_period": None,
        "corrected_invoice_number_override": None,
        "corrected_seller": None,
        "corrected_buyers": [],
    }


def _build_address(
    country_code: str,
    address_line_1: str,
    address_line_2: str | None = None,
    gln: str | None = None,
) -> InvoiceAddress:
    return InvoiceAddress(
        country_code=country_code,
        address_line_1=address_line_1,
        address_line_2=address_line_2,
        gln=gln,
    )


class CorrectionBuilder[TParent]:
    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[CorrectionInvoiceContext], None],
        existing_state: CorrectionInvoiceContext | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._state: InvoiceCorrectionState = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, correction: CorrectionInvoiceContext) -> Self:
        self._state = adapter.validate_python(correction.model_dump())
        return self

    def reason(self, value: str | None) -> Self:
        self._state["correction_reason"] = value
        return self

    def effect_type(self, value: CorrectionEffectType | None) -> Self:
        self._state["correction_effect_type"] = value
        return self

    def add_corrected_invoice(
        self,
        *,
        issue_date: date,
        invoice_number: str,
        ksef_id: str | None = None,
        outside_ksef: bool = False,
    ) -> Self:
        self._state["corrected_invoices"].append(
            CorrectedInvoiceReference(
                issue_date=issue_date,
                invoice_number=invoice_number,
                ksef_id=ksef_id,
                outside_ksef=outside_ksef,
            )
        )
        return self

    def add_corrected_invoice_model(
        self, corrected_invoice: CorrectedInvoiceReference
    ) -> Self:
        self._state["corrected_invoices"].append(corrected_invoice)
        return self

    def clear_corrected_invoices(self) -> Self:
        self._state["corrected_invoices"].clear()
        return self

    def corrected_invoice_period(self, value: str | None) -> Self:
        self._state["corrected_invoice_period"] = value
        return self

    def corrected_invoice_number_override(self, value: str | None) -> Self:
        self._state["corrected_invoice_number_override"] = value
        return self

    def corrected_seller(
        self,
        *,
        name: str,
        tax_id: str,
        country_code: str,
        address_line_1: str,
        address_line_2: str | None = None,
        gln: str | None = None,
        vat_prefix: str | None = None,
    ) -> Self:
        self._state["corrected_seller"] = CorrectedSellerEntity(
            vat_prefix=vat_prefix,
            tax_id=tax_id,
            name=name,
            address=_build_address(
                country_code=country_code,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                gln=gln,
            ),
        )
        return self

    def corrected_seller_model(
        self, corrected_seller: CorrectedSellerEntity | None
    ) -> Self:
        self._state["corrected_seller"] = corrected_seller
        return self

    def add_corrected_buyer(
        self,
        *,
        name: str,
        tax_id: str | None = None,
        eu_vat_id: str | None = None,
        country_code: str | None = None,
        address_country_code: str | None = None,
        other_id: str | None = None,
        no_id: bool = False,
        address_line_1: str | None = None,
        address_line_2: str | None = None,
        gln: str | None = None,
        buyer_id: str | None = None,
    ) -> Self:
        address = None
        address_code = address_country_code or country_code
        if address_code is not None and address_line_1 is not None:
            address = _build_address(
                country_code=address_code,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                gln=gln,
            )
        self._state["corrected_buyers"].append(
            CorrectedBuyerEntity(
                tax_id=tax_id,
                eu_vat_id=eu_vat_id,
                country_code=country_code,
                other_id=other_id,
                no_id=no_id,
                name=name,
                address=address,
                buyer_id=buyer_id,
            )
        )
        return self

    def add_corrected_buyer_model(self, corrected_buyer: CorrectedBuyerEntity) -> Self:
        self._state["corrected_buyers"].append(corrected_buyer)
        return self

    def clear_corrected_buyers(self) -> Self:
        self._state["corrected_buyers"].clear()
        return self

    def build(self) -> CorrectionInvoiceContext:
        return CorrectionInvoiceContext(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Correction details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class CorrectionBuilderMixin:
    _correction: CorrectionInvoiceContext | None = None

    def correction(self) -> CorrectionBuilder[Self]:
        return CorrectionBuilder(self, self._set_correction, self._correction)

    def _set_correction(self, value: CorrectionInvoiceContext) -> None:
        self._correction = value
