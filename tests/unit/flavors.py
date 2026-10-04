"""Run one test body against the sync and the async client flavour."""

import asyncio
import inspect
from collections.abc import Iterable
from typing import Any

from ksef2._clients.async_authenticated import AsyncAuthenticatedClient
from ksef2._clients.async_batch import AsyncBatchSessionClient
from ksef2._clients.async_online import AsyncOnlineSessionClient
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._clients.batch import BatchSessionClient
from ksef2._clients.online import OnlineSessionClient
from ksef2._core.stores import CertificateStore
from ksef2._domain.models.auth import AuthTokens
from ksef2._domain.models.batch import BatchSessionResumeState, PreparedBatch
from ksef2._domain.models.session import OnlineSessionResumeState
from ksef2._services.async_batch import AsyncBatchService
from ksef2._services.async_invoices import AsyncInvoicesService
from ksef2._services.batch import BatchService
from ksef2._services.invoices import InvoicesService
from tests.unit.fakes.transport import AsyncFakeTransport, FakeTransport


async def _await(value: Any) -> Any:
    return await value


async def _collect(iterable: Any) -> list[Any]:
    return [item async for item in iterable]


class Flavor:
    """Builds sync or async clients over one fake transport and drives them."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.is_async = name == "async"
        self.transport: FakeTransport | AsyncFakeTransport = (
            AsyncFakeTransport() if self.is_async else FakeTransport()
        )

    def run(self, value: Any) -> Any:
        """Await ``value`` for the async flavour; pass it through for sync."""
        if inspect.isawaitable(value):
            return asyncio.run(_await(value))
        return value

    def collect(self, iterable: Iterable[Any] | Any) -> list[Any]:
        """Drain a sync or async iterable into a list."""
        if self.is_async:
            return asyncio.run(_collect(iterable))
        return list(iterable)

    def close(self, session: Any) -> None:
        """Close a session client."""
        self.run(session.aclose() if self.is_async else session.close())

    def online_session(
        self, state: OnlineSessionResumeState, *, resumed: bool = False
    ) -> Any:
        cls = AsyncOnlineSessionClient if self.is_async else OnlineSessionClient
        return cls(self.transport, state, resumed=resumed)  # pyright: ignore[reportArgumentType]

    def batch_session(
        self,
        state: BatchSessionResumeState,
        *,
        resumed: bool = False,
        prepared_batch: PreparedBatch | None = None,
    ) -> Any:
        cls = AsyncBatchSessionClient if self.is_async else BatchSessionClient
        return cls(
            self.transport,  # pyright: ignore[reportArgumentType]
            state,
            prepared_batch=prepared_batch,
            resumed=resumed,
        )

    def authenticated(self, tokens: AuthTokens) -> Any:
        cls = AsyncAuthenticatedClient if self.is_async else AuthenticatedClient
        return cls(
            transport=self.transport,  # pyright: ignore[reportArgumentType]
            auth_tokens=tokens,
            certificate_store=CertificateStore(),
        )

    def invoices_service(self) -> Any:
        if self.is_async:
            return AsyncInvoicesService(
                self.transport,  # pyright: ignore[reportArgumentType]
                self.transport,  # pyright: ignore[reportArgumentType]
                CertificateStore(),
            )
        return InvoicesService(
            self.transport,  # pyright: ignore[reportArgumentType]
            self.transport,  # pyright: ignore[reportArgumentType]
            CertificateStore(),
        )

    def batch_service(self, *, get_encryption_key: Any, open_batch_session: Any) -> Any:
        cls = AsyncBatchService if self.is_async else BatchService
        return cls(
            authed_transport=self.transport,  # pyright: ignore[reportArgumentType]
            upload_transport=self.transport,  # pyright: ignore[reportArgumentType]
            get_encryption_key=get_encryption_key,
            open_batch_session=open_batch_session,
        )
