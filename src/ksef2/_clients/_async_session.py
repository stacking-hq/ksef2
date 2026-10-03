"""Awaitable async session wrapper used by session factories."""

from collections.abc import Coroutine, Generator
from types import TracebackType
from typing import Any, Generic, Protocol, Self, TypeVar, runtime_checkable


@runtime_checkable
class _AsyncSessionClient(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...


_TSession = TypeVar("_TSession", bound=_AsyncSessionClient)


class _AwaitableSession(Generic[_TSession]):
    def __init__(self, coro: Coroutine[Any, Any, _TSession]) -> None:
        self._coro = coro
        self._session: _TSession | None = None

    def __await__(self) -> Generator[Any, None, _TSession]:
        return self._coro.__await__()

    async def __aenter__(self) -> _TSession:
        session = await self._coro
        self._session = session
        return await session.__aenter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        await self._session.__aexit__(exc_type, exc_val, exc_tb)
