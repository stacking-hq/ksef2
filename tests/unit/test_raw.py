import asyncio
from unittest.mock import MagicMock

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_base import AsyncClient
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.clients.base import Client
from ksef2.config import Environment
from ksef2.core.exceptions import KSeFUnsupportedEnvironmentError
from ksef2.core.routes import TokenRoutes
from ksef2.core.stores import CertificateStore
from ksef2.domain.models.auth import AuthTokens
from ksef2.endpoints.auth import AuthEndpoints
from ksef2.endpoints.encryption import EncryptionEndpoints
from ksef2.endpoints.invoices import InvoicesEndpoints
from ksef2.endpoints.permissions import (
    GetPermissionsEndpoints,
    PermissionsGrantEndpoints,
    QueryPermissionsEndpoints,
    RevokePermissionsEndpoints,
)
from ksef2.endpoints.tokens import TokenEndpoints
from ksef2.infra.schema.api import spec
from ksef2.raw import encrypt_invoice, generate_session_key, sha256_b64
from ksef2.raw.async_facade import AsyncRawAuthenticatedClient, AsyncRawClient
from ksef2.raw.facade import RawAuthenticatedClient, RawClient
from ksef2.raw.mappers import auth as auth_mapper
from tests.unit.fakes.transport import AsyncFakeTransport, FakeTransport


def test_root_client_exposes_raw_unauthenticated_endpoints() -> None:
    client = Client(
        environment=Environment.TEST, http_client=MagicMock(spec=httpx.Client)
    )

    assert isinstance(client.raw, RawClient)
    assert client.raw is client.raw
    assert isinstance(client.raw.auth, AuthEndpoints)
    assert isinstance(client.raw.encryption, EncryptionEndpoints)

    client.close()


def test_root_raw_testdata_respects_environment() -> None:
    client = Client(
        environment=Environment.PRODUCTION,
        http_client=MagicMock(spec=httpx.Client),
    )

    with pytest.raises(KSeFUnsupportedEnvironmentError):
        _ = client.raw.testdata

    client.close()


def test_root_client_binds_tokens_to_authenticated_raw_client(
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    client = Client(
        environment=Environment.TEST, http_client=MagicMock(spec=httpx.Client)
    )

    auth = client.authenticated(domain_auth_tokens.build())

    assert isinstance(auth, AuthenticatedClient)
    assert isinstance(auth.raw, RawAuthenticatedClient)
    assert isinstance(auth.raw.invoices, InvoicesEndpoints)
    assert isinstance(auth.raw.tokens, TokenEndpoints)
    assert isinstance(auth.raw.permissions.grant, PermissionsGrantEndpoints)
    assert isinstance(auth.raw.permissions.revoke, RevokePermissionsEndpoints)
    assert isinstance(auth.raw.permissions.query, QueryPermissionsEndpoints)
    assert isinstance(auth.raw.permissions.status, GetPermissionsEndpoints)

    client.close()


def test_authenticated_raw_endpoints_use_bearer_transport(
    fake_transport: FakeTransport,
    domain_auth_tokens: BaseFactory[AuthTokens],
    token_list_resp: BaseFactory[spec.QueryTokensResponse],
) -> None:
    auth_tokens = domain_auth_tokens.build()
    fake_transport.enqueue(token_list_resp.build().model_dump(mode="json"))
    client = AuthenticatedClient(
        transport=fake_transport,
        auth_tokens=auth_tokens,
        certificate_store=CertificateStore(),
        environment=Environment.TEST,
    )

    _ = client.raw.tokens.list_tokens()

    call = fake_transport.calls[0]
    assert call.method == "GET"
    assert call.path == TokenRoutes.LIST_TOKENS
    assert call.headers == {"Authorization": f"Bearer {auth_tokens.access_token.token}"}


def test_public_auth_mapper_converts_raw_tokens_to_domain_tokens(
    auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse],
) -> None:
    response = auth_tokens_resp.build()

    tokens = auth_mapper.from_spec(response)

    assert tokens.access_token.token == response.accessToken.token
    assert tokens.refresh_token.token == response.refreshToken.token


def test_raw_reexports_low_level_invoice_crypto_utilities() -> None:
    invoice_xml = b"<Invoice>raw</Invoice>"
    aes_key, iv = generate_session_key()

    encrypted = encrypt_invoice(xml_bytes=invoice_xml, key=aes_key, iv=iv)

    assert len(aes_key) == 32
    assert len(iv) == 16
    assert encrypted != invoice_xml
    assert sha256_b64(invoice_xml) != sha256_b64(encrypted)


def test_async_root_client_exposes_raw_unauthenticated_endpoints() -> None:
    client = AsyncClient(
        environment=Environment.TEST,
        http_client=MagicMock(spec=httpx.AsyncClient),
    )

    try:
        assert isinstance(client.raw, AsyncRawClient)
        assert client.raw is client.raw
    finally:
        asyncio.run(client.aclose())


def test_async_authenticated_raw_endpoints_use_bearer_transport(
    async_fake_transport: AsyncFakeTransport,
    domain_auth_tokens: BaseFactory[AuthTokens],
    token_list_resp: BaseFactory[spec.QueryTokensResponse],
) -> None:
    async def _run() -> None:
        auth_tokens = domain_auth_tokens.build()
        async_fake_transport.enqueue(token_list_resp.build().model_dump(mode="json"))
        client = AsyncAuthenticatedClient(
            transport=async_fake_transport,
            auth_tokens=auth_tokens,
            certificate_store=CertificateStore(),
            environment=Environment.TEST,
        )

        assert isinstance(client.raw, AsyncRawAuthenticatedClient)
        _ = await client.raw.tokens.list_tokens()

        call = async_fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == TokenRoutes.LIST_TOKENS
        assert call.headers == {
            "Authorization": f"Bearer {auth_tokens.access_token.token}"
        }

    asyncio.run(_run())
