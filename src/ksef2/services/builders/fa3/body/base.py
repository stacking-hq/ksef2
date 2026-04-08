from datetime import date
from decimal import Decimal
from typing import Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import KsefInvoiceBody, AdditionalDescriptionEntry


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
    }


class BaseBodyBuilder:
    def __init__(self, existing_state: KsefInvoiceBody | None = None) -> None:
        self._state = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, body: KsefInvoiceBody) -> Self:
        self.__init__(existing_state=body)
        return self

    def currency(self, value: str) -> Self:
        self._state["currency"] = value.upper()
        return self

    def issue_date(self, value: date) -> Self:
        self._state["issue_date"] = value
        return self

    def issue_place(self, value: str | None) -> Self:
        self._state["issue_place"] = value
        return self

    def invoice_number(self, value: str) -> Self:
        self._state["invoice_number"] = value
        return self

    def add_warehouse_document(self, value: str) -> Self:
        self._state["warehouse_documents"].append(value)
        return self

    def replace_warehouse_documents(self, values: list[str]) -> Self:
        self._state["warehouse_documents"] = list(values)
        return self

    def clear_warehouse_documents(self) -> Self:
        self._state["warehouse_documents"].clear()
        return self

    def date_of_supply(self, value: date | None) -> Self:
        self._state["date_of_supply"] = value
        return self

    def billing_period(
        self, *, period_start: date | None = None, period_end: date | None = None
    ) -> Self:
        self._state["period_start"] = period_start
        self._state["period_end"] = period_end
        return self

    def vat_currency_exchange_rate(self, value: Decimal | None) -> Self:
        self._state["vat_currency_exchange_rate"] = value
        return self

    def mark_fp(self, enabled: bool = True) -> Self:
        self._state["fp_invoice"] = enabled
        return self

    def related_party_transaction(self, enabled: bool = True) -> Self:
        self._state["related_party_transaction"] = enabled
        return self

    def add_description(
        self, *, key: str, value: str, row_number: int | None = None
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

    def return_of_excise(self, value: bool | None) -> Self:
        self._state["return_of_excise"] = value
        return self
