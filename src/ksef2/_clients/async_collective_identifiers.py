"""Async client for collective invoice identifiers."""

from collections.abc import AsyncIterator
from typing import final

from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.collective_identifiers import (
    CollectiveIdentifierInvoice,
    CollectiveIdentifierInvoicesPage,
    CollectiveIdentifierInvoicesQuery,
    CollectiveIdentifierReferencesPage,
    CollectiveIdentifiersPage,
    CollectiveIdentifiersQuery,
    GenerateCollectiveIdentifierResponse,
)
from ksef2._domain.models.pagination import CollectiveIdentifierParams
from ksef2._endpoints.async_collective_identifiers import (
    AsyncCollectiveIdentifiersEndpoints,
)
from ksef2._infra.mappers.collective_identifiers import from_spec, to_spec


@final
class AsyncCollectiveIdentifiersClient:
    """API for generating and querying collective invoice identifiers."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._endpoints = AsyncCollectiveIdentifiersEndpoints(transport)

    async def generate(
        self,
        *,
        invoices: list[CollectiveIdentifierInvoice],
    ) -> GenerateCollectiveIdentifierResponse:
        """Generate a collective identifier for the supplied invoices."""
        return from_spec(await self._endpoints.generate(body=to_spec(invoices)))

    async def query(
        self,
        *,
        filters: CollectiveIdentifiersQuery,
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> CollectiveIdentifiersPage:
        """Fetch one page of collective identifiers visible in the context."""
        parameters = params or CollectiveIdentifierParams()
        return from_spec(
            await self._endpoints.query(
                body=to_spec(filters),
                continuation_token=continuation_token,
                **parameters.to_query_params(),
            )
        )

    async def query_all(
        self,
        *,
        filters: CollectiveIdentifiersQuery,
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncIterator[CollectiveIdentifiersPage]:
        """Iterate through every page matching a collective identifier query."""
        parameters = params or CollectiveIdentifierParams()
        response = await self.query(filters=filters, params=parameters)
        yield response

        while continuation_token := response.continuation_token:
            response = await self.query(
                filters=filters,
                continuation_token=continuation_token,
                params=parameters,
            )
            yield response

    async def query_by_ksef_number(
        self,
        *,
        ksef_number: str,
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> CollectiveIdentifierReferencesPage:
        """Fetch one page of identifiers associated with a KSeF invoice."""
        parameters = params or CollectiveIdentifierParams()
        return from_spec(
            await self._endpoints.query_by_ksef_number(
                ksef_number=ksef_number,
                continuation_token=continuation_token,
                **parameters.to_query_params(),
            )
        )

    async def query_all_by_ksef_number(
        self,
        *,
        ksef_number: str,
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncIterator[CollectiveIdentifierReferencesPage]:
        """Iterate through identifiers associated with one KSeF invoice."""
        parameters = params or CollectiveIdentifierParams()
        response = await self.query_by_ksef_number(
            ksef_number=ksef_number,
            params=parameters,
        )
        yield response

        while continuation_token := response.continuation_token:
            response = await self.query_by_ksef_number(
                ksef_number=ksef_number,
                continuation_token=continuation_token,
                params=parameters,
            )
            yield response

    async def list_invoices(
        self,
        *,
        collective_identifier_numbers: list[str],
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> CollectiveIdentifierInvoicesPage:
        """Fetch one page of invoices inside the supplied collective identifiers."""
        parameters = params or CollectiveIdentifierParams()
        query = CollectiveIdentifierInvoicesQuery(
            collective_identifier_numbers=collective_identifier_numbers
        )
        return from_spec(
            await self._endpoints.list_invoices(
                body=to_spec(query),
                continuation_token=continuation_token,
                **parameters.to_query_params(),
            )
        )

    async def list_all_invoices(
        self,
        *,
        collective_identifier_numbers: list[str],
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncIterator[CollectiveIdentifierInvoicesPage]:
        """Iterate through every invoice page for the supplied collective identifiers."""
        parameters = params or CollectiveIdentifierParams()
        response = await self.list_invoices(
            collective_identifier_numbers=collective_identifier_numbers,
            params=parameters,
        )
        yield response

        while continuation_token := response.continuation_token:
            response = await self.list_invoices(
                collective_identifier_numbers=collective_identifier_numbers,
                continuation_token=continuation_token,
                params=parameters,
            )
            yield response
