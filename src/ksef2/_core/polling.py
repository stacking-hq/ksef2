"""Shared sync and async polling helpers built on monotonic time."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from ksef2._core.exceptions import (
    KSeFRateLimitError,
    KSeFServerError,
    KSeFTransportError,
)

# Unused here since the helpers declare their own ``[T]``; kept because 0.x
# releases exposed it as ``ksef2.core.polling.T``.
T = TypeVar("T")

_RETRYABLE_POLL_ERRORS = (KSeFRateLimitError, KSeFServerError, KSeFTransportError)


def _error_delay(error: Exception, poll_interval: float) -> float:
    if isinstance(error, KSeFRateLimitError):
        if error.context.get("retry_after_exceeds_ceiling") is True:
            raise error
        retry_after = error.retry_after
    else:
        retry_after = None
    return float(retry_after) if retry_after is not None else poll_interval


def poll_until[T](
    *,
    operation: Callable[[], T],
    retry_predicate: Callable[[T], bool],
    poll_interval: float,
    timeout_seconds: float | None = None,
    max_attempts: int | None = None,
    timeout_error_factory: Callable[[], BaseException],
    sleep: Callable[[float], None] | None = None,
    clock: Callable[[], float] | None = None,
) -> T:
    """Call *operation* until complete, or until its attempt/time budget expires.

    Retryable server, rate-limit, and transport errors are treated like pending
    results. They consume the same timeout budget and do not consume
    ``max_attempts`` when a timeout is configured.
    """
    if (timeout_seconds is None) == (max_attempts is None):
        raise ValueError(
            "Exactly one of timeout_seconds or max_attempts must be provided."
        )
    if max_attempts is not None and max_attempts < 1:
        raise timeout_error_factory()

    effective_sleep = time.sleep if sleep is None else sleep
    effective_clock = time.monotonic if clock is None else clock
    started = effective_clock()
    attempts = 0

    while True:
        if (
            attempts
            and timeout_seconds is not None
            and effective_clock() - started >= timeout_seconds
        ):
            raise timeout_error_factory()
        if max_attempts is not None and attempts >= max_attempts:
            raise timeout_error_factory()
        attempts += 1

        try:
            result = operation()
        except _RETRYABLE_POLL_ERRORS as error:
            delay = _error_delay(error, poll_interval)
        else:
            if not retry_predicate(result):
                return result
            delay = poll_interval

        if timeout_seconds is not None:
            remaining = timeout_seconds - (effective_clock() - started)
            if remaining <= 0:
                raise timeout_error_factory()
            delay = min(delay, remaining)
        if max_attempts is not None and attempts >= max_attempts:
            raise timeout_error_factory()
        effective_sleep(delay)


async def async_poll_until[T](
    *,
    operation: Callable[[], Awaitable[T]],
    retry_predicate: Callable[[T], bool],
    poll_interval: float,
    timeout_seconds: float | None = None,
    max_attempts: int | None = None,
    timeout_error_factory: Callable[[], BaseException],
    sleep: Callable[[float], Awaitable[None]] | None = None,
    clock: Callable[[], float] | None = None,
) -> T:
    """Async variant of :func:`poll_until`, with the same timeout accounting."""
    if (timeout_seconds is None) == (max_attempts is None):
        raise ValueError(
            "Exactly one of timeout_seconds or max_attempts must be provided."
        )
    if max_attempts is not None and max_attempts < 1:
        raise timeout_error_factory()

    effective_sleep = asyncio.sleep if sleep is None else sleep
    effective_clock = time.monotonic if clock is None else clock
    started = effective_clock()
    attempts = 0

    while True:
        if (
            attempts
            and timeout_seconds is not None
            and effective_clock() - started >= timeout_seconds
        ):
            raise timeout_error_factory()
        if max_attempts is not None and attempts >= max_attempts:
            raise timeout_error_factory()
        attempts += 1

        try:
            result = await operation()
        except _RETRYABLE_POLL_ERRORS as error:
            delay = _error_delay(error, poll_interval)
        else:
            if not retry_predicate(result):
                return result
            delay = poll_interval

        if timeout_seconds is not None:
            remaining = timeout_seconds - (effective_clock() - started)
            if remaining <= 0:
                raise timeout_error_factory()
            delay = min(delay, remaining)
        if max_attempts is not None and attempts >= max_attempts:
            raise timeout_error_factory()
        await effective_sleep(delay)
