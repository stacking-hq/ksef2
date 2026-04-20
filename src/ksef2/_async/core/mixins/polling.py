"""PollingMixin — generic async polling with configurable predicate and timeout.

Supports:
- Immediate return on first success.
- Retry with configurable interval until predicate passes.
- Timeout with domain-specific error after max attempts.
- Fast-fail on terminal error status.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from ksef2.core.exceptions import ExceptionCode, KSeFApiError

TStatus = TypeVar("TStatus")


class PollingMixin:
    """Mixin providing a generic ``poll_until`` async method."""

    async def poll_until(
        self,
        *,
        get_status_fn: Callable[..., Awaitable[TStatus]],
        predicate: Callable[[TStatus], bool],
        poll_interval: float = 1.0,
        max_attempts: int = 60,
        is_terminal_error_fn: Callable[[TStatus], bool] | None = None,
        error_type: type = KSeFApiError,
        error_kwargs: dict[str, object] | None = None,
        _sleep_fn: Callable[[float], Awaitable[None]] | None = None,
    ) -> TStatus:
        """Poll until a predicate passes or a timeout/error occurs.

        Args:
            get_status_fn: Async callable returning the current status.
            predicate: Sync callable that returns True when polling should stop.
            poll_interval: Seconds to sleep between attempts.
            max_attempts: Maximum number of status checks before raising.
            is_terminal_error_fn: Optional sync callable that returns True if the
                status represents a terminal failure (fast-fail).
            error_type: Exception class to raise on timeout or terminal failure.
            error_kwargs: Keyword arguments passed to ``error_type`` constructor.
            _sleep_fn: Override sleep function (for testing).

        Returns:
            The status value that passed the predicate.

        Raises:
            error_type: If max attempts exhausted or terminal error detected.
        """
        sleep_fn = _sleep_fn or asyncio.sleep

        for attempt in range(max_attempts):
            status = await get_status_fn()

            if predicate(status):
                return status

            if is_terminal_error_fn is not None and is_terminal_error_fn(status):
                kwargs = error_kwargs or {
                    "status_code": 0,
                    "exception_code": ExceptionCode.UNKNOWN_ERROR,
                    "message": f"Terminal error detected during polling at attempt {attempt + 1}",
                }
                raise error_type(**kwargs)

            # Don't sleep after the last attempt
            if attempt < max_attempts - 1:
                _ = await sleep_fn(poll_interval)

        kwargs = error_kwargs or {
            "status_code": 0,
            "exception_code": ExceptionCode.UNKNOWN_ERROR,
            "message": f"Polling timed out after {max_attempts} attempts",
        }
        raise error_type(**kwargs)
