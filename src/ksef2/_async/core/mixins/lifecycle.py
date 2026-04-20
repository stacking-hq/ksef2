"""LifecycleMixin — async lifecycle management for client objects.

Provides:
- ``_ensure_open()`` — raises ``KSeFClientClosedError`` if closed.
- ``close()`` — idempotent async cleanup.
- Async context manager: ``__aenter__``/``__aexit__``.
"""

import logging
from types import TracebackType
from typing import Self

from ksef2.core.exceptions import KSeFClientClosedError

logger = logging.getLogger(__name__)


class LifecycleMixin:
    """Mixin providing lifecycle management: open/close guard and async context manager.

    Subclasses must set ``_closed = False`` in ``__init__`` or rely on the
    default.  They should override ``close()`` to add custom cleanup, calling
    ``super().close()`` or setting ``self._closed = True`` themselves.
    """

    _closed: bool = False

    def _ensure_open(self) -> None:
        """Raise ``KSeFClientClosedError`` if the client has been closed."""
        if self._closed:
            raise KSeFClientClosedError("Client is closed.")

    async def close(self) -> None:
        """Mark the client as closed.  Idempotent — safe to call multiple times.

        Subclasses should override to perform resource cleanup and call
        ``self._closed = True`` (or ``super().close()``).
        """
        if self._closed:
            return
        self._closed = True

    async def __aenter__(self) -> Self:
        """Enter the async context manager, ensuring the client is open."""
        self._ensure_open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context manager, calling ``close()`` with best-effort cleanup.

        If ``close()`` raises and there is already an exception propagating,
        the close error is logged and suppressed so the original exception
        propagates.
        """
        try:
            await self.close()
        except Exception:
            if exc_type is None:
                # No original exception — let the close error propagate
                raise
            # Original exception takes priority; log the close error
            logger.warning(
                "Error during context manager close",
                exc_info=True,
            )
