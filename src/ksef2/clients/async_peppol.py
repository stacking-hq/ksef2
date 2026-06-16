"""Async PEPPOL branch client."""

from collections.abc import AsyncIterator
from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.pagination import OffsetPaginationParams
from ksef2.domain.models.peppol import ListPeppolProvidersResponse, PeppolProvider
from ksef2.endpoints.async_peppol import AsyncPeppolEndpoints
from ksef2.infra.mappers.peppol import from_spec


@final
class AsyncPeppolClient:
    """Async service for querying Peppol service providers.

    Catch ``KSeFException`` for SDK-classified failures raised by this branch,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(self, transport: AsyncMiddleware):
        self._transport = transport
        self._endpoints = AsyncPeppolEndpoints(transport)

    async def query(
        self,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> ListPeppolProvidersResponse:
        """Query Peppol service providers.

        Args:
            params: Pagination parameters.

        Returns:
            QueryPeppolProvidersResponse containing the list of providers
            and pagination info.
        """
        current_params = params or OffsetPaginationParams()
        response = await self._endpoints.query_providers(
            **current_params.to_query_params()
        )
        return from_spec(response)

    async def all(
        self, *, params: OffsetPaginationParams | None = None
    ) -> AsyncIterator[PeppolProvider]:
        """Iterate over all Peppol service providers.

        This method handles pagination internally.

        Args:
            params: Pagination parameters.

        Returns:
            Iterator over PeppolProvider objects.
        """
        current_params = params or OffsetPaginationParams()

        while True:
            response = await self.query(params=current_params)
            for provider in response.providers:
                yield provider

            if not response.has_more:
                break

            current_params = current_params.next_page()
