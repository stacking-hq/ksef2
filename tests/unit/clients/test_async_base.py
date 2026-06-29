import asyncio
from collections.abc import Iterable
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2.clients.async_auth import AsyncAuthClient
from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_base import AsyncClient
from ksef2.clients.async_encryption import AsyncEncryptionClient
from ksef2.clients.async_peppol import AsyncPeppolClient
from ksef2.clients.async_testdata import AsyncTestDataClient
from ksef2.config import Environment, TimeoutConfig, TransportConfig
from ksef2.core.exceptions import KSeFClientClosedError
from ksef2.core.exceptions import KSeFUnsupportedEnvironmentError
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models.encryption import (
    CertUsage,
    CertUsageEnum,
    PublicKeyCertificate,
)

HTTPX_ASYNC_CLIENT_CLASS = httpx.AsyncClient


class CustomCertificateStore:
    def __init__(self) -> None:
        self.certificates: list[PublicKeyCertificate] = []

    def load(self, certs: Iterable[PublicKeyCertificate]) -> None:
        self.certificates = list(certs)

    def get_valid(
        self,
        usage: CertUsage | CertUsageEnum | str,
    ) -> PublicKeyCertificate:
        raise AssertionError(f"Unexpected certificate lookup for {usage}.")

    def needs_refresh(
        self,
        usage: CertUsage | CertUsageEnum | str,
        *,
        at: datetime | None = None,
    ) -> bool:
        _ = usage
        _ = at
        return True


class TestAsyncClient:
    def test_accessors_return_expected_types(self) -> None:
        client = AsyncClient(environment=Environment.TEST)

        try:
            assert isinstance(client.authentication, AsyncAuthClient)
            assert isinstance(client.encryption, AsyncEncryptionClient)
            assert isinstance(client.peppol, AsyncPeppolClient)
            assert isinstance(client.testdata, AsyncTestDataClient)
        finally:
            asyncio.run(client.aclose())

    def test_testdata_accessor_rejects_production_environment(self) -> None:
        client = AsyncClient(environment=Environment.PRODUCTION)
        try:
            with pytest.raises(
                KSeFUnsupportedEnvironmentError,
                match="testdata is only available",
            ):
                _ = client.testdata
        finally:
            asyncio.run(client.aclose())

    @patch("ksef2.clients.async_base.httpx.AsyncClient")
    def test_aclose_closes_owned_http_client(
        self,
        client_cls: MagicMock,
    ) -> None:
        http_client = AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS)
        client_cls.return_value = http_client

        client = AsyncClient(environment=Environment.TEST)
        asyncio.run(client.aclose())

        http_client.aclose.assert_awaited_once()

    def test_aclose_does_not_close_user_supplied_http_client(self) -> None:
        http_client = AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS)

        client = AsyncClient(environment=Environment.TEST, http_client=http_client)
        asyncio.run(client.aclose())

        http_client.aclose.assert_not_awaited()

    @patch("ksef2.clients.async_base.httpx.AsyncClient")
    def test_async_context_manager_closes_owned_client(
        self,
        client_cls: MagicMock,
    ) -> None:
        http_client = AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS)
        client_cls.return_value = http_client

        async def _run() -> None:
            async with AsyncClient(environment=Environment.TEST):
                pass

        asyncio.run(_run())

        http_client.aclose.assert_awaited_once()

    @patch("ksef2.clients.async_base.httpx.AsyncClient")
    def test_transport_config_is_translated_to_httpx_client(
        self,
        client_cls: MagicMock,
    ) -> None:
        http_client = AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS)
        client_cls.return_value = http_client

        config = TransportConfig(
            timeouts=TimeoutConfig(connect=1.0, read=2.0, write=3.0, pool=4.0),
            proxy_url="http://proxy.local:8080",
        )

        client = AsyncClient(environment=Environment.TEST, transport_config=config)
        asyncio.run(client.aclose())

        _, kwargs = client_cls.call_args
        timeout = kwargs["timeout"]
        assert isinstance(timeout, httpx.Timeout)
        assert timeout.connect == 1.0
        assert timeout.read == 2.0
        assert timeout.write == 3.0
        assert timeout.pool == 4.0
        assert kwargs["proxy"] == "http://proxy.local:8080"
        assert kwargs["http2"] is True

    @patch("ksef2.clients.async_base.httpx.AsyncClient")
    def test_accessors_raise_after_close(
        self,
        client_cls: MagicMock,
    ) -> None:
        client_cls.return_value = AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS)
        client = AsyncClient(environment=Environment.TEST)
        asyncio.run(client.aclose())

        with pytest.raises(KSeFClientClosedError, match="Client is closed"):
            _ = client.authentication

    @patch("ksef2.clients.async_base.AsyncAuthClient")
    def test_authentication_accessor_uses_custom_certificate_store(
        self,
        auth_client_cls: MagicMock,
    ) -> None:
        store = CustomCertificateStore()
        client = AsyncClient(
            environment=Environment.TEST,
            http_client=AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS),
            certificate_store=store,
        )

        try:
            _ = client.authentication
        finally:
            asyncio.run(client.aclose())

        _, kwargs = auth_client_cls.call_args
        assert kwargs["certificate_store"] is store

    def test_authenticated_deprecated_wrapper_delegates_to_auth_branch(
        self,
        domain_auth_tokens: BaseFactory[AuthTokens],
    ) -> None:
        store = CustomCertificateStore()
        auth_tokens = domain_auth_tokens.build()
        client = AsyncClient(
            environment=Environment.TEST,
            http_client=AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS),
            certificate_store=store,
        )

        try:
            with pytest.deprecated_call(match="AsyncClient.authenticated"):
                authenticated = client.authenticated(auth_tokens)
        finally:
            asyncio.run(client.aclose())

        assert isinstance(authenticated, AsyncAuthenticatedClient)
        assert authenticated.resume_state().to_tokens() == auth_tokens
