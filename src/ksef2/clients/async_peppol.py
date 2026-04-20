from collections.abc import AsyncIterator
from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.pagination import OffsetPaginationParams
from ksef2.domain.models.peppol import ListPeppolProvidersResponse, PeppolProvider
from ksef2.endpoints.async_peppol import AsyncPeppolEndpoints
from ksef2.infra.mappers.peppol import from_spec


@final
class AsyncPeppolClient:
    """Async service for querying Peppol service providers."""

    def __init__(self, transport: AsyncMiddleware):
        self._transport = transport
        self._endpoints = AsyncPeppolEndpoints(transport)

    async def query(
        self,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> ListPeppolProvidersResponse:
        current_params = params or OffsetPaginationParams()
        response = await self._endpoints.query_providers(
            **current_params.to_query_params()
        )
        return from_spec(response)

    async def all(
        self, *, params: OffsetPaginationParams | None = None
    ) -> AsyncIterator[PeppolProvider]:
        current_params = params or OffsetPaginationParams()

        while True:
            response = await self.query(params=current_params)
            for provider in response.providers:
                yield provider

            if not response.has_more:
                break

            current_params = current_params.next_page()
