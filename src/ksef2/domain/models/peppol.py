"""Domain models for Peppol provider queries."""

from datetime import datetime

from ksef2.domain.models.base import KSeFBaseModel


class PeppolProvider(KSeFBaseModel):
    """A Peppol service provider registered in the KSeF system."""

    id: str
    """Provider ID in format P[A-Z]{2}[0-9]{6}, e.g. 'PPL123456'."""

    name: str | None
    """Name of the Peppol service provider."""

    date_created: datetime
    """Date when the provider was registered in the system."""


class ListPeppolProvidersResponse(KSeFBaseModel):
    """Response from querying Peppol service providers."""

    providers: list[PeppolProvider]
    """List of Peppol service providers."""

    has_more: bool
    """Flag indicating if more results are available on the next page."""
