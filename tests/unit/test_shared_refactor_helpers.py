import asyncio
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from ksef2.clients.async_batch import AsyncBatchSessionClient
from ksef2.clients.async_base import AsyncClient
from ksef2.clients.base import Client
from ksef2.clients.batch import BatchSessionClient
from ksef2.config import Environment, TimeoutConfig, TransportConfig
from ksef2.core.http_config import HttpClientKwargs
from ksef2.domain.models.batch import BatchInvoice
from ksef2.domain.models.session import FormSchema
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.endpoints.base import BaseEndpoints
from ksef2.services.async_batch import AsyncBatchService
from ksef2.services.batch import BatchService
from tests.unit.fakes.transport import AsyncFakeTransport, FakeTransport
from tests.unit.helpers import VALID_PUBLIC_KEY_ID

HTTPX_CLIENT_CLASS = httpx.Client
HTTPX_ASYNC_CLIENT_CLASS = httpx.AsyncClient


def test_sync_and_async_endpoint_base_build_identical_params() -> None:
    params = {
        "pageOffset": 10,
        "pageSize": 50,
    }

    sync_params = BaseEndpoints(FakeTransport()).build_params(params)
    async_params = AsyncBaseEndpoints(AsyncFakeTransport()).build_params(params)

    assert sync_params == async_params
    assert str(sync_params) == "pageOffset=10&pageSize=50"


def test_sync_and_async_root_clients_use_equivalent_http_config_kwargs() -> None:
    config = TransportConfig(
        timeouts=TimeoutConfig(connect=1.0, read=2.0, write=3.0, pool=4.0),
        proxy_url="http://proxy.local:8080",
    )

    with (
        patch("ksef2.clients.base.httpx.Client") as sync_client_cls,
        patch("ksef2.clients.async_base.httpx.AsyncClient") as async_client_cls,
    ):
        sync_client_cls.return_value = MagicMock(spec=HTTPX_CLIENT_CLASS)
        async_client_cls.return_value = AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS)

        _ = Client(environment=Environment.TEST, transport_config=config)
        async_client = AsyncClient(
            environment=Environment.TEST, transport_config=config
        )
        asyncio.run(async_client.aclose())

    assert sync_client_cls.call_args is not None
    assert async_client_cls.call_args is not None
    sync_kwargs = cast(HttpClientKwargs, sync_client_cls.call_args.kwargs)
    async_kwargs = cast(HttpClientKwargs, async_client_cls.call_args.kwargs)

    assert sync_kwargs.keys() == async_kwargs.keys()
    assert sync_kwargs["base_url"] == async_kwargs["base_url"]
    assert sync_kwargs["proxy"] == async_kwargs["proxy"]
    assert sync_kwargs["trust_env"] == async_kwargs["trust_env"]
    assert sync_kwargs["http2"] == async_kwargs["http2"]
    assert sync_kwargs["verify"] == async_kwargs["verify"]
    assert sync_kwargs["timeout"].connect == async_kwargs["timeout"].connect
    assert sync_kwargs["timeout"].read == async_kwargs["timeout"].read
    assert sync_kwargs["timeout"].write == async_kwargs["timeout"].write
    assert sync_kwargs["timeout"].pool == async_kwargs["timeout"].pool
    assert (
        sync_kwargs["limits"].max_connections == async_kwargs["limits"].max_connections
    )
    assert (
        sync_kwargs["limits"].max_keepalive_connections
        == async_kwargs["limits"].max_keepalive_connections
    )


def test_sync_and_async_batch_preparation_share_metadata_logic() -> None:
    invoices = [
        BatchInvoice(file_name="invoice-1.xml", content=b"<Invoice>1</Invoice>"),
        BatchInvoice(file_name="invoice-2.xml", content=b"<Invoice>2</Invoice>"),
    ]

    def _sync_open_batch_session() -> BatchSessionClient:
        raise AssertionError("not used")

    async def _async_open_batch_session() -> AsyncBatchSessionClient:
        raise AssertionError("not used")

    sync_service = BatchService(
        authed_transport=FakeTransport(),
        upload_transport=FakeTransport(),
        get_encryption_key=lambda: (
            b"k" * 32,
            b"v" * 16,
            b"enc-key",
            VALID_PUBLIC_KEY_ID,
        ),
        open_batch_session=_sync_open_batch_session,
    )

    async def _get_encryption_key() -> tuple[bytes, bytes, bytes, str | None]:
        return b"k" * 32, b"v" * 16, b"enc-key", VALID_PUBLIC_KEY_ID

    async_service = AsyncBatchService(
        authed_transport=AsyncFakeTransport(),
        upload_transport=AsyncFakeTransport(),
        get_encryption_key=_get_encryption_key,
        open_batch_session=_async_open_batch_session,
    )

    def _encrypt_batch_part(*, payload: bytes, aes_key: bytes, iv: bytes) -> bytes:
        del aes_key, iv
        return b"encrypted-" + payload

    with (
        patch(
            "ksef2.services.batch_preparation.build_zip",
            return_value=b"deterministic-zip",
        ),
        patch(
            "ksef2.services.batch_preparation.encrypt_batch_part",
            side_effect=_encrypt_batch_part,
        ),
    ):
        sync_prepared = sync_service.prepare_batch(
            invoices=invoices,
            form_code=FormSchema.FA3,
        )
        async_prepared = asyncio.run(
            async_service.prepare_batch(
                invoices=invoices,
                form_code=FormSchema.FA3,
            )
        )

    assert sync_prepared.model_dump(mode="json") == async_prepared.model_dump(
        mode="json"
    )
    assert sync_prepared.batch_file.file_size == len(b"deterministic-zip")
    assert sync_prepared.parts[0].content == b"encrypted-deterministic-zip"


def test_batch_session_client_types_remain_public() -> None:
    assert BatchSessionClient.__name__ == "BatchSessionClient"
    assert AsyncBatchSessionClient.__name__ == "AsyncBatchSessionClient"
