"""Generic paging object returned by collection operations."""

from collections.abc import AsyncGenerator, AsyncIterator, Callable
from typing import Generic, TypeVar

from ksef2._core.polling import async_poll_until

_T = TypeVar("_T")


class AsyncPager(Generic[_T]):
    """Lazy view over a paged collection in KSeF.

    Iterating the pager yields every item across all pages, requesting pages as
    needed. ``pages()`` yields one list of items per page, and ``first_page()``
    fetches only the first. Nothing is requested until the pager is consumed, and
    every iteration starts from the first page again.

    Raises:
        KSeFApiError: If KSeF returns an API error response while a page is
            fetched.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(
        self,
        pages: Callable[[], AsyncGenerator[list[_T], None]],
        *,
        timeout_error: Callable[[float], BaseException] | None = None,
    ) -> None:
        """Create the pager.

        Args:
            pages: Factory returning a fresh async generator over the pages, each one a list of items.
            timeout_error: Builds the exception ``wait()`` raises from its timeout; ``None`` raises ``TimeoutError``.
        """
        self._pages = pages
        self._timeout_error = timeout_error

    def __aiter__(self) -> AsyncIterator[_T]:
        return self._items()

    async def _items(self) -> AsyncGenerator[_T, None]:
        async for page in self._pages():
            for item in page:
                yield item

    def pages(self) -> AsyncIterator[list[_T]]:
        """Iterate over the collection one page at a time.

        Returns:
            An iterator yielding the items of each page as a list, in order.
        """
        return self._pages()

    async def first_page(self) -> list[_T]:
        """Fetch only the first page.

        Returns:
            The items of the first page; empty if the collection is empty.
        """
        pages = self._pages()
        try:
            async for page in pages:
                return page
            return []
        finally:
            await pages.aclose()

    async def wait(
        self,
        *,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> "AsyncPager[_T]":
        """Poll until the collection contains at least one item.

        Use it when KSeF indexes items with a delay, for example invoices that were
        accepted a moment ago and are not searchable yet.

        Args:
            timeout: Maximum number of seconds to wait before giving up.
            poll_interval: Delay in seconds between checks.

        Returns:
            This pager, now known to be non-empty. Iterating it requests the pages again.

        Raises:
            KSeFInvoiceQueryTimeoutError: For invoice searches, if no invoice appears within ``timeout``.
            TimeoutError: For other collections, if no item appears within ``timeout``.
        """
        _ = await async_poll_until(
            operation=self.first_page,
            retry_predicate=lambda page: not page,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: self._build_timeout_error(timeout),
        )
        return self

    def _build_timeout_error(self, timeout: float) -> BaseException:
        if self._timeout_error is not None:
            return self._timeout_error(timeout)
        return TimeoutError(f"No items appeared after {timeout}s")
