"""Async Peppol endpoints for querying Peppol service providers."""

from typing import Unpack, final

from ksef2._core import routes
from ksef2._domain.types import OffsetPaginationQueryParams
from ksef2._endpoints.async_base import AsyncBaseEndpoints
from ksef2._infra.schema.api import spec


@final
class AsyncPeppolEndpoints(AsyncBaseEndpoints):
    async def query_providers(
        self,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryPeppolProvidersResponse:
        return self._parse(
            await self._transport.get(
                path=routes.PeppolRoutes.QUERY_PROVIDERS,
                params=self.build_params(params),
            ),
            spec.QueryPeppolProvidersResponse,
        )
