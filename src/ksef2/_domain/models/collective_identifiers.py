"""Domain models for collective invoice identifiers."""

from datetime import datetime

from pydantic import Field

from ksef2._domain.models.base import KSeFBaseModel
from ksef2._domain.types import CurrencyCodes


class CollectiveIdentifierInvoicePayment(KSeFBaseModel):
    """Payment details attached to one invoice in a collective identifier."""

    amount: float
    """Payment amount."""
    currency: CurrencyCodes
    """Currency of the payment."""


class CollectiveIdentifierInvoice(KSeFBaseModel):
    """Invoice included when generating a collective identifier."""

    ksef_number: str
    """KSeF number of the invoice."""
    payment: CollectiveIdentifierInvoicePayment | None = None
    """Payment details; ``None`` when not provided."""
    description: str | None = Field(default=None, max_length=512)
    """Free-text description, up to 512 characters."""


class GenerateCollectiveIdentifierResponse(KSeFBaseModel):
    """Identifier returned after grouping invoices."""

    collective_identifier_number: str
    """Number of the generated collective identifier."""


class CollectiveIdentifiersQuery(KSeFBaseModel):
    """Filters for collective identifiers visible in the current context."""

    date_created_from: datetime
    """Start of the creation date range."""
    date_created_to: datetime
    """End of the creation date range."""
    collective_identifier_number: str | None = None
    """Match this collective identifier number."""
    invoice_count_from: int | None = None
    """Minimum number of invoices."""
    invoice_count_to: int | None = None
    """Maximum number of invoices."""
    created_in_current_context: bool | None = None
    """Match only identifiers created in the current context (``True``) or elsewhere (``False``)."""


class CollectiveIdentifierInvoicesQuery(KSeFBaseModel):
    """Collective identifiers to expand into their member invoices.

    KSeF accepts at most 10 identifiers in one request.
    """

    collective_identifier_numbers: list[str] = Field(min_length=1, max_length=10)
    """Collective identifier numbers to expand (1–10)."""


class CollectiveIdentifierSummary(KSeFBaseModel):
    """Collective identifier returned by a context query."""

    collective_identifier_number: str
    """Number of the collective identifier."""
    date_created: datetime
    """When the identifier was created."""
    invoice_count: int
    """Number of invoices it groups."""
    created_in_current_context: bool
    """Whether it was created in the current context."""


class CollectiveIdentifiersPage(KSeFBaseModel):
    """One page of collective identifiers returned by a context query."""

    continuation_token: str | None
    """Opaque token for requesting the next page; ``None`` when there are no more pages."""
    collective_identifiers: list[CollectiveIdentifierSummary]
    """Collective identifiers on this page."""


class CollectiveIdentifierReference(KSeFBaseModel):
    """Collective identifier associated with one KSeF invoice number."""

    collective_identifier_number: str
    """Number of the collective identifier."""
    date_created: datetime
    """When the identifier was created."""
    created_in_current_context: bool
    """Whether it was created in the current context."""


class CollectiveIdentifierReferencesPage(KSeFBaseModel):
    """One page of collective identifiers associated with an invoice."""

    continuation_token: str | None
    """Opaque token for requesting the next page; ``None`` when there are no more pages."""
    collective_identifiers: list[CollectiveIdentifierReference]
    """Collective identifiers on this page."""


class CollectiveIdentifierInvoiceDetails(KSeFBaseModel):
    """Invoice details returned for a collective identifier."""

    ksef_number: str
    """KSeF number of the invoice."""
    payment: CollectiveIdentifierInvoicePayment | None = None
    """Payment details; ``None`` when not provided."""
    description: str | None = None
    """Free-text description, if any."""
    details_hidden: bool
    """Whether the payment and description are hidden because the invoice was added in another context."""


class CollectiveIdentifierInvoicesPage(KSeFBaseModel):
    """One page of invoices belonging to a collective identifier."""

    continuation_token: str | None
    """Opaque token for requesting the next page; ``None`` when there are no more pages."""
    invoices: list[CollectiveIdentifierInvoiceDetails]
    """Invoices on this page."""
