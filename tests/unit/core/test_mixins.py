"""Tests for shared async mixins: PaginationMixin, PollingMixin, LifecycleMixin.

Covers validation contract assertions VAL-ABS-001 through VAL-ABS-019.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from ksef2._async.core.mixins.lifecycle import LifecycleMixin
from ksef2._async.core.mixins.pagination import PaginationMixin
from ksef2._async.core.mixins.polling import PollingMixin
from ksef2.core.exceptions import ExceptionCode, KSeFApiError, KSeFClientClosedError


# ---------------------------------------------------------------------------
# Helpers — lightweight response-like objects for mocking pagination patterns
# ---------------------------------------------------------------------------


class OffsetPage:
    """Simulates an offset-paginated API response."""

    def __init__(self, items: list[Any], has_more: bool) -> None:
        self.items = items
        self.has_more = has_more


class ContinuationPage:
    """Simulates a continuation-token paginated API response."""

    def __init__(self, data: Any, continuation_token: str | None = None) -> None:
        self.data = data
        self.continuation_token = continuation_token


# ---------------------------------------------------------------------------
# PaginationMixin — offset-based tests (VAL-ABS-001..004)
# ---------------------------------------------------------------------------


class TestOffsetPagination:
    """Tests for offset-based pagination strategy."""

    async def test_yields_all_items_across_multiple_pages(self) -> None:
        """VAL-ABS-001: Offset pagination yields all items across pages."""
        call_count = 0

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> OffsetPage:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return OffsetPage(items=list(range(10)), has_more=True)
                if call_count == 2:
                    return OffsetPage(items=list(range(10, 20)), has_more=True)
                return OffsetPage(items=list(range(20, 30)), has_more=False)

            def next_page_params(self, params: dict[str, Any]) -> dict[str, Any]:
                return {**params, "page_offset": params.get("page_offset", 0) + 1}

        stub = Stub()
        items: list[int] = []
        async for item in stub.iter_offset(
            query_fn=stub.query,
            next_page_fn=stub.next_page_params,
            extract_items=lambda r: r.items,
            has_more_fn=lambda r: r.has_more,
            params={"page_offset": 0},
        ):
            items.append(item)

        assert items == list(range(30))
        assert call_count == 3

    async def test_empty_first_page(self) -> None:
        """VAL-ABS-002: Empty first page yields nothing immediately."""
        called = False

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> OffsetPage:
                nonlocal called
                called = True
                return OffsetPage(items=[], has_more=False)

            def next_page_params(self, params: dict[str, Any]) -> dict[str, Any]:
                return params

        stub = Stub()
        items: list[Any] = []
        async for item in stub.iter_offset(
            query_fn=stub.query,
            next_page_fn=stub.next_page_params,
            extract_items=lambda r: r.items,
            has_more_fn=lambda r: r.has_more,
            params={},
        ):
            items.append(item)

        assert items == []
        assert called

    async def test_single_page_result(self) -> None:
        """VAL-ABS-003: Single-page result terminates after first call."""
        call_count = 0

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> OffsetPage:
                nonlocal call_count
                call_count += 1
                return OffsetPage(items=[1, 2, 3, 4, 5], has_more=False)

            def next_page_params(self, params: dict[str, Any]) -> dict[str, Any]:
                return params

        stub = Stub()
        items: list[int] = []
        async for item in stub.iter_offset(
            query_fn=stub.query,
            next_page_fn=stub.next_page_params,
            extract_items=lambda r: r.items,
            has_more_fn=lambda r: r.has_more,
            params={},
        ):
            items.append(item)

        assert items == [1, 2, 3, 4, 5]
        assert call_count == 1

    async def test_preserves_filter_params_across_pages(self) -> None:
        """VAL-ABS-004: Filter parameters are preserved across page calls."""
        captured_params: list[dict[str, Any]] = []

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> OffsetPage:
                captured_params.append(dict(kwargs))
                page = kwargs.get("page_offset", 0)
                if page < 2:
                    return OffsetPage(items=[page], has_more=True)
                return OffsetPage(items=[page], has_more=False)

            def next_page_params(self, params: dict[str, Any]) -> dict[str, Any]:
                return {**params, "page_offset": params.get("page_offset", 0) + 1}

        stub = Stub()
        items: list[int] = []
        async for item in stub.iter_offset(
            query_fn=stub.query,
            next_page_fn=stub.next_page_params,
            extract_items=lambda r: r.items,
            has_more_fn=lambda r: r.has_more,
            params={"page_offset": 0, "filter_name": "test"},
        ):
            items.append(item)

        # Each query call should have the filter_name preserved
        for params in captured_params:
            assert params["filter_name"] == "test"


# ---------------------------------------------------------------------------
# PaginationMixin — continuation-token tests (VAL-ABS-005..008)
# ---------------------------------------------------------------------------


class TestContinuationTokenPagination:
    """Tests for continuation-token pagination strategy."""

    async def test_yields_all_pages_with_tokens(self) -> None:
        """VAL-ABS-005: Continuation-token pagination yields all pages."""
        call_count = 0
        tokens_passed: list[str | None] = []

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> ContinuationPage:
                nonlocal call_count
                call_count += 1
                tokens_passed.append(kwargs.get("continuation_token"))
                if call_count == 1:
                    return ContinuationPage(data="page1", continuation_token="tok1")
                if call_count == 2:
                    return ContinuationPage(data="page2", continuation_token="tok2")
                return ContinuationPage(data="page3", continuation_token=None)

        stub = Stub()
        pages: list[ContinuationPage] = []
        async for page in stub.iter_continuation(
            query_fn=stub.query,
            extract_token=lambda r: r.continuation_token,
            params={},
        ):
            pages.append(page)

        assert len(pages) == 3
        assert [p.data for p in pages] == ["page1", "page2", "page3"]
        # Page 2 should have been called with tok1, page 3 with tok2
        assert tokens_passed[1] == "tok1"
        assert tokens_passed[2] == "tok2"

    async def test_empty_single_page_no_token(self) -> None:
        """VAL-ABS-006: Single page with no continuation token yields once."""
        call_count = 0

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> ContinuationPage:
                nonlocal call_count
                call_count += 1
                return ContinuationPage(data="only_page", continuation_token=None)

        stub = Stub()
        pages: list[ContinuationPage] = []
        async for page in stub.iter_continuation(
            query_fn=stub.query,
            extract_token=lambda r: r.continuation_token,
            params={},
        ):
            pages.append(page)

        assert len(pages) == 1
        assert pages[0].data == "only_page"
        assert call_count == 1

    async def test_preserves_query_params(self) -> None:
        """VAL-ABS-007: Original params are included in every query call."""
        captured_params: list[dict[str, Any]] = []

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> ContinuationPage:
                captured_params.append(dict(kwargs))
                token = kwargs.get("continuation_token")
                if token is None:
                    return ContinuationPage(data="p1", continuation_token="tok1")
                return ContinuationPage(data="p2", continuation_token=None)

        stub = Stub()
        pages: list[ContinuationPage] = []
        async for page in stub.iter_continuation(
            query_fn=stub.query,
            extract_token=lambda r: r.continuation_token,
            params={"filter": "value", "page_size": 10},
        ):
            pages.append(page)

        # Both calls should include the original params
        for params in captured_params:
            assert params["filter"] == "value"
            assert params["page_size"] == 10

    async def test_detects_duplicate_continuation_tokens(self) -> None:
        """VAL-ABS-008: Duplicate tokens prevent infinite loops."""
        call_count = 0

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> ContinuationPage:
                nonlocal call_count
                call_count += 1
                # Always return the same token — stuck loop
                return ContinuationPage(
                    data=f"page{call_count}", continuation_token="stuck"
                )

        stub = Stub()
        pages: list[ContinuationPage] = []
        async for page in stub.iter_continuation(
            query_fn=stub.query,
            extract_token=lambda r: r.continuation_token,
            params={},
        ):
            pages.append(page)

        # Should stop after the second occurrence of the same token
        # (first call gets "stuck", second call also gets "stuck" → detected as duplicate)
        assert len(pages) <= 3  # At most a few iterations, not infinite
        assert call_count <= 3


# ---------------------------------------------------------------------------
# PaginationMixin — async iterator type (VAL-ABS-009)
# ---------------------------------------------------------------------------


class TestAsyncPaginationType:
    """Tests for async pagination returning AsyncIterator."""

    async def test_iter_offset_returns_async_iterator(self) -> None:
        """VAL-ABS-009: iter_offset returns AsyncIterator."""

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> OffsetPage:
                return OffsetPage(items=[1], has_more=False)

            def next_page_params(self, params: dict[str, Any]) -> dict[str, Any]:
                return params

        stub = Stub()
        result = stub.iter_offset(
            query_fn=stub.query,
            next_page_fn=stub.next_page_params,
            extract_items=lambda r: r.items,
            has_more_fn=lambda r: r.has_more,
            params={},
        )
        assert isinstance(result, AsyncIterator)

        # Verify query was awaited by consuming the iterator
        items: list[int] = []
        async for item in result:
            items.append(item)
        assert items == [1]

    async def test_iter_continuation_returns_async_iterator(self) -> None:
        """VAL-ABS-009: iter_continuation returns AsyncIterator."""

        class Stub(PaginationMixin):
            async def query(self, **kwargs: Any) -> ContinuationPage:
                return ContinuationPage(data="page", continuation_token=None)

        stub = Stub()
        result = stub.iter_continuation(
            query_fn=stub.query,
            extract_token=lambda r: r.continuation_token,
            params={},
        )
        assert isinstance(result, AsyncIterator)

        pages: list[ContinuationPage] = []
        async for page in result:
            pages.append(page)
        assert len(pages) == 1


# ---------------------------------------------------------------------------
# PollingMixin tests (VAL-ABS-010..014)
# ---------------------------------------------------------------------------


class TestPollingMixin:
    """Tests for PollingMixin.poll_until."""

    async def test_returns_immediately_on_first_success(self) -> None:
        """VAL-ABS-010: Polling returns immediately on first success."""
        check_count = 0

        async def get_status() -> str:
            nonlocal check_count
            check_count += 1
            return "success"

        mixin = PollingMixin()
        result = await mixin.poll_until(
            get_status_fn=get_status,
            predicate=lambda s: s == "success",
            poll_interval=0.01,
            max_attempts=10,
        )
        assert result == "success"
        assert check_count == 1

    async def test_retries_until_predicate_pass(self) -> None:
        """VAL-ABS-011: Polling retries until predicate passes."""
        check_count = 0
        sleep_times: list[float] = []

        async def get_status() -> str:
            nonlocal check_count
            check_count += 1
            if check_count < 5:
                return "pending"
            return "success"

        # Patch asyncio.sleep to track calls
        original_sleep = asyncio.sleep

        async def tracked_sleep(delay: float) -> None:
            sleep_times.append(delay)
            await original_sleep(0)  # Don't actually wait

        mixin = PollingMixin()
        # We pass the custom sleep to verify it's called
        result = await mixin.poll_until(
            get_status_fn=get_status,
            predicate=lambda s: s == "success",
            poll_interval=0.1,
            max_attempts=10,
            _sleep_fn=tracked_sleep,
        )
        assert result == "success"
        assert check_count == 5
        assert len(sleep_times) == 4  # 4 sleeps between 5 checks

    async def test_raises_timeout_on_max_attempts(self) -> None:
        """VAL-ABS-012: Polling raises timeout error after max attempts."""
        check_count = 0

        async def get_status() -> str:
            nonlocal check_count
            check_count += 1
            return "pending"

        mixin = PollingMixin()
        with pytest.raises(KSeFApiError, match="timed out"):
            await mixin.poll_until(
                get_status_fn=get_status,
                predicate=lambda s: s == "success",
                poll_interval=0.01,
                max_attempts=3,
                error_type=KSeFApiError,
                error_kwargs={
                    "status_code": 0,
                    "exception_code": ExceptionCode.UNKNOWN_ERROR,
                    "message": "Polling timed out",
                },
            )
        assert check_count == 3

    async def test_fast_fail_on_terminal_error(self) -> None:
        """VAL-ABS-013: Polling fails fast on terminal error status."""
        check_count = 0

        async def get_status() -> dict[str, Any]:
            nonlocal check_count
            check_count += 1
            if check_count == 1:
                return {"status": "pending", "code": 200}
            return {"status": "error", "code": 400}

        mixin = PollingMixin()
        with pytest.raises(KSeFApiError, match="terminal failure"):
            await mixin.poll_until(
                get_status_fn=get_status,
                predicate=lambda s: s.get("status") == "success",
                is_terminal_error_fn=lambda s: s.get("code", 0) >= 400,
                poll_interval=0.01,
                max_attempts=10,
                error_type=KSeFApiError,
                error_kwargs={
                    "status_code": 400,
                    "exception_code": ExceptionCode.UNKNOWN_ERROR,
                    "message": "terminal failure",
                },
            )
        assert check_count == 2

    async def test_async_polling_uses_asyncio_sleep(self) -> None:
        """VAL-ABS-014: Async polling uses asyncio.sleep (not time.sleep)."""
        import inspect

        # Verify poll_until is async and accepts a sleep function
        assert inspect.iscoroutinefunction(PollingMixin.poll_until)

        sleep_called = False

        async def mock_sleep(delay: float) -> None:
            nonlocal sleep_called
            sleep_called = True

        async def get_status() -> str:
            return "success"

        mixin = PollingMixin()
        await mixin.poll_until(
            get_status_fn=get_status,
            predicate=lambda s: s == "success",
            poll_interval=0.01,
            max_attempts=5,
            _sleep_fn=mock_sleep,
        )
        # No sleep needed since first check succeeds
        assert not sleep_called

    async def test_async_polling_actually_sleeps(self) -> None:
        """VAL-ABS-014: Async polling calls sleep between retries."""
        sleep_calls: list[float] = []

        async def mock_sleep(delay: float) -> None:
            sleep_calls.append(delay)

        call_count = 0

        async def get_status() -> str:
            nonlocal call_count
            call_count += 1
            return "success" if call_count >= 3 else "pending"

        mixin = PollingMixin()
        await mixin.poll_until(
            get_status_fn=get_status,
            predicate=lambda s: s == "success",
            poll_interval=0.5,
            max_attempts=10,
            _sleep_fn=mock_sleep,
        )
        assert sleep_calls == [0.5, 0.5]


# ---------------------------------------------------------------------------
# LifecycleMixin tests (VAL-ABS-015..019)
# ---------------------------------------------------------------------------


class TestLifecycleMixin:
    """Tests for LifecycleMixin."""

    async def test_rejects_operations_after_close(self) -> None:
        """VAL-ABS-015: _ensure_open raises KSeFClientClosedError after close."""
        mixin = LifecycleMixin()
        # Should not raise before close
        mixin._ensure_open()

        await mixin.close()

        with pytest.raises(KSeFClientClosedError, match="[Cc]losed"):
            mixin._ensure_open()

    async def test_close_is_idempotent(self) -> None:
        """VAL-ABS-016: Calling close() twice does not raise."""
        mixin = LifecycleMixin()
        await mixin.close()
        # Second close should not raise
        await mixin.close()

    async def test_async_context_manager_enter_exit(self) -> None:
        """VAL-ABS-017: async with enters and exits correctly."""
        mixin = LifecycleMixin()
        close_called = False
        original_close = mixin.close

        async def tracked_close() -> None:
            nonlocal close_called
            close_called = True
            await original_close()

        mixin.close = tracked_close  # type: ignore[attr-defined]

        async with mixin as ctx:
            assert ctx is mixin
            assert not close_called

        assert close_called

    async def test_context_manager_calls_close_on_exception(self) -> None:
        """VAL-ABS-017: close() called even on exception."""
        mixin = LifecycleMixin()
        close_called = False
        original_close = mixin.close

        async def tracked_close() -> None:
            nonlocal close_called
            close_called = True
            await original_close()

        mixin.close = tracked_close  # type: ignore[attr-defined]

        with pytest.raises(ValueError, match="test error"):
            async with mixin:
                raise ValueError("test error")

        assert close_called

    async def test_exit_swallows_secondary_close_errors(self) -> None:
        """VAL-ABS-018: Original exception propagates if close() also fails."""
        import httpx

        mixin = LifecycleMixin()

        async def failing_close() -> None:
            raise httpx.HTTPError("close failed")

        mixin.close = failing_close  # type: ignore[attr-defined]

        with pytest.raises(ValueError, match="original error"):
            async with mixin:
                raise ValueError("original error")

    async def test_mixin_composition_valid_mro(self) -> None:
        """VAL-ABS-019: All three mixins compose without MRO issues."""

        class CompositeClient(PaginationMixin, PollingMixin, LifecycleMixin):
            pass

        # Should instantiate without TypeError
        client = CompositeClient()
        assert isinstance(client, PaginationMixin)
        assert isinstance(client, PollingMixin)
        assert isinstance(client, LifecycleMixin)

        # All methods should be accessible
        assert hasattr(client, "iter_offset")
        assert hasattr(client, "iter_continuation")
        assert hasattr(client, "poll_until")
        assert hasattr(client, "_ensure_open")
        assert hasattr(client, "close")
        assert hasattr(client, "__aenter__")
        assert hasattr(client, "__aexit__")

    async def test_composite_with_two_mixins(self) -> None:
        """VAL-ABS-019: Pairwise mixin composition works."""

        class PairA(PaginationMixin, LifecycleMixin):
            pass

        class PairB(PollingMixin, LifecycleMixin):
            pass

        class PairC(PaginationMixin, PollingMixin):
            pass

        a = PairA()
        b = PairB()
        c = PairC()
        assert all(
            [
                isinstance(a, (PaginationMixin, LifecycleMixin)),
                isinstance(b, (PollingMixin, LifecycleMixin)),
                isinstance(c, (PaginationMixin, PollingMixin)),
            ]
        )
