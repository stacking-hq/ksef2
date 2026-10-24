"""The generic paging object: items, pages, first page, cursors and ``wait()``."""

import json

import pytest

from ksef2._clients._async_pager import AsyncPager
from ksef2._clients._pagination_cursor import CURSOR_VERSION, OffsetCursor
from ksef2._clients._pager import Pager
from ksef2._core.exceptions import (
    KSeFArgumentError,
    KSeFInvoiceQueryTimeoutError,
)
from ksef2._domain.models.pagination import Page
from tests.unit.support.flavors import Flavor

OPERATION = "pager.test"


class _CursorSource:
    """A cursor page source that serves fixed pages and counts the requests it serves."""

    def __init__(self, flavor: Flavor, pages: list[list[int]]) -> None:
        self.flavor = flavor
        self.pages = pages
        self.fetched = 0

    def pager(self) -> Pager[int] | AsyncPager[int]:
        if self.flavor.is_async:
            return AsyncPager[int](fetch_page=self.fetch_async)
        return Pager[int](fetch_page=self.fetch)

    def fetch(self, cursor: str | None) -> Page[int]:
        index = (
            0
            if cursor is None
            else OffsetCursor.decode(cursor, operation=OPERATION).page_offset
        )
        self.fetched += 1
        items = self.pages[index] if index < len(self.pages) else []
        return Page(
            items=list(items),
            next_cursor=OffsetCursor.encode_next(
                operation=OPERATION,
                page_offset=index,
                has_more=index + 1 < len(self.pages),
            ),
        )

    async def fetch_async(self, cursor: str | None) -> Page[int]:
        return self.fetch(cursor)


class _SyncPageSpy(Pager[int]):
    """Sync pager that records every cursor its own callers hand to ``page()``."""

    def __init__(self, source: _CursorSource) -> None:
        super().__init__(fetch_page=source.fetch)
        self.cursors: list[str | None] = []

    def page(self, cursor: str | None = None) -> Page[int]:
        self.cursors.append(cursor)
        return super().page(cursor)


class _AsyncPageSpy(AsyncPager[int]):
    """Async pager that records every cursor its own callers hand to ``page()``."""

    def __init__(self, source: _CursorSource) -> None:
        super().__init__(fetch_page=source.fetch_async)
        self.cursors: list[str | None] = []

    async def page(self, cursor: str | None = None) -> Page[int]:
        self.cursors.append(cursor)
        return await super().page(cursor)


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


def test_page_requires_a_page_source() -> None:
    with pytest.raises(KSeFArgumentError, match="needs a source of pages"):
        Pager[int]()  # pyright: ignore[reportCallIssue]


def test_page_returns_a_serializable_model(flavor: Flavor) -> None:
    source = _CursorSource(flavor, [[1, 2], [3]])

    page = flavor.run(source.pager().page(None))

    assert isinstance(page, Page)
    assert page.items == [1, 2]
    assert isinstance(page.next_cursor, str)
    assert Page[int].model_validate_json(page.model_dump_json()) == page


def test_first_page_uses_the_cursor_source(flavor: Flavor) -> None:
    source = _CursorSource(flavor, [[1, 2], [3]])

    assert flavor.run(source.pager().first_page()) == [1, 2]
    assert source.fetched == 1


def test_first_page_and_iteration_use_public_page(flavor: Flavor) -> None:
    """``first_page()`` and the page walk both go through the caller-visible ``page()``.

    An empty page in the middle proves the walk follows ``next_cursor`` rather than
    stopping on the first page with no items, and the last page carries no cursor, which
    is what ends the walk.
    """
    source = _CursorSource(flavor, [[1], [], [2, 3]])
    pager = _AsyncPageSpy(source) if flavor.is_async else _SyncPageSpy(source)

    assert flavor.run(pager.first_page()) == [1]
    assert flavor.collect(pager.pages()) == [[1], [], [2, 3]]

    # One request per page: the first page, then three pages walked by cursor.
    assert source.fetched == 4
    # Each walk asks for the first page once and then hands on the cursor it was given.
    asked = pager.cursors
    assert asked[0] is None
    assert asked[1] is None
    assert all(cursor is not None for cursor in asked[2:])


def test_page_resume_on_fresh_pager(flavor: Flavor) -> None:
    pages = [[1, 2], [3], [4]]
    first = _CursorSource(flavor, pages)
    page = flavor.run(first.pager().page(None))

    assert page.items == [1, 2]
    assert page.next_cursor is not None

    # A pager built from scratch, as after a restart, continues from the cursor string.
    carried = json.loads(json.dumps({"cursor": str(page.next_cursor)}))["cursor"]
    restarted = _CursorSource(flavor, pages)
    resumed = flavor.run(restarted.pager().page(carried))

    assert resumed.items == [3]
    assert resumed.next_cursor is not None
    assert restarted.fetched == 1

    last = flavor.run(restarted.pager().page(resumed.next_cursor))
    assert last.items == [4]
    assert last.next_cursor is None


def test_iterating_a_cursor_pager_walks_every_page(flavor: Flavor) -> None:
    source = _CursorSource(flavor, [[1], [2], [3]])
    pager = source.pager()

    assert flavor.collect(pager) == [1, 2, 3]
    assert flavor.collect(pager.pages()) == [[1], [2], [3]]
    assert source.fetched == 6


def test_pages_continues_after_empty_page_with_cursor(flavor: Flavor) -> None:
    source = _CursorSource(flavor, [[1], [], [2]])

    assert flavor.collect(source.pager()) == [1, 2]
    assert flavor.collect(source.pager().pages()) == [[1], [], [2]]
    assert source.fetched == 6


def test_page_does_not_advance_other_consumers(flavor: Flavor) -> None:
    source = _CursorSource(flavor, [[1], [2]])
    pager = source.pager()

    first = flavor.run(pager.page(None))
    again = flavor.run(pager.page(None))
    assert again == first

    assert flavor.collect(pager.pages()) == [[1], [2]]
    assert source.fetched == 4


@pytest.mark.parametrize(
    ("cursor", "reason"),
    [
        ("not a cursor!!", "not URL-safe Base64"),
        ("bm90IGpzb24=", "not valid JSON"),
        ("Imp1c3QgYSBzdHJpbmci", "not a JSON object"),
    ],
    ids=["bad-base64", "not-json", "not-an-object"],
)
def test_page_rejects_invalid_cursor_before_fetch(
    flavor: Flavor, cursor: str, reason: str
) -> None:
    source = _CursorSource(flavor, [[1]])

    with pytest.raises(KSeFArgumentError, match=reason):
        flavor.run(source.pager().page(cursor))

    assert source.fetched == 0


def test_page_rejects_a_cursor_of_another_shape(flavor: Flavor) -> None:
    source = _CursorSource(flavor, [[1]])
    other_operation = OffsetCursor(
        v=CURSOR_VERSION, operation="pager.other", page_offset=1
    ).encode()

    with pytest.raises(KSeFArgumentError, match="not for pager.test"):
        flavor.run(source.pager().page(other_operation))

    assert source.fetched == 0


def test_legacy_pager_page_cursor_roundtrip(flavor: Flavor) -> None:
    source = _Source(flavor, [[1, 2], [3], [4]])
    pager = source.pager()

    first = flavor.run(pager.page(None))  # pyright: ignore[reportAttributeAccessIssue]
    assert first.items == [1, 2]
    assert first.next_cursor is not None

    second = flavor.run(pager.page(first.next_cursor))  # pyright: ignore[reportAttributeAccessIssue]
    assert second.items == [3]
    assert second.next_cursor is not None

    third = flavor.run(pager.page(second.next_cursor))  # pyright: ignore[reportAttributeAccessIssue]
    assert third.items == [4]
    assert third.next_cursor is None

    # Iteration keeps using the caller's generator, so its contract is untouched.
    assert flavor.collect(pager) == [1, 2, 3, 4]
    # Each page() call closes the generator it opened, and iteration closes its own.
    assert source.closed == 4
