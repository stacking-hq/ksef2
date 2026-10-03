"""Async client for collective invoice identifiers."""

from collections.abc import AsyncGenerator, AsyncIterator, Coroutine
from typing import final

from typing_extensions import deprecated

from ksef2._clients._async_pager import AsyncPager
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.collective_identifiers import (
    CollectiveIdentifierInvoice,
    CollectiveIdentifierInvoiceDetails,
    CollectiveIdentifierInvoicesPage,
    CollectiveIdentifierInvoicesQuery,
    CollectiveIdentifierReference,
    CollectiveIdentifierReferencesPage,
    CollectiveIdentifierSummary,
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
        """Create the client.

        Args:
            transport: Middleware chain used for requests to KSeF.
        """
        self._endpoints = AsyncCollectiveIdentifiersEndpoints(transport)

    async def generate(
        self,
        *,
        invoices: list[CollectiveIdentifierInvoice],
    ) -> GenerateCollectiveIdentifierResponse:
        """Generate a collective identifier for the supplied invoices.

        Args:
            invoices: Invoices to group, with optional payment details.

        Returns:
            The generated collective identifier number.
        """
        return from_spec(await self._endpoints.generate(body=to_spec(invoices)))

    async def _query(
        self,
        *,
        filters: CollectiveIdentifiersQuery,
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> CollectiveIdentifiersPage:
        parameters = params or CollectiveIdentifierParams()
        return from_spec(
            await self._endpoints.query(
                body=to_spec(filters),
                continuation_token=continuation_token,
                **parameters.to_query_params(),
            )
        )

    async def _query_pages(
        self,
        filters: CollectiveIdentifiersQuery,
        params: CollectiveIdentifierParams | None,
    ) -> AsyncGenerator[CollectiveIdentifiersPage, None]:
        parameters = params or CollectiveIdentifierParams()
        response = await self._query(filters=filters, params=parameters)
        yield response

        while continuation_token := response.continuation_token:
            response = await self._query(
                filters=filters,
                continuation_token=continuation_token,
                params=parameters,
            )
            yield response

    async def _query_by_ksef_number(
        self,
        *,
        ksef_number: str,
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> CollectiveIdentifierReferencesPage:
        parameters = params or CollectiveIdentifierParams()
        return from_spec(
            await self._endpoints.query_by_ksef_number(
                ksef_number=ksef_number,
                continuation_token=continuation_token,
                **parameters.to_query_params(),
            )
        )

    async def _query_by_ksef_number_pages(
        self,
        ksef_number: str,
        params: CollectiveIdentifierParams | None,
    ) -> AsyncGenerator[CollectiveIdentifierReferencesPage, None]:
        parameters = params or CollectiveIdentifierParams()
        response = await self._query_by_ksef_number(
            ksef_number=ksef_number,
            params=parameters,
        )
        yield response

        while continuation_token := response.continuation_token:
            response = await self._query_by_ksef_number(
                ksef_number=ksef_number,
                continuation_token=continuation_token,
                params=parameters,
            )
            yield response

    async def _list_invoices(
        self,
        *,
        collective_identifier_numbers: list[str],
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> CollectiveIdentifierInvoicesPage:
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

    async def _list_invoices_pages(
        self,
        collective_identifier_numbers: list[str],
        params: CollectiveIdentifierParams | None,
    ) -> AsyncGenerator[CollectiveIdentifierInvoicesPage, None]:
        parameters = params or CollectiveIdentifierParams()
        response = await self._list_invoices(
            collective_identifier_numbers=collective_identifier_numbers,
            params=parameters,
        )
        yield response

        while continuation_token := response.continuation_token:
            response = await self._list_invoices(
                collective_identifier_numbers=collective_identifier_numbers,
                continuation_token=continuation_token,
                params=parameters,
            )
            yield response

    @deprecated(
        "`query()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    def query(
        self,
        *,
        filters: CollectiveIdentifiersQuery,
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> Coroutine[None, None, CollectiveIdentifiersPage]:
        """Deprecated: fetch one page of collective identifiers visible in the context.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list()`` instead; ``first_page()`` fetches one page.

        Args:
            filters: Criteria selecting collective identifiers.
            continuation_token: Token from the previous page's response; ``None`` requests the first page.
            params: Page size; defaults are used when ``None``.

        Returns:
            One page of matching collective identifiers.
        """
        return self._query(
            filters=filters,
            continuation_token=continuation_token,
            params=params,
        )

    @deprecated(
        "`query_all()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    async def query_all(
        self,
        *,
        filters: CollectiveIdentifiersQuery,
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncIterator[CollectiveIdentifiersPage]:
        """Deprecated: iterate through every page matching a collective identifier query.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list().pages()`` instead.

        Args:
            filters: Criteria selecting collective identifiers.
            params: Page size; defaults are used when ``None``.

        Yields:
            Each page of matching collective identifiers, following continuation tokens.
        """
        async for page in self._query_pages(filters, params):
            yield page

    @deprecated(
        "`query_by_ksef_number()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_for_invoice()` instead."
    )
    def query_by_ksef_number(
        self,
        *,
        ksef_number: str,
        continuation_token: str | None = None,
        params: CollectiveIdentifierParams | None = None,
    ) -> Coroutine[None, None, CollectiveIdentifierReferencesPage]:
        """Deprecated: fetch one page of identifiers associated with a KSeF invoice.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_for_invoice()`` instead; ``first_page()`` fetches one page.

        Args:
            ksef_number: KSeF number of the invoice.
            continuation_token: Token from the previous page's response; ``None`` requests the first page.
            params: Page size; defaults are used when ``None``.

        Returns:
            One page of collective identifiers that reference the invoice.
        """
        return self._query_by_ksef_number(
            ksef_number=ksef_number,
            continuation_token=continuation_token,
            params=params,
        )

    @deprecated(
        "`query_all_by_ksef_number()` is deprecated and will be removed in "
        "ksef2 1.10.0; use `list_for_invoice()` instead."
    )
    async def query_all_by_ksef_number(
        self,
        *,
        ksef_number: str,
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncIterator[CollectiveIdentifierReferencesPage]:
        """Deprecated: iterate through identifiers associated with one KSeF invoice.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_for_invoice().pages()`` instead.

        Args:
            ksef_number: KSeF number of the invoice.
            params: Page size; defaults are used when ``None``.

        Yields:
            Each page of identifiers that reference the invoice, following continuation tokens.
        """
        async for page in self._query_by_ksef_number_pages(ksef_number, params):
            yield page

    @deprecated(
        "`list_all_invoices()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_invoices()` instead."
    )
    async def list_all_invoices(
        self,
        *,
        collective_identifier_numbers: list[str],
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncIterator[CollectiveIdentifierInvoicesPage]:
        """Deprecated: iterate through every invoice page for the supplied collective identifiers.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_invoices().pages()`` instead.

        Args:
            collective_identifier_numbers: Collective identifier numbers to expand (1–10).
            params: Page size; defaults are used when ``None``.

        Yields:
            Each page of invoices, following continuation tokens.
        """
        async for page in self._list_invoices_pages(
            collective_identifier_numbers, params
        ):
            yield page

    def list_for_invoice(
        self,
        ksef_number: str,
        *,
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncPager[CollectiveIdentifierReference]:
        """List the collective identifiers that reference one KSeF invoice.

        Nothing is requested until the result is consumed.

        Args:
            ksef_number: KSeF number of the invoice.
            params: Page size; defaults are used when ``None``.

        Returns:
            A paging object over the collective identifiers referencing the invoice.

        Example:
            ```python
            async for reference in auth.collective_identifiers.list_for_invoice(ksef_number):
                print(reference.collective_identifier_number)
            ```
        """

        async def _reference_pages() -> AsyncGenerator[
            list[CollectiveIdentifierReference], None
        ]:
            async for page in self._query_by_ksef_number_pages(ksef_number, params):
                yield page.collective_identifiers

        return AsyncPager(_reference_pages)

    def list_invoices(
        self,
        collective_identifier_numbers: list[str],
        *,
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncPager[CollectiveIdentifierInvoiceDetails]:
        """List the invoices inside the supplied collective identifiers.

        Nothing is requested until the result is consumed. Unlike the former
        ``list_invoices()``, which fetched one page, this returns a paging object.

        Args:
            collective_identifier_numbers: Collective identifier numbers to expand (1–10).
            params: Page size; defaults are used when ``None``.

        Returns:
            A paging object over the invoices belonging to the identifiers.

        Example:
            ```python
            async for invoice in auth.collective_identifiers.list_invoices([number]):
                print(invoice.ksef_number)
            ```
        """

        async def _invoice_pages() -> AsyncGenerator[
            list[CollectiveIdentifierInvoiceDetails], None
        ]:
            async for page in self._list_invoices_pages(
                collective_identifier_numbers, params
            ):
                yield page.invoices

        return AsyncPager(_invoice_pages)

    def list(
        self,
        filters: CollectiveIdentifiersQuery,
        *,
        params: CollectiveIdentifierParams | None = None,
    ) -> AsyncPager[CollectiveIdentifierSummary]:
        """List the collective identifiers visible in the context.

        Nothing is requested until the result is consumed. Iterate it for every
        identifier, call ``pages()`` for page-sized lists or ``first_page()`` for
        one request only.

        Args:
            filters: Criteria selecting collective identifiers.
            params: Page size; defaults are used when ``None``.

        Returns:
            A paging object over the matching collective identifiers.

        Example:
            ```python
            async for identifier in auth.collective_identifiers.list(filters):
                print(identifier.collective_identifier_number)
            ```
        """

        async def _identifier_pages() -> AsyncGenerator[
            list[CollectiveIdentifierSummary], None
        ]:
            async for page in self._query_pages(filters, params):
                yield page.collective_identifiers

        return AsyncPager(_identifier_pages)
