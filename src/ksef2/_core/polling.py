"""Shared sync and async polling helpers built on tenacity.

These helpers centralise the retry/timeout logic that was previously
duplicated across auth, token, invoice, and batch call-sites. Tenacity
types are intentionally kept internal: callers only supply plain
callables, predicates, and exception factories.
"""

from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import (
    AsyncRetrying,
    Retrying,
    RetryError as _RetryError,
    retry_if_result,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
)
from tenacity.stop import stop_base

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Sync helper
# ---------------------------------------------------------------------------


def poll_until(
    *,
    operation: Callable[[], T],
    retry_predicate: Callable[[T], bool],
    poll_interval: float,
    timeout_seconds: float | None = None,
    max_attempts: int | None = None,
    timeout_error_factory: Callable[[], BaseException],
    sleep: Callable[[float], None] | None = None,
) -> T:
    """Call *operation* repeatedly until it produces a non-retry result.

    Parameters
    ----------
    operation:
        Synchronous callable that performs one poll attempt.
    retry_predicate:
        When it returns ``True`` the result is considered incomplete and the
        poller will retry after *poll_interval* seconds.
    poll_interval:
        Seconds to wait between attempts.
    timeout_seconds:
        If given, polling stops after this many **seconds** have elapsed.
    max_attempts:
        If given, polling stops after this many **attempts** (inclusive of
        the first call). Values below ``1`` exhaust before calling *operation*.
        Exactly one of *timeout_seconds* and *max_attempts* must be provided.
    timeout_error_factory:
        Called (with no arguments) to produce the exception raised when
        polling is exhausted.

    Returns
    -------
    The first result for which *retry_predicate* returns ``False``.

    Raises
    ------
    The exception produced by *timeout_error_factory* when retries are
    exhausted.  SDK/domain exceptions raised by *operation* propagate
    unchanged.
    """
    stop = _build_stop(timeout_seconds, max_attempts)
    if max_attempts is not None and max_attempts < 1:
        raise timeout_error_factory()

    if sleep is None:
        retryer = Retrying(
            stop=stop,
            wait=wait_fixed(poll_interval),
            retry=retry_if_result(retry_predicate),
            reraise=True,
        )
    else:
        retryer = Retrying(
            stop=stop,
            wait=wait_fixed(poll_interval),
            retry=retry_if_result(retry_predicate),
            reraise=True,
            sleep=sleep,
        )
    try:
        return retryer(operation)
    except _RetryError as exc:
        raise timeout_error_factory() from exc


# ---------------------------------------------------------------------------
# Async helper
# ---------------------------------------------------------------------------


async def async_poll_until(
    *,
    operation: Callable[[], Awaitable[T]],
    retry_predicate: Callable[[T], bool],
    poll_interval: float,
    timeout_seconds: float | None = None,
    max_attempts: int | None = None,
    timeout_error_factory: Callable[[], BaseException],
    sleep: Callable[[float], Awaitable[None]] | None = None,
) -> T:
    """Async variant of :func:`poll_until`.

    Parameters are identical to :func:`poll_until` except that *operation*
    must return an awaitable.
    """
    stop = _build_stop(timeout_seconds, max_attempts)
    if max_attempts is not None and max_attempts < 1:
        raise timeout_error_factory()

    async def invoke_operation() -> T:
        return await operation()

    if sleep is None:
        retryer = AsyncRetrying(
            stop=stop,
            wait=wait_fixed(poll_interval),
            retry=retry_if_result(retry_predicate),
            reraise=True,
        )
    else:
        retryer = AsyncRetrying(
            stop=stop,
            wait=wait_fixed(poll_interval),
            retry=retry_if_result(retry_predicate),
            reraise=True,
            sleep=sleep,
        )
    try:
        return await retryer(invoke_operation)
    except _RetryError as exc:
        raise timeout_error_factory() from exc


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------


def _build_stop(
    timeout_seconds: float | None,
    max_attempts: int | None,
) -> stop_base:
    """Return the appropriate tenacity stop condition."""
    if timeout_seconds is not None and max_attempts is not None:
        raise ValueError("Only one of timeout_seconds or max_attempts may be provided.")
    if timeout_seconds is not None:
        return stop_after_delay(timeout_seconds)
    if max_attempts is not None:
        return stop_after_attempt(max_attempts)
    raise ValueError("Either timeout_seconds or max_attempts must be provided.")
