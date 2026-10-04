"""Base class for client-side handles to asynchronous KSeF operations."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ksef2._core.polling import async_poll_until

_TStatus = TypeVar("_TStatus")
_TResult = TypeVar("_TResult")


class AsyncOperationHandle(ABC, Generic[_TStatus, _TResult]):
    """Client-side handle to an operation that KSeF finishes asynchronously.

    A handle keeps a reference to the client that started the operation and the
    operation's reference number. It is not a data model: it cannot be
    serialized, and the plain response models stay separate. Subclasses say how
    to read the operation's status, when it is still pending and how to turn the
    finished status into the result returned by ``wait()``.

    Catch ``KSeFException`` for SDK-classified failures raised while waiting, and
    ``httpx.HTTPError`` for transport failures.
    """

    def __init__(self, reference_number: str) -> None:
        """Create the handle.

        Args:
            reference_number: KSeF reference number of the operation.
        """
        self._reference_number = reference_number

    @property
    def reference_number(self) -> str:
        """Get the KSeF reference number of the operation.

        Returns:
            The reference number KSeF assigned to the operation.
        """
        return self._reference_number

    @abstractmethod
    async def get_status(self) -> _TStatus:
        """Fetch the current status of the operation without waiting.

        Returns:
            The status as KSeF reports it right now.
        """

    @abstractmethod
    def _is_pending(self, status: _TStatus) -> bool:
        """Return whether KSeF is still working on the operation."""

    @abstractmethod
    def _timeout_error(self, timeout: float) -> BaseException:
        """Build the exception raised when polling exceeds ``timeout``."""

    def _check_status(self, status: _TStatus) -> None:
        """Raise when ``status`` is a terminal failure; the default accepts all."""
        del status

    @abstractmethod
    async def _finish(self, status: _TStatus) -> _TResult:
        """Turn the final status into the result of ``wait()``."""

    async def _poll(self) -> _TStatus:
        status = await self.get_status()
        self._check_status(status)
        return status

    async def _wait(self, timeout: float, poll_interval: float) -> _TResult:
        status = await async_poll_until(
            operation=self._poll,
            retry_predicate=self._is_pending,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: self._timeout_error(timeout),
        )
        return await self._finish(status)
