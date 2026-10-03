from typing import Annotated

from pydantic import Field, AwareDatetime

from ksef2._infra.schema.api.supp.base import BaseSupp


class PeppolProvider(BaseSupp):
    """Supplementary request for PeppolProvider.

    Overrides:
        name: str -> str | None
        API returns None as name for system providers
    """

    # override
    name: str | None = None
    """
    Nazwa dostawcy usług Peppol.
    """

    # others
    id: Annotated[str, Field(max_length=9, min_length=9, pattern="^P[A-Z]{2}[0-9]{6}$")]
    """
    Identyfikator dostawcy usług Peppol.
    """
    dateCreated: AwareDatetime
    """
    Data rejestracji dostawcy usług Peppol w systemie.
    """


class QueryPeppolProvidersResponse(BaseSupp):
    """Root request for Peppol providers query response.

    Overrides:
        peppolProviders: list[spec.PeppolProvider] -> list[supp.PeppolProvider]
        replaced PeppolProvider request with supplementary one
    """

    # override
    peppolProviders: list[PeppolProvider]
    """
    Lista dostawców usług Peppol.
    """

    # others
    hasMore: bool
    """
    Flaga informująca o dostępności kolejnej strony wyników.
    """
