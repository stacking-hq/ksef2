"""Domain models for collective invoice identifiers."""

from datetime import datetime

from pydantic import Field

from ksef2._domain.models.base import KSeFBaseModel
from ksef2._domain.types import CurrencyCodes


class CollectiveIdentifierInvoicePayment(KSeFBaseModel):
    """Payment details attached to one invoice in a collective identifier."""

    amount: float
    currency: CurrencyCodes


class CollectiveIdentifierInvoice(KSeFBaseModel):
    """Invoice included when generating a collective identifier."""

    ksef_number: str
    payment: CollectiveIdentifierInvoicePayment | None = None
    description: str | None = Field(default=None, max_length=512)


class GenerateCollectiveIdentifierResponse(KSeFBaseModel):
    """Identifier returned after grouping invoices."""

    collective_identifier_number: str


class CollectiveIdentifiersQuery(KSeFBaseModel):
    """Filters for collective identifiers visible in the current context."""

    date_created_from: datetime
    date_created_to: datetime
    collective_identifier_number: str | None = None
    invoice_count_from: int | None = None
    invoice_count_to: int | None = None
    created_in_current_context: bool | None = None


class CollectiveIdentifierInvoicesQuery(KSeFBaseModel):
    """Collective identifiers to expand into their member invoices.

    KSeF accepts at most 10 identifiers in one request.
    """

    collective_identifier_numbers: list[str] = Field(min_length=1, max_length=10)


class CollectiveIdentifierSummary(KSeFBaseModel):
    """Collective identifier returned by a context query."""

    collective_identifier_number: str
    date_created: datetime
    invoice_count: int
    created_in_current_context: bool


class CollectiveIdentifiersPage(KSeFBaseModel):
    """One page of collective identifiers returned by a context query."""

    continuation_token: str | None
    collective_identifiers: list[CollectiveIdentifierSummary]


class CollectiveIdentifierReference(KSeFBaseModel):
    """Collective identifier associated with one KSeF invoice number."""

    collective_identifier_number: str
    date_created: datetime
    created_in_current_context: bool


class CollectiveIdentifierReferencesPage(KSeFBaseModel):
    """One page of collective identifiers associated with an invoice."""

    continuation_token: str | None
    collective_identifiers: list[CollectiveIdentifierReference]


class CollectiveIdentifierInvoiceDetails(KSeFBaseModel):
    """Invoice details returned for a collective identifier."""

    ksef_number: str
    payment: CollectiveIdentifierInvoicePayment | None = None
    description: str | None = None
    details_hidden: bool


class CollectiveIdentifierInvoicesPage(KSeFBaseModel):
    """One page of invoices belonging to a collective identifier."""

    continuation_token: str | None
    invoices: list[CollectiveIdentifierInvoiceDetails]
