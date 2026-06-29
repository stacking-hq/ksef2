from collections.abc import Iterable
from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.clients.base import Client
from ksef2.clients.testdata import TestDataClient as KSeFTestDataClient
from ksef2.config import Environment, TimeoutConfig, TransportConfig
from ksef2.core.exceptions import (
    KSeFClientClosedError,
    KSeFUnsupportedEnvironmentError,
)
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models.encryption import (
    CertUsage,
    CertUsageEnum,
    PublicKeyCertificate,
)

HTTPX_CLIENT_CLASS = httpx.Client


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


class TestClient:
    def test_testdata_accessor_uses_client(
        self,
    ) -> None:
        client = Client(environment=Environment.TEST)

        assert isinstance(client.testdata, KSeFTestDataClient)

    def test_testdata_accessor_rejects_production_environment(self) -> None:
        client = Client(environment=Environment.PRODUCTION)

        with pytest.raises(
            KSeFUnsupportedEnvironmentError,
            match="testdata is only available",
        ):
            _ = client.testdata

    @patch("ksef2.clients.base.httpx.Client")
    def test_close_closes_owned_http_client(
        self,
        client_cls: MagicMock,
    ) -> None:
        http_client = MagicMock(spec=HTTPX_CLIENT_CLASS)
        client_cls.return_value = http_client

        client = Client(environment=Environment.TEST)
        client.close()

        http_client.close.assert_called_once()

    def test_close_does_not_close_user_supplied_http_client(self) -> None:
        http_client = MagicMock(spec=HTTPX_CLIENT_CLASS)

        client = Client(environment=Environment.TEST, http_client=http_client)
        client.close()

        http_client.close.assert_not_called()

    @patch("ksef2.clients.base.httpx.Client")
    def test_context_manager_closes_owned_client(
        self,
        client_cls: MagicMock,
    ) -> None:
        http_client = MagicMock(spec=HTTPX_CLIENT_CLASS)
        client_cls.return_value = http_client

        with Client(environment=Environment.TEST):
            pass

        http_client.close.assert_called_once()

    @patch("ksef2.clients.base.httpx.Client")
    def test_transport_config_is_translated_to_httpx_client(
        self,
        client_cls: MagicMock,
    ) -> None:
        http_client = MagicMock(spec=HTTPX_CLIENT_CLASS)
        client_cls.return_value = http_client

        config = TransportConfig(
            timeouts=TimeoutConfig(connect=1.0, read=2.0, write=3.0, pool=4.0),
            proxy_url="http://proxy.local:8080",
        )

        _ = Client(environment=Environment.TEST, transport_config=config)

        _, kwargs = client_cls.call_args
        timeout = kwargs["timeout"]
        assert isinstance(timeout, httpx.Timeout)
        assert timeout.connect == 1.0
        assert timeout.read == 2.0
        assert timeout.write == 3.0
        assert timeout.pool == 4.0
        assert kwargs["proxy"] == "http://proxy.local:8080"
        assert kwargs["http2"] is True

    @patch("ksef2.clients.base.httpx.Client")
    def test_accessors_raise_after_close(
        self,
        client_cls: MagicMock,
    ) -> None:
        client_cls.return_value = MagicMock(spec=HTTPX_CLIENT_CLASS)
        client = Client(environment=Environment.TEST)
        client.close()

        with pytest.raises(KSeFClientClosedError, match="Client is closed"):
            _ = client.authentication

    @patch("ksef2.clients.base.AuthClient")
    def test_authentication_accessor_uses_custom_certificate_store(
        self,
        auth_client_cls: MagicMock,
    ) -> None:
        store = CustomCertificateStore()
        client = Client(
            environment=Environment.TEST,
            http_client=MagicMock(spec=HTTPX_CLIENT_CLASS),
            certificate_store=store,
        )

        _ = client.authentication

        _, kwargs = auth_client_cls.call_args
        assert kwargs["certificate_store"] is store

    def test_authenticated_deprecated_wrapper_delegates_to_auth_branch(
        self,
        domain_auth_tokens: BaseFactory[AuthTokens],
    ) -> None:
        store = CustomCertificateStore()
        auth_tokens = domain_auth_tokens.build()
        client = Client(
            environment=Environment.TEST,
            http_client=MagicMock(spec=HTTPX_CLIENT_CLASS),
            certificate_store=store,
        )

        with pytest.deprecated_call(match="Client.authenticated"):
            authenticated = client.authenticated(auth_tokens)

        assert isinstance(authenticated, AuthenticatedClient)
        assert authenticated.resume_state().to_tokens() == auth_tokens
