"""Async PEPPOL branch client."""

from collections.abc import AsyncGenerator, AsyncIterator, Coroutine
from typing import final

from typing_extensions import deprecated

from ksef2._clients._async_pager import AsyncPager
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.pagination import OffsetPaginationParams
from ksef2._domain.models.peppol import ListPeppolProvidersResponse, PeppolProvider
from ksef2._endpoints.async_peppol import AsyncPeppolEndpoints
from ksef2._infra.mappers.peppol import from_spec


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
        """Create the client.

        Args:
            transport: Middleware chain used for requests to KSeF.
        """
        self._transport = transport
        self._endpoints = AsyncPeppolEndpoints(transport)

    async def _query(
        self,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> ListPeppolProvidersResponse:
        current_params = params or OffsetPaginationParams()
        response = await self._endpoints.query_providers(
            **current_params.to_query_params()
        )
        return from_spec(response)

    async def _pages(
        self, params: OffsetPaginationParams | None
    ) -> AsyncGenerator[ListPeppolProvidersResponse, None]:
        current_params = params or OffsetPaginationParams()

        while True:
            response = await self._query(params=current_params)
            yield response

            if not response.has_more:
                break

            current_params = current_params.next_page()

    @deprecated(
        "`query()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    def query(
        self,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, ListPeppolProvidersResponse]:
        """Deprecated: query one page of Peppol service providers.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list()`` instead; ``first_page()`` fetches one page.

        Args:
            params: Pagination parameters.

        Returns:
            One page of providers with pagination info.
        """
        return self._query(params=params)

    @deprecated(
        "`all()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    async def all(
        self, *, params: OffsetPaginationParams | None = None
    ) -> AsyncIterator[PeppolProvider]:
        """Deprecated: iterate over all Peppol service providers.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list()`` instead.

        Args:
            params: Pagination parameters.

        Yields:
            Each Peppol service provider, across all pages.
        """
        async for page in self._pages(params):
            for provider in page.providers:
                yield provider

    def list(
        self, *, params: OffsetPaginationParams | None = None
    ) -> AsyncPager[PeppolProvider]:
        """List the registered Peppol service providers.

        Nothing is requested until the result is consumed. Iterate it for every
        provider, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the Peppol service providers.

        Example:
            ```python
            async for provider in auth.peppol.list():
                print(provider.id, provider.name)
            ```
        """

        async def _provider_pages() -> AsyncGenerator[list[PeppolProvider], None]:
            async for page in self._pages(params):
                yield page.providers

        return AsyncPager(_provider_pages)
