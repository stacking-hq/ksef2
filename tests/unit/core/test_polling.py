import asyncio

import pytest

from ksef2._core.exceptions import (
    ExceptionCode,
    KSeFRateLimitError,
    KSeFServerError,
    KSeFTransportError,
)
from ksef2._core.polling import async_poll_until, poll_until


class PollTimeoutError(Exception):
    pass


class PollTerminalError(Exception):
    pass


def test_poll_until_returns_first_non_retry_result() -> None:
    values = iter([0, 0, 1])
    sleeps: list[float] = []

    result = poll_until(
        operation=lambda: next(values),
        retry_predicate=lambda value: value < 1,
        poll_interval=0.25,
        max_attempts=3,
        timeout_error_factory=PollTimeoutError,
        sleep=sleeps.append,
    )

    assert result == 1
    assert sleeps == [0.25, 0.25]


def test_poll_until_converts_retry_exhaustion_to_timeout_error() -> None:
    with pytest.raises(PollTimeoutError):
        _ = poll_until(
            operation=lambda: 0,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=2,
            timeout_error_factory=PollTimeoutError,
            sleep=lambda _: None,
        )


@pytest.mark.parametrize("max_attempts", [0, -1])
def test_poll_until_times_out_without_attempt_for_non_positive_max_attempts(
    max_attempts: int,
) -> None:
    def _operation() -> int:
        raise AssertionError("operation should not be called")

    with pytest.raises(PollTimeoutError):
        _ = poll_until(
            operation=_operation,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=max_attempts,
            timeout_error_factory=PollTimeoutError,
            sleep=lambda _: None,
        )


def test_poll_until_propagates_operation_exceptions() -> None:
    def _raise() -> int:
        raise PollTerminalError("terminal")

    with pytest.raises(PollTerminalError, match="terminal"):
        _ = poll_until(
            operation=_raise,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=2,
            timeout_error_factory=PollTimeoutError,
            sleep=lambda _: None,
        )


def test_poll_until_does_not_sleep_after_final_attempt() -> None:
    sleeps: list[float] = []

    with pytest.raises(PollTimeoutError):
        _ = poll_until(
            operation=lambda: 0,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=3,
            timeout_error_factory=PollTimeoutError,
            sleep=sleeps.append,
        )

    assert sleeps == [0.25, 0.25]


def test_async_poll_until_returns_first_non_retry_result() -> None:
    async def _run() -> tuple[int, list[float]]:
        values = iter([0, 0, 1])
        sleeps: list[float] = []

        async def _operation() -> int:
            return next(values)

        async def _sleep(delay: float) -> None:
            sleeps.append(delay)

        result = await async_poll_until(
            operation=_operation,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=3,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
        )
        return result, sleeps

    result, sleeps = asyncio.run(_run())

    assert result == 1
    assert sleeps == [0.25, 0.25]


def test_async_poll_until_converts_retry_exhaustion_to_timeout_error() -> None:
    async def _run() -> None:
        async def _operation() -> int:
            return 0

        async def _sleep(_: float) -> None:
            return None

        _ = await async_poll_until(
            operation=_operation,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=2,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
        )

    with pytest.raises(PollTimeoutError):
        asyncio.run(_run())


@pytest.mark.parametrize("max_attempts", [0, -1])
def test_async_poll_until_times_out_without_attempt_for_non_positive_max_attempts(
    max_attempts: int,
) -> None:
    async def _run() -> None:
        async def _operation() -> int:
            raise AssertionError("operation should not be called")

        async def _sleep(_: float) -> None:
            return None

        _ = await async_poll_until(
            operation=_operation,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=max_attempts,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
        )

    with pytest.raises(PollTimeoutError):
        asyncio.run(_run())


def test_async_poll_until_propagates_operation_exceptions() -> None:
    async def _run() -> None:
        async def _operation() -> int:
            raise PollTerminalError("terminal")

        async def _sleep(_: float) -> None:
            return None

        _ = await async_poll_until(
            operation=_operation,
            retry_predicate=lambda value: value < 1,
            poll_interval=0.25,
            max_attempts=2,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
        )

    with pytest.raises(PollTerminalError, match="terminal"):
        asyncio.run(_run())


def test_async_poll_until_does_not_sleep_after_final_attempt() -> None:
    async def _run() -> list[float]:
        sleeps: list[float] = []

        async def _operation() -> int:
            return 0

        async def _sleep(delay: float) -> None:
            sleeps.append(delay)

        with pytest.raises(PollTimeoutError):
            _ = await async_poll_until(
                operation=_operation,
                retry_predicate=lambda value: value < 1,
                poll_interval=0.25,
                max_attempts=3,
                timeout_error_factory=PollTimeoutError,
                sleep=_sleep,
            )
        return sleeps

    assert asyncio.run(_run()) == [0.25, 0.25]


def test_poll_until_retries_transient_errors_until_timeout_with_fake_clock() -> None:
    now = 0.0
    attempts = 0
    sleeps: list[float] = []

    def _sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    def _operation() -> int:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise KSeFServerError(503, ExceptionCode.UNKNOWN_ERROR, "busy")
        return 1

    assert (
        poll_until(
            operation=_operation,
            retry_predicate=lambda _: False,
            poll_interval=2.0,
            timeout_seconds=5.0,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
            clock=lambda: now,
        )
        == 1
    )
    assert attempts == 3
    assert sleeps == [2.0, 2.0]


def test_poll_until_caps_sleep_to_remaining_timeout_and_retries_transport_errors() -> (
    None
):
    now = 0.0
    sleeps: list[float] = []

    def _sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    with pytest.raises(PollTimeoutError):
        poll_until(
            operation=lambda: (_ for _ in ()).throw(
                KSeFTransportError("lost", method="GET", path="/status")
            ),
            retry_predicate=lambda _: False,
            poll_interval=10.0,
            timeout_seconds=3.0,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
            clock=lambda: now,
        )
    assert sleeps == [3.0]


def test_poll_until_uses_retry_after_for_rate_limit_errors() -> None:
    now = 0.0
    sleeps: list[float] = []

    def _sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    attempts = 0

    def _operation() -> int:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise KSeFRateLimitError(4, "slow down")
        return 1

    assert (
        poll_until(
            operation=_operation,
            retry_predicate=lambda _: False,
            poll_interval=1.0,
            timeout_seconds=5.0,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
            clock=lambda: now,
        )
        == 1
    )
    assert sleeps == [4.0]


def test_async_poll_until_retries_transient_errors_until_timeout_with_fake_clock() -> (
    None
):
    async def _run() -> tuple[int, list[float]]:
        now = 0.0
        attempts = 0
        sleeps: list[float] = []

        async def _sleep(delay: float) -> None:
            nonlocal now
            sleeps.append(delay)
            now += delay

        async def _operation() -> int:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise KSeFServerError(503, ExceptionCode.UNKNOWN_ERROR, "busy")
            return 1

        result = await async_poll_until(
            operation=_operation,
            retry_predicate=lambda _: False,
            poll_interval=2.0,
            timeout_seconds=5.0,
            timeout_error_factory=PollTimeoutError,
            sleep=_sleep,
            clock=lambda: now,
        )
        assert attempts == 3
        return result, sleeps

    assert asyncio.run(_run()) == (1, [2.0, 2.0])


def test_poll_until_propagates_over_ceiling_rate_limit_without_sleeping() -> None:
    error = KSeFRateLimitError(600, "slow down")
    error.context["retry_after_exceeds_ceiling"] = True
    sleeps: list[float] = []
    now = 0.0

    with pytest.raises(KSeFRateLimitError) as exc_info:
        poll_until(
            operation=lambda: (_ for _ in ()).throw(error),
            retry_predicate=lambda _: False,
            poll_interval=1.0,
            timeout_seconds=30.0,
            timeout_error_factory=PollTimeoutError,
            sleep=sleeps.append,
            clock=lambda: now,
        )

    assert exc_info.value is error
    assert sleeps == []


def test_async_poll_until_propagates_over_ceiling_rate_limit_without_sleeping() -> None:
    async def _run() -> tuple[KSeFRateLimitError, list[float]]:
        error = KSeFRateLimitError(600, "slow down")
        error.context["retry_after_exceeds_ceiling"] = True
        sleeps: list[float] = []
        now = 0.0

        async def _operation() -> int:
            raise error

        async def _sleep(delay: float) -> None:
            sleeps.append(delay)

        with pytest.raises(KSeFRateLimitError) as exc_info:
            await async_poll_until(
                operation=_operation,
                retry_predicate=lambda _: False,
                poll_interval=1.0,
                timeout_seconds=30.0,
                timeout_error_factory=PollTimeoutError,
                sleep=_sleep,
                clock=lambda: now,
            )

        return exc_info.value, sleeps

    error, sleeps = asyncio.run(_run())
    assert error.context["retry_after_exceeds_ceiling"] is True
    assert sleeps == []
