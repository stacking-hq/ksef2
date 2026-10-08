"""Public root client for authenticated and unauthenticated SDK entry points."""

from functools import cached_property
from types import TracebackType
from typing import final, Self

import httpx
from typing_extensions import deprecated

from ksef2._clients.auth import AuthClient
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._clients.encryption import EncryptionClient
from ksef2._clients.peppol import PeppolClient
from ksef2._clients.testdata import TestDataClient
from ksef2._config import Environment, TransportConfig
from ksef2._core import exceptions, middlewares, stores
from ksef2._core.http_config import build_http_client_kwargs
from ksef2._core.http import HttpTransport
from ksef2._domain.models.auth import AuthenticationResumeState, AuthTokens
from ksef2.raw._facade import RawClient


@final
class Client:
    """Root KSeF SDK client responsible for transport and lifecycle management.

    Branch properties only create child clients. Branch operations document
    their own API, validation, and transport failures.

    Raises:
        KSeFClientClosedError: If a branch is accessed after the client is closed.
        KSeFUnsupportedEnvironmentError: If a TEST-only branch is accessed outside
            ``Environment.TEST``.

    Example:
        ```python
        from ksef2 import Client, Environment

        with Client(Environment.TEST) as client:
            auth = client.authentication.with_test_certificate(nip="5261040828")
            for invoice in auth.invoices.all_metadata(filters=filters):
                print(invoice.ksef_number)
        ```
    """

    def __init__(
        self,
        environment: Environment = Environment.PRODUCTION,
        *,
        transport_config: TransportConfig | None = None,
        http_client: httpx.Client | None = None,
        certificate_store: stores.CertificateStoreProtocol | None = None,
    ) -> None:
        """Create the client.

        Args:
            environment: KSeF environment to talk to. Defaults to production.
            transport_config: HTTP transport settings (timeouts, retries, TLS, connection pool). Defaults are used when omitted.
            http_client: Existing ``httpx.Client`` to use instead of building one. The caller then owns it and must close it.
            certificate_store: Store for KSeF public-key certificates; an in-memory store is created when omitted.
        """
        self._environment = environment
        self._transport_config = transport_config or TransportConfig()
        self._http_client = http_client or self._build_http_client(
            environment=environment,
            config=self._transport_config,
        )
        self._owns_http_client = http_client is None
        self._lifecycle_state = middlewares.ClientLifecycleState()
        lifecycle_transport = middlewares.ClientLifecycleMiddleware(
            HttpTransport(client=self._http_client, headers={}),
            self._lifecycle_state,
        )
        self._transfer_transport = lifecycle_transport
        self._transport = middlewares.KSeFExceptionMiddleware(
            middlewares.RetryMiddleware(
                middlewares.ErrorFormatMiddleware(
                    lifecycle_transport, self._transport_config.error_format
                ),
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
    ) -> httpx.Client:
        """Create the underlying ``httpx.Client`` from transport configuration."""
        return httpx.Client(
            **build_http_client_kwargs(environment=environment, config=config)
        )

    def _ensure_open(self) -> None:
        """Reject operations once the client lifecycle has been closed."""
        if self._lifecycle_state.closed:
            raise exceptions.KSeFClientClosedError("Client is closed.")

    @cached_property
    def authentication(self) -> AuthClient:
        """Return the authentication entry point.

        Returns:
            The authentication branch, used to log in and obtain an authenticated client.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AuthClient(
            transport=self._transport,
            certificate_store=self._certificate_store,
            environment=self._environment,
            transfer_transport=self._transfer_transport,
            auto_refresh_tokens=self._transport_config.auto_refresh_tokens,
        )

    @cached_property
    def encryption(self) -> EncryptionClient:
        """Return the public encryption-certificate client.

        Returns:
            The client for downloading KSeF public-key certificates.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return EncryptionClient(self._transport)

    @cached_property
    def testdata(self) -> TestDataClient:
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
        return TestDataClient(self._transport)

    @cached_property
    def peppol(self) -> PeppolClient:
        """Return the public Peppol provider client.

        Returns:
            The client for listing registered Peppol providers.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return PeppolClient(self._transport)

    @cached_property
    def raw(self) -> RawClient:
        """Return raw unauthenticated endpoints for advanced integrations.

        Returns:
            Raw unauthenticated endpoints for advanced integrations.
        """
        self._ensure_open()
        return RawClient(self._transport, self._environment)

    @deprecated(
        "`Client.authenticated()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `Client.authentication.resume()` with "
        "`AuthenticationResumeState.from_tokens()` instead."
    )
    def authenticated(self, auth_tokens: AuthTokens) -> AuthenticatedClient:
        """Deprecated compatibility wrapper for ``authentication.resume()``.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``authentication.resume()`` with ``AuthenticationResumeState.from_tokens()`` instead.

        Args:
            auth_tokens: Access and refresh tokens from a previous authentication.

        Returns:
            An authenticated client bound to the tokens.
        """
        self._ensure_open()
        return self.authentication.resume(
            AuthenticationResumeState.from_tokens(auth_tokens)
        )

    def close(self) -> None:
        """Close owned resources and invalidate cached child clients."""
        if self._lifecycle_state.closed:
            return

        self._lifecycle_state.closed = True

        for name in ("authentication", "encryption", "testdata", "peppol", "raw"):
            self.__dict__.pop(name, None)

        if self._owns_http_client:
            self._http_client.close()

    def __enter__(self) -> Self:
        """Return the client for context-manager usage."""
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the client on context-manager exit."""
        self.close()
