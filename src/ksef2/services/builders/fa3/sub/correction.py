from datetime import date
from typing import Annotated, Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import CorrectedInvoiceReference
from ksef2.domain.models.fa3.body.correction import (
    CorrectedBuyerEntity,
    CorrectedSellerEntity,
    CorrectionEffectType,
    CorrectionInvoiceContext,
)
from ksef2.domain.models.fa3.party import InvoiceAddress
from ksef2.services.builders.fa3.metadata import builder_param


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

    def reason(
        self,
        value: Annotated[
            str | None,
            builder_param(
                "Reason for issuing the correction invoice.",
                examples=["Price reduction after complaint"],
            ),
        ],
    ) -> Self:
        self._state["correction_reason"] = value
        return self

    def effect_type(
        self,
        value: Annotated[
            CorrectionEffectType | None,
            builder_param(
                "Correction effect type required by the FA(3) correction section.",
                examples=["increase", "decrease"],
                format="enum-string",
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["correction_effect_type"] = value
        return self

    def add_corrected_invoice(
        self,
        *,
        issue_date: Annotated[
            date,
            builder_param(
                "Issue date of the corrected invoice.",
                examples=["2026-03-15"],
                format="date",
            ),
        ],
        invoice_number: Annotated[
            str,
            builder_param(
                "Number of the corrected invoice.",
                examples=["FV/2026/03/0015"],
            ),
        ],
        ksef_id: Annotated[
            str | None,
            builder_param(
                "KSeF identifier of the corrected invoice.",
                examples=["20260315-1234567890-ABCDEF1234567890"],
                priority="advanced",
            ),
        ] = None,
        outside_ksef: Annotated[
            bool,
            builder_param(
                "Set to true when the corrected invoice was issued outside KSeF.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
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

    def corrected_invoice_period(
        self,
        value: Annotated[
            str | None,
            builder_param(
                "Accounting period covered by the corrected invoice, when the correction refers to a period instead of a single document.",
                examples=["2026-03"],
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["corrected_invoice_period"] = value
        return self

    def corrected_invoice_number_override(
        self,
        value: Annotated[
            str | None,
            builder_param(
                "Manual corrected invoice number used when it must differ from the referenced invoice number.",
                examples=["KOR/2026/04/0001"],
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["corrected_invoice_number_override"] = value
        return self

    def corrected_seller(
        self,
        *,
        name: Annotated[
            str,
            builder_param(
                "Seller name from the corrected invoice.",
                examples=["ACME sp. z o.o."],
            ),
        ],
        tax_id: Annotated[
            str,
            builder_param(
                "Seller tax identifier from the corrected invoice.",
                examples=["1234567890"],
            ),
        ],
        country_code: Annotated[
            str,
            builder_param(
                "Country code from the corrected seller address.",
                examples=["PL"],
                format="country-code",
            ),
        ],
        address_line_1: Annotated[
            str,
            builder_param(
                "First address line from the corrected seller details.",
                examples=["ul. Przykladowa 10"],
            ),
        ],
        address_line_2: Annotated[
            str | None,
            builder_param(
                "Second address line from the corrected seller details.",
                examples=["00-001 Warszawa"],
            ),
        ] = None,
        gln: Annotated[
            str | None,
            builder_param(
                "GLN from the corrected seller address.",
                examples=["5901234123457"],
                priority="advanced",
            ),
        ] = None,
        vat_prefix: Annotated[
            str | None,
            builder_param(
                "VAT prefix from the corrected seller identity.",
                examples=["PL"],
                priority="advanced",
            ),
        ] = None,
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
        name: Annotated[
            str,
            builder_param(
                "Buyer name from the corrected invoice.",
                examples=["XYZ GmbH"],
            ),
        ],
        tax_id: Annotated[
            str | None,
            builder_param(
                "Buyer tax identifier from the corrected invoice.",
                examples=["9876543210"],
            ),
        ] = None,
        eu_vat_id: Annotated[
            str | None,
            builder_param(
                "Buyer EU VAT identifier from the corrected invoice.",
                examples=["DE123456789"],
                priority="advanced",
            ),
        ] = None,
        country_code: Annotated[
            str | None,
            builder_param(
                "Buyer identity country code from the corrected invoice.",
                examples=["DE"],
                format="country-code",
                priority="advanced",
            ),
        ] = None,
        address_country_code: Annotated[
            str | None,
            builder_param(
                "Country code for the corrected buyer address.",
                examples=["DE"],
                format="country-code",
                priority="advanced",
            ),
        ] = None,
        other_id: Annotated[
            str | None,
            builder_param(
                "Alternative buyer identifier from the corrected invoice.",
                examples=["CUST-4455"],
                priority="advanced",
            ),
        ] = None,
        no_id: Annotated[
            bool,
            builder_param(
                "Set to true when the corrected buyer should be recorded without an identifier.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        address_line_1: Annotated[
            str | None,
            builder_param(
                "First address line from the corrected buyer details.",
                examples=["Unter den Linden 1"],
                priority="advanced",
            ),
        ] = None,
        address_line_2: Annotated[
            str | None,
            builder_param(
                "Second address line from the corrected buyer details.",
                examples=["10117 Berlin"],
                priority="advanced",
            ),
        ] = None,
        gln: Annotated[
            str | None,
            builder_param(
                "GLN from the corrected buyer address.",
                examples=["4012345678901"],
                priority="advanced",
            ),
        ] = None,
        buyer_id: Annotated[
            str | None,
            builder_param(
                "Buyer identifier stored on the corrected invoice.",
                examples=["buyer-42"],
                priority="advanced",
            ),
        ] = None,
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
