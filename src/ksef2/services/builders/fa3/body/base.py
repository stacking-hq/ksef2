from datetime import date
from decimal import Decimal
from typing import Annotated, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import KsefInvoiceBody, AdditionalDescriptionEntry
from ksef2.domain.models.fa3.body import InvoiceSummaryOverrides
from ksef2.services.builders.fa3.metadata import builder_param


class BodyCoreState(TypedDict):
    currency: str
    issue_date: date
    issue_place: str | None
    invoice_number: str
    warehouse_documents: list[str]
    date_of_supply: date | None
    period_start: date | None
    period_end: date | None
    vat_currency_exchange_rate: Decimal | None
    fp_invoice: bool
    related_party_transaction: bool
    additional_description: list[AdditionalDescriptionEntry]
    return_of_excise: bool | None
    summary_overrides: InvoiceSummaryOverrides | None


adapter = TypeAdapter(BodyCoreState)


def _default_state() -> BodyCoreState:
    return {
        "currency": "PLN",
        "issue_date": date.today(),
        "issue_place": None,
        "invoice_number": "not-specified",
        "warehouse_documents": [],
        "date_of_supply": None,
        "period_start": None,
        "period_end": None,
        "vat_currency_exchange_rate": None,
        "fp_invoice": False,
        "related_party_transaction": False,
        "additional_description": [],
        "return_of_excise": None,
        "summary_overrides": None,
    }


class BaseBodyBuilder:
    def __init__(self, existing_state: KsefInvoiceBody | None = None) -> None:
        self._state = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, body: KsefInvoiceBody) -> Self:
        self._state = adapter.validate_python(body.model_dump())
        return self

    def currency(
        self,
        value: Annotated[
            str,
            builder_param(
                "Invoice currency code. The builder stores it in uppercase.",
                examples=["PLN", "EUR"],
            ),
        ],
    ) -> Self:
        self._state["currency"] = value.upper()
        return self

    def issue_date(
        self,
        value: Annotated[
            date,
            builder_param(
                "Date when the invoice is issued.",
                examples=["2026-04-09"],
                format="date",
            ),
        ],
    ) -> Self:
        self._state["issue_date"] = value
        return self

    def issue_place(
        self,
        value: Annotated[
            str | None,
            builder_param(
                "Place where the invoice was issued.",
                examples=["Warszawa"],
            ),
        ],
    ) -> Self:
        self._state["issue_place"] = value
        return self

    def invoice_number(
        self,
        value: Annotated[
            str,
            builder_param(
                "Invoice number visible on the document.",
                examples=["FV/2026/04/0001"],
            ),
        ],
    ) -> Self:
        self._state["invoice_number"] = value
        return self

    def add_warehouse_document(
        self,
        value: Annotated[
            str,
            builder_param(
                "Reference to a warehouse or stock document linked to the invoice.",
                examples=["WZ/2026/04/15"],
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["warehouse_documents"].append(value)
        return self

    def replace_warehouse_documents(self, values: list[str]) -> Self:
        self._state["warehouse_documents"] = list(values)
        return self

    def clear_warehouse_documents(self) -> Self:
        self._state["warehouse_documents"].clear()
        return self

    def date_of_supply(
        self,
        value: Annotated[
            date | None,
            builder_param(
                "Supply or service completion date for the invoice.",
                examples=["2026-04-08"],
                format="date",
            ),
        ],
    ) -> Self:
        self._state["date_of_supply"] = value
        return self

    def billing_period(
        self,
        *,
        period_start: Annotated[
            date | None,
            builder_param(
                "Start of the billing period for period-based invoices.",
                examples=["2026-04-01"],
                format="date",
                priority="advanced",
            ),
        ] = None,
        period_end: Annotated[
            date | None,
            builder_param(
                "End of the billing period for period-based invoices.",
                examples=["2026-04-30"],
                format="date",
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        self._state["period_start"] = period_start
        self._state["period_end"] = period_end
        return self

    def vat_currency_exchange_rate(
        self,
        value: Annotated[
            Decimal | None,
            builder_param(
                "Exchange rate used for VAT calculations when the invoice currency differs from PLN.",
                examples=["4.2512"],
                format="decimal-string",
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["vat_currency_exchange_rate"] = value
        return self

    def mark_fp(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the invoice as an FP invoice.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        self._state["fp_invoice"] = enabled
        return self

    def related_party_transaction(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the invoice as a related-party transaction.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        self._state["related_party_transaction"] = enabled
        return self

    def add_description(
        self,
        *,
        key: Annotated[
            str,
            builder_param(
                "Label for an additional invoice description entry.",
                examples=["campaign"],
                priority="advanced",
            ),
        ],
        value: Annotated[
            str,
            builder_param(
                "Value stored under the additional description label.",
                examples=["spring-2026"],
                priority="advanced",
            ),
        ],
        row_number: Annotated[
            int | None,
            builder_param(
                "Invoice row number that this additional description refers to.",
                examples=[1],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        self._state["additional_description"].append(
            AdditionalDescriptionEntry(
                row_number=row_number,
                key=key,
                value=value,
            )
        )
        return self

    def add_description_model(self, entry: AdditionalDescriptionEntry) -> Self:
        self._state["additional_description"].append(entry)
        return self

    def clear_descriptions(self) -> Self:
        self._state["additional_description"].clear()
        return self

    def return_of_excise(
        self,
        value: Annotated[
            bool | None,
            builder_param(
                "Marks the invoice as related to an excise refund scenario when required.",
                examples=[True],
                priority="advanced",
            ),
        ],
    ) -> Self:
        self._state["return_of_excise"] = value
        return self

    def summary_overrides(
        self,
        value: Annotated[
            InvoiceSummaryOverrides | None,
            builder_param(
                "Explicit invoice summary totals to preserve when they should not be recomputed from lines.",
                examples=[],
                priority="override",
                format="object",
                schema_ref="ksef2.domain.models.fa3.body.InvoiceSummaryOverrides",
            ),
        ],
    ) -> Self:
        self._state["summary_overrides"] = value
        return self
