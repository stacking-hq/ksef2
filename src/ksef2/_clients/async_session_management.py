"""Async session-management branch client."""

from collections.abc import AsyncGenerator, AsyncIterator, Coroutine
from typing import final

from typing_extensions import deprecated

from ksef2._clients._async_pager import AsyncPager
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.auth import (
    AuthenticationSession,
    AuthenticationSessionsResponse,
)
from ksef2._endpoints.async_auth import AsyncAuthEndpoints
from ksef2._infra.mappers.auth import from_spec


@final
class AsyncSessionManagementClient:
    """Async manage authentication sessions opened through the auth API.

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
        self._auth_ep = AsyncAuthEndpoints(transport)

    async def _query(
        self,
        *,
        page_size: int | None = None,
        continuation_token: str | None = None,
    ) -> AuthenticationSessionsResponse:
        return from_spec(
            await self._auth_ep.list_sessions(
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def _pages(
        self, page_size: int | None
    ) -> AsyncGenerator[AuthenticationSessionsResponse, None]:
        response = await self._query(page_size=page_size)
        yield response

        while ct := response.continuation_token:
            response = await self._query(page_size=page_size, continuation_token=ct)
            yield response

    @deprecated(
        "`query()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    def query(
        self,
        *,
        page_size: int | None = None,
        continuation_token: str | None = None,
    ) -> Coroutine[None, None, AuthenticationSessionsResponse]:
        """Deprecated: fetch one page of authentication sessions.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list()`` instead; ``first_page()`` fetches one page.

        Args:
            page_size: Maximum number of sessions to request from KSeF.
            continuation_token: Cursor returned by a previous page.

        Returns:
            One page of authentication sessions for the current subject.
        """
        return self._query(page_size=page_size, continuation_token=continuation_token)

    @deprecated(
        "`all()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    async def all(
        self,
        *,
        page_size: int | None = None,
    ) -> AsyncIterator[AuthenticationSessionsResponse]:
        """Deprecated: iterate through all authentication session pages.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list().pages()`` instead.

        Args:
            page_size: Maximum number of sessions to request per page.

        Yields:
            Successive pages of authentication sessions until KSeF stops
            returning a continuation token.
        """
        async for page in self._pages(page_size):
            yield page

    async def terminate_current(self) -> None:
        """Terminate the authentication session backing the current bearer token."""
        await self._auth_ep.terminate_current_session()

    async def close(self, *, reference_number: str) -> None:
        """Terminate an authentication session by reference number.

        Args:
            reference_number: Reference number of the authentication session to terminate.
        """
        await self._auth_ep.terminate_auth_session(reference_number=reference_number)

    def list(
        self, *, page_size: int | None = None
    ) -> AsyncPager[AuthenticationSession]:
        """List the authentication sessions of the current subject.

        Nothing is requested until the result is consumed. Iterate it for every
        session, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            page_size: Maximum number of sessions to request per page; the KSeF default when ``None``.

        Returns:
            A paging object over the authentication sessions.

        Example:
            ```python
            async for session in auth.sessions.list():
                print(session.reference_number)
            ```
        """

        async def _session_pages() -> AsyncGenerator[list[AuthenticationSession], None]:
            async for page in self._pages(page_size):
                yield page.items

        return AsyncPager(_session_pages)
