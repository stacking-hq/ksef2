"""Async root client for authenticated and unauthenticated SDK entry points."""

from functools import cached_property
from types import TracebackType
from typing import Self, final

import httpx
from typing_extensions import deprecated

from ksef2._clients.async_auth import AsyncAuthClient
from ksef2._clients.async_authenticated import AsyncAuthenticatedClient
from ksef2._clients.async_encryption import AsyncEncryptionClient
from ksef2._clients.async_peppol import AsyncPeppolClient
from ksef2._clients.async_testdata import AsyncTestDataClient
from ksef2._config import Environment, TransportConfig
from ksef2._core import exceptions, stores
from ksef2._core.http_config import build_http_client_kwargs
from ksef2._core.async_http import AsyncHttpTransport
from ksef2._core.middlewares.async_exceptions import AsyncKSeFExceptionMiddleware
from ksef2._core.middlewares.async_lifecycle import (
    AsyncClientLifecycleMiddleware,
    AsyncClientLifecycleState,
)
from ksef2._core.middlewares.async_retry import AsyncRetryMiddleware
from ksef2._domain.models.auth import AuthenticationResumeState, AuthTokens
from ksef2.raw._async_facade import AsyncRawClient


@final
class AsyncClient:
    """Root async KSeF SDK client responsible for transport and lifecycle management.

    Branch properties only create child clients. Branch operations document
    their own API, validation, and transport failures.

    Raises:
        KSeFClientClosedError: If a branch is accessed after the client is closed.
        KSeFUnsupportedEnvironmentError: If a TEST-only branch is accessed outside
            ``Environment.TEST``.

    Example:
        ```python
        from ksef2 import AsyncClient, Environment

        async with AsyncClient(Environment.TEST) as client:
            auth = await client.authentication.with_test_certificate(nip="5261040828")
            async for invoice in auth.invoices.all_metadata(filters=filters):
                print(invoice.ksef_number)
        ```
    """

    def __init__(
        self,
        environment: Environment = Environment.PRODUCTION,
        *,
        transport_config: TransportConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
        certificate_store: stores.CertificateStoreProtocol | None = None,
    ) -> None:
        """Create the client.

        Args:
            environment: KSeF environment to talk to. Defaults to production.
            transport_config: HTTP transport settings (timeouts, retries, TLS, connection pool). Defaults are used when omitted.
            http_client: Existing ``httpx.AsyncClient`` to use instead of building one. The caller then owns it and must close it.
            certificate_store: Store for KSeF public-key certificates; an in-memory store is created when omitted.
        """
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
        lifecycle_transport = AsyncClientLifecycleMiddleware(
            self._http_transport,
            self._lifecycle_state,
        )
        self._transfer_transport = lifecycle_transport
        self._transport = AsyncKSeFExceptionMiddleware(
            AsyncRetryMiddleware(
                lifecycle_transport,
                self._transport_config.retry,
            )
        )
        self._certificate_store = (
            certificate_store
            if certificate_store is not None
            else stores.CertificateStore()
        )

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

        Returns:
            The authentication branch, used to log in and obtain an authenticated client.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AsyncAuthClient(
            transport=self._transport,
            certificate_store=self._certificate_store,
            environment=self._environment,
            transfer_transport=self._transfer_transport,
        )

    @cached_property
    def encryption(self) -> AsyncEncryptionClient:
        """Return the public encryption-certificate client.

        Returns:
            The client for downloading KSeF public-key certificates.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AsyncEncryptionClient(self._transport)

    @cached_property
    def peppol(self) -> AsyncPeppolClient:
        """Return the public Peppol provider client.

        Returns:
            The client for listing registered Peppol providers.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AsyncPeppolClient(self._transport)

    @cached_property
    def testdata(self) -> AsyncTestDataClient:
        """Return the TEST-only data seeding client.

        Returns:
            The client for creating and removing TEST-environment data.

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
        """Return raw unauthenticated endpoints for advanced async integrations.

        Returns:
            Raw unauthenticated endpoints for advanced async integrations.
        """
        self._ensure_open()
        return AsyncRawClient(self._transport, self._environment)

    @deprecated(
        "`AsyncClient.authenticated()` is deprecated and will be removed in ksef2 2.0; "
        "use `AsyncClient.authentication.resume()` with "
        "`AuthenticationResumeState.from_tokens()` instead."
    )
    def authenticated(self, auth_tokens: AuthTokens) -> AsyncAuthenticatedClient:
        """Deprecated compatibility wrapper for ``authentication.resume()``.

        Deprecated:
            Will be removed in ksef2 2.0. Use ``authentication.resume()`` with ``AuthenticationResumeState.from_tokens()`` instead.

        Args:
            auth_tokens: Access and refresh tokens from a previous authentication.

        Returns:
            An authenticated client bound to the tokens.
        """
        self._ensure_open()
        return self.authentication.resume(
            AuthenticationResumeState.from_tokens(auth_tokens)
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
