"""Async raw endpoints for collective invoice identifiers."""

from typing import Unpack, final

from pydantic import TypeAdapter

from ksef2.core import routes
from ksef2.domain.types import CollectiveIdentifierQueryParams
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.infra.schema.api import spec

_QUERY_PARAMS = TypeAdapter(CollectiveIdentifierQueryParams)


@final
class AsyncCollectiveIdentifiersEndpoints(AsyncBaseEndpoints):
    """Raw collective identifier endpoints backed by generated schema models."""

    async def generate(
        self,
        body: spec.GenerateCollectiveIdentifierRequest,
    ) -> spec.GenerateCollectiveIdentifierResponse:
        """Generate a collective identifier for a list of invoices."""
        return self._parse(
            await self._transport.post(
                path=routes.CollectiveIdentifierRoutes.GENERATE,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.GenerateCollectiveIdentifierResponse,
        )

    async def query(
        self,
        body: spec.CollectiveIdentifiersQueryRequest,
        continuation_token: str | None = None,
        **params: Unpack[CollectiveIdentifierQueryParams],
    ) -> spec.CollectiveIdentifiersQueryResponse:
        """Fetch one page of collective identifiers visible in the context."""
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )
        return self._parse(
            await self._transport.post(
                path=routes.CollectiveIdentifierRoutes.QUERY,
                params=self.build_params(params, _QUERY_PARAMS),
                headers=headers,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.CollectiveIdentifiersQueryResponse,
        )

    async def query_by_ksef_number(
        self,
        ksef_number: str,
        continuation_token: str | None = None,
        **params: Unpack[CollectiveIdentifierQueryParams],
    ) -> spec.CollectiveIdentifiersByKsefNumberQueryResponse:
        """Fetch identifiers associated with one KSeF invoice number."""
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )
        return self._parse(
            await self._transport.get(
                path=routes.CollectiveIdentifierRoutes.QUERY_BY_KSEF_NUMBER.format(
                    ksefNumber=ksef_number
                ),
                params=self.build_params(params, _QUERY_PARAMS),
                headers=headers,
            ),
            spec.CollectiveIdentifiersByKsefNumberQueryResponse,
        )

    async def list_invoices(
        self,
        body: spec.CollectiveIdentifierInvoicesQueryRequest,
        continuation_token: str | None = None,
        **params: Unpack[CollectiveIdentifierQueryParams],
    ) -> spec.CollectiveIdentifierInvoicesQueryResponse:
        """Fetch one page of invoices inside the supplied collective identifiers."""
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )
        return self._parse(
            await self._transport.post(
                path=routes.CollectiveIdentifierRoutes.LIST_INVOICES,
                params=self.build_params(params, _QUERY_PARAMS),
                headers=headers,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.CollectiveIdentifierInvoicesQueryResponse,
        )
