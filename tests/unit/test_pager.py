"""The generic paging object: items, pages, first page and ``wait()``."""

import pytest

from ksef2._clients._async_pager import AsyncPager
from ksef2._clients._pager import Pager
from ksef2._core.exceptions import KSeFInvoiceQueryTimeoutError
from tests.unit.flavors import Flavor


class _Source:
    """A page source that records how far it was read."""

    def __init__(self, flavor: Flavor, pages: list[list[int]]) -> None:
        self.flavor = flavor
        self.pages = pages
        self.fetched = 0
        self.closed = 0
        self.runs = 0

    def pager(self, **kwargs: object) -> object:
        if self.flavor.is_async:

            async def _async_pages():
                self.runs += 1
                try:
                    for page in self.pages:
                        self.fetched += 1
                        yield list(page)
                finally:
                    self.closed += 1

            return AsyncPager(_async_pages, **kwargs)  # pyright: ignore[reportArgumentType]

        def _pages():
            self.runs += 1
            try:
                for page in self.pages:
                    self.fetched += 1
                    yield list(page)
            finally:
                self.closed += 1

        return Pager(_pages, **kwargs)  # pyright: ignore[reportArgumentType]


def test_iterating_yields_items_across_pages(flavor: Flavor) -> None:
    source = _Source(flavor, [[1, 2], [3], [4, 5]])

    assert flavor.collect(source.pager()) == [1, 2, 3, 4, 5]


def test_pages_yields_one_list_per_page(flavor: Flavor) -> None:
    source = _Source(flavor, [[1, 2], [3]])
    pager = source.pager()

    assert flavor.collect(pager.pages()) == [[1, 2], [3]]  # pyright: ignore[reportAttributeAccessIssue]


def test_nothing_is_fetched_until_the_pager_is_consumed(flavor: Flavor) -> None:
    source = _Source(flavor, [[1]])

    _ = source.pager()

    assert source.runs == 0


def test_first_page_fetches_only_the_first_page_and_closes_the_source(
    flavor: Flavor,
) -> None:
    source = _Source(flavor, [[1, 2], [3], [4]])
    pager = source.pager()

    assert flavor.run(pager.first_page()) == [1, 2]  # pyright: ignore[reportAttributeAccessIssue]
    assert source.fetched == 1
    assert source.closed == 1


def test_first_page_of_an_empty_collection_is_empty(flavor: Flavor) -> None:
    source = _Source(flavor, [])

    assert flavor.run(source.pager().first_page()) == []  # pyright: ignore[reportAttributeAccessIssue]


def test_every_iteration_starts_from_the_first_page(flavor: Flavor) -> None:
    source = _Source(flavor, [[1], [2]])
    pager = source.pager()

    assert flavor.collect(pager) == flavor.collect(pager) == [1, 2]
    assert source.runs == 2


def test_wait_polls_until_an_item_appears_and_returns_the_pager(
    flavor: Flavor,
) -> None:
    attempts = {"count": 0}

    if flavor.is_async:

        async def _async_pages():
            attempts["count"] += 1
            yield [] if attempts["count"] < 3 else [42]

        pager = AsyncPager(_async_pages)
    else:

        def _pages():
            attempts["count"] += 1
            yield [] if attempts["count"] < 3 else [42]

        pager = Pager(_pages)

    assert flavor.run(pager.wait(timeout=1.0, poll_interval=0.0)) is pager
    assert attempts["count"] == 3


def test_wait_raises_the_supplied_timeout_error(flavor: Flavor) -> None:
    source = _Source(flavor, [[]])
    pager = source.pager(
        timeout_error=lambda timeout: KSeFInvoiceQueryTimeoutError(timeout=timeout)
    )

    with pytest.raises(KSeFInvoiceQueryTimeoutError):
        flavor.run(pager.wait(timeout=0.0, poll_interval=0.0))  # pyright: ignore[reportAttributeAccessIssue]


def test_wait_raises_timeout_error_by_default(flavor: Flavor) -> None:
    source = _Source(flavor, [[]])

    with pytest.raises(TimeoutError):
        flavor.run(source.pager().wait(timeout=0.0, poll_interval=0.0))  # pyright: ignore[reportAttributeAccessIssue]
