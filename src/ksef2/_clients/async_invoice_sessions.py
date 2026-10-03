"""Async invoice-session branch client."""

import builtins
from collections.abc import AsyncGenerator, AsyncIterator, Coroutine
from typing import final

from typing_extensions import deprecated

from ksef2._clients._async_pager import AsyncPager
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.pagination import ListSessionsQuery
from ksef2._domain.models.session import (
    ListSessionsResponse,
    SessionStatus,
    SessionStatusEnum,
    SessionSummary,
    normalize_session_status,
    normalize_session_type,
)
from ksef2._endpoints.async_session import AsyncSessionEndpoints
from ksef2._infra.mappers.sessions import from_spec


@final
class AsyncInvoiceSessionsClient:
    """Async browse historical online and batch invoice sessions.

    Catch ``KSeFException`` for SDK-classified failures raised by this branch,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(self, transport: AsyncMiddleware) -> None:
        """Create the client.

        Args:
            transport: Middleware chain used for requests to KSeF.
        """
        self._endpoints = AsyncSessionEndpoints(transport)

    async def _query(
        self,
        *,
        session_type: str,
        continuation_token: str | None = None,
        params: ListSessionsQuery | None = None,
        statuses: builtins.list[SessionStatus | SessionStatusEnum] | None = None,
    ) -> ListSessionsResponse:
        parameters = params or ListSessionsQuery(
            session_type=normalize_session_type(session_type),
        )
        if statuses is not None:
            parameters = parameters.model_copy(
                update={
                    "statuses": [
                        normalize_session_status(status) for status in statuses
                    ]
                }
            )

        return from_spec(
            await self._endpoints.list_sessions(
                continuation_token=continuation_token,
                **parameters.to_query_params(),
            )
        )

    async def _pages(
        self,
        session_type: str,
        params: ListSessionsQuery | None,
        statuses: builtins.list[SessionStatus | SessionStatusEnum] | None = None,
    ) -> AsyncGenerator[ListSessionsResponse, None]:
        parameters = params or ListSessionsQuery(
            session_type=normalize_session_type(session_type),
        )

        response = await self._query(
            session_type=session_type,
            params=parameters,
            statuses=statuses,
        )
        yield response

        while continuation_token := response.continuation_token:
            response = await self._query(
                session_type=session_type,
                continuation_token=continuation_token,
                params=parameters,
                statuses=statuses,
            )
            yield response

    @deprecated(
        "`query()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    def query(
        self,
        *,
        session_type: str,
        continuation_token: str | None = None,
        params: ListSessionsQuery | None = None,
        statuses: builtins.list[SessionStatus | SessionStatusEnum] | None = None,
    ) -> Coroutine[None, None, ListSessionsResponse]:
        """Deprecated: fetch one page of invoice session history for the chosen session type.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list()`` instead; ``first_page()`` fetches one page.

        Args:
            session_type: Invoice session family to browse, such as ``"online"``
                or ``"batch"``.
            continuation_token: Cursor returned by a previous page.
            params: Optional query object with pagination and filter settings.
            statuses: Optional list of status filters applied on top of ``params``.

        Returns:
            One page of historical invoice sessions.
        """
        return self._query(
            session_type=session_type,
            continuation_token=continuation_token,
            params=params,
            statuses=statuses,
        )

    @deprecated(
        "`all()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    async def all(
        self,
        *,
        session_type: str,
        params: ListSessionsQuery | None = None,
    ) -> AsyncIterator[ListSessionsResponse]:
        """Deprecated: iterate through all pages of invoice session history.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list().pages()`` instead.

        Args:
            session_type: Invoice session family to browse, such as ``"online"``
                or ``"batch"``.
            params: Optional query object with pagination and filter settings.

        Yields:
            Successive pages of historical invoice sessions until KSeF stops
            returning a continuation token.
        """
        async for page in self._pages(session_type, params):
            yield page

    def list(
        self,
        session_type: str,
        *,
        params: ListSessionsQuery | None = None,
        statuses: builtins.list[SessionStatus | SessionStatusEnum] | None = None,
    ) -> AsyncPager[SessionSummary]:
        """List the invoice sessions of the chosen type, newest history first as KSeF returns it.

        Nothing is requested until the result is consumed. Iterate it for every
        session, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            session_type: Invoice session family to browse, such as ``"online"`` or ``"batch"``.
            params: Optional query object with page size and filter settings.
            statuses: Optional list of status filters applied on top of ``params``.

        Returns:
            A paging object over the matching invoice sessions.

        Example:
            ```python
            async for session in auth.invoice_sessions.list("online"):
                print(session.reference_number, session.status)
            ```
        """

        async def _session_pages() -> AsyncGenerator[list[SessionSummary], None]:
            async for page in self._pages(session_type, params, statuses):
                yield page.sessions

        return AsyncPager(_session_pages)
