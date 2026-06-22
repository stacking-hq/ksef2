"""Async root client for authenticated and unauthenticated SDK entry points."""

from functools import cached_property
from types import TracebackType
from typing import Self, final

import httpx

from ksef2.clients.async_auth import AsyncAuthClient
from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_encryption import AsyncEncryptionClient
from ksef2.clients.async_peppol import AsyncPeppolClient
from ksef2.clients.async_testdata import AsyncTestDataClient
from ksef2.config import Environment, TransportConfig
from ksef2.core import exceptions, stores
from ksef2.core.http_config import build_http_client_kwargs
from ksef2.core.async_http import AsyncHttpTransport
from ksef2.core.middlewares.async_exceptions import AsyncKSeFExceptionMiddleware
from ksef2.core.middlewares.async_lifecycle import (
    AsyncClientLifecycleMiddleware,
    AsyncClientLifecycleState,
)
from ksef2.core.middlewares.async_retry import AsyncRetryMiddleware
from ksef2.domain.models.auth import AuthTokens
from ksef2.raw.async_facade import AsyncRawClient


@final
class AsyncClient:
    """Root async KSeF SDK client responsible for transport and lifecycle management.

    Branch properties only create child clients. Branch operations document
    their own API, validation, and transport failures.

    Raises:
        KSeFClientClosedError: If a branch is accessed after the client is closed.
        KSeFUnsupportedEnvironmentError: If a TEST-only branch is accessed outside
            ``Environment.TEST``.
    """

    def __init__(
        self,
        environment: Environment = Environment.PRODUCTION,
        *,
        transport_config: TransportConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._environment = environment
        self._transport_config = transport_config or TransportConfig()
        self._http_client = http_client or self._build_http_client(
            environment=environment,
            config=self._transport_config,
        )
        self._owns_http_client = http_client is None
        self._lifecycle_state = AsyncClientLifecycleState()
        self._http_transport = AsyncHttpTransport(
            client=self._http_client,
            headers={},
            _owns_client=self._owns_http_client,
        )
        self._transport = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                AsyncClientLifecycleMiddleware(
                    self._http_transport,
                    self._lifecycle_state,
                ),
                self._transport_config.retry,
            )
        )
        self._certificate_store = stores.CertificateStore()

    @staticmethod
    def _build_http_client(
        *,
        environment: Environment,
        config: TransportConfig,
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            **build_http_client_kwargs(environment=environment, config=config)
        )

    def _ensure_open(self) -> None:
        if self._lifecycle_state.closed:
            raise exceptions.KSeFClientClosedError("Client is closed.")

    @cached_property
    def authentication(self) -> AsyncAuthClient:
        """Return the authentication entry point.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AsyncAuthClient(
            transport=self._transport,
            certificate_store=self._certificate_store,
            environment=self._environment,
        )

    @cached_property
    def encryption(self) -> AsyncEncryptionClient:
        """Return the public encryption-certificate client.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AsyncEncryptionClient(self._transport)

    @cached_property
    def peppol(self) -> AsyncPeppolClient:
        """Return the public Peppol provider client.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AsyncPeppolClient(self._transport)

    @cached_property
    def testdata(self) -> AsyncTestDataClient:
        """Return the TEST-only data seeding client.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
            KSeFUnsupportedEnvironmentError: If the client environment is not TEST.
        """
        self._ensure_open()
        if self._environment is not Environment.TEST:
            raise exceptions.KSeFUnsupportedEnvironmentError(
                "testdata is only available for Environment.TEST"
            )
        return AsyncTestDataClient(self._transport)

    @cached_property
    def raw(self) -> AsyncRawClient:
        """Return raw unauthenticated endpoints for advanced async integrations."""
        self._ensure_open()
        return AsyncRawClient(self._transport, self._environment)

    def authenticated(self, auth_tokens: AuthTokens) -> AsyncAuthenticatedClient:
        """Bind caller-supplied auth tokens to an authenticated async SDK client."""
        self._ensure_open()
        return AsyncAuthenticatedClient(
            transport=self._transport,
            auth_tokens=auth_tokens,
            certificate_store=self._certificate_store,
            environment=self._environment,
        )

    async def aclose(self) -> None:
        """Close owned resources and invalidate cached child clients."""
        if self._lifecycle_state.closed:
            return

        self._lifecycle_state.closed = True

        for name in ("authentication", "encryption", "peppol", "testdata", "raw"):
            self.__dict__.pop(name, None)

        await self._http_transport.aclose()

    async def __aenter__(self) -> Self:
        self._ensure_open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()
