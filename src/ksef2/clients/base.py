"""Public root client for authenticated and unauthenticated SDK entry points."""

from functools import cached_property
from types import TracebackType
from typing import final, Self

import httpx

from ksef2.clients.auth import AuthClient
from ksef2.clients import encryption, peppol
from ksef2.clients.testdata import TestDataClient
from ksef2.config import Environment, TransportConfig
from ksef2.core import exceptions, middlewares, stores
from ksef2.core.http_config import build_http_client_kwargs
from ksef2.core.http import HttpTransport


@final
class Client:
    """Root KSeF SDK client responsible for transport and lifecycle management.

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
        http_client: httpx.Client | None = None,
    ) -> None:
        self._environment = environment
        self._transport_config = transport_config or TransportConfig()
        self._http_client = http_client or self._build_http_client(
            environment=environment,
            config=self._transport_config,
        )
        self._owns_http_client = http_client is None
        self._lifecycle_state = middlewares.ClientLifecycleState()
        self._transport = middlewares.KSeFExceptionMiddleware(
            middlewares.RetryMiddleware(
                middlewares.ClientLifecycleMiddleware(
                    HttpTransport(client=self._http_client, headers={}),
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

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return AuthClient(
            transport=self._transport,
            certificate_store=self._certificate_store,
            environment=self._environment,
        )

    @cached_property
    def encryption(self) -> encryption.EncryptionClient:
        """Return the public encryption-certificate client.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return encryption.EncryptionClient(self._transport)

    @cached_property
    def testdata(self) -> TestDataClient:
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
        return TestDataClient(self._transport)

    @cached_property
    def peppol(self) -> peppol.PeppolClient:
        """Return the public Peppol provider client.

        Raises:
            KSeFClientClosedError: If the root client has been closed.
        """
        self._ensure_open()
        return peppol.PeppolClient(self._transport)

    def close(self) -> None:
        """Close owned resources and invalidate cached child clients."""
        if self._lifecycle_state.closed:
            return

        self._lifecycle_state.closed = True

        for name in ("authentication", "encryption", "testdata", "peppol"):
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
