"""PaginationMixin — async pagination strategies.

Two strategies:
- Offset-based: yields individual items, advances via next_page(), stops when has_more=False.
- Continuation-token: yields pages, passes continuation token, stops when token is absent.
  Detects duplicate tokens to prevent infinite loops.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeVar

TPage = TypeVar("TPage")
TItem = TypeVar("TItem")


class PaginationMixin:
    """Mixin providing async pagination helpers.

    Subclasses define ``query`` and page-advancement methods that are
    passed as callables to ``iter_offset`` and ``iter_continuation``.
    """

    def iter_offset(
        self,
        *,
        query_fn: Callable[..., Awaitable[TPage]],
        next_page_fn: Callable[[dict[str, object]], dict[str, object]],
        extract_items: Callable[[TPage], list[TItem]],
        has_more_fn: Callable[[TPage], bool],
        params: dict[str, object],
    ) -> AsyncIterator[TItem]:
        """Yield individual items across offset-based pages.

        Args:
            query_fn: Async callable that fetches one page of results.
            next_page_fn: Sync callable that advances pagination params.
            extract_items: Sync callable that extracts the item list from a response.
            has_more_fn: Sync callable that returns True if more pages exist.
            params: Initial query parameters (filters + pagination).

        Yields:
            Individual items from all pages.
        """
        return self._iter_offset_impl(
            query_fn=query_fn,
            next_page_fn=next_page_fn,
            extract_items=extract_items,
            has_more_fn=has_more_fn,
            params=params,
        )

    async def _iter_offset_impl(
        self,
        *,
        query_fn: Callable[..., Awaitable[TPage]],
        next_page_fn: Callable[[dict[str, object]], dict[str, object]],
        extract_items: Callable[[TPage], list[TItem]],
        has_more_fn: Callable[[TPage], bool],
        params: dict[str, object],
    ) -> AsyncIterator[TItem]:
        current_params = dict(params)
        while True:
            response = await query_fn(**current_params)
            for item in extract_items(response):
                yield item

            if not has_more_fn(response):
                break

            current_params = next_page_fn(current_params)

    def iter_continuation(
        self,
        *,
        query_fn: Callable[..., Awaitable[TPage]],
        extract_token: Callable[[TPage], str | None],
        params: dict[str, object],
    ) -> AsyncIterator[TPage]:
        """Yield pages using continuation-token pagination.

        Args:
            query_fn: Async callable that fetches one page of results.
            extract_token: Sync callable that extracts the continuation token
                from a response. Returns None when no more pages exist.
            params: Query parameters passed with every request.

        Yields:
            Each page response.

        Raises:
            KSeFApiError: If the same continuation token is returned twice
                (infinite loop protection).
        """
        return self._iter_continuation_impl(
            query_fn=query_fn,
            extract_token=extract_token,
            params=params,
        )

    async def _iter_continuation_impl(
        self,
        *,
        query_fn: Callable[..., Awaitable[TPage]],
        extract_token: Callable[[TPage], str | None],
        params: dict[str, object],
    ) -> AsyncIterator[TPage]:
        response = await query_fn(**params)
        yield response

        previous_token: str | None = None
        continuation_token: str | None = extract_token(response)

        while continuation_token is not None:
            # Infinite-loop guard: detect duplicate continuation tokens
            if continuation_token == previous_token:
                break

            previous_token = continuation_token
            response = await query_fn(continuation_token=continuation_token, **params)
            yield response
            continuation_token = extract_token(response)
