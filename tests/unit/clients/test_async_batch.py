import asyncio

import pytest
from polyfactory import BaseFactory

from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_batch import AsyncBatchSessionClient
from ksef2.core.crypto import sha256_b64
from ksef2.core.exceptions import KSeFClientClosedError
from ksef2.core.routes import InvoiceRoutes, SessionRoutes
from ksef2.core.stores import CertificateStore
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchPreparedPart,
    BatchSessionResumeState,
    PreparedBatch,
)
from ksef2.domain.models.session import FormSchema
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport


def _build_authenticated_client(
    async_fake_transport: AsyncFakeTransport,
    auth_tokens: AuthTokens,
) -> AsyncAuthenticatedClient:
    return AsyncAuthenticatedClient(
        transport=async_fake_transport,
        auth_tokens=auth_tokens,
        certificate_store=CertificateStore(),
    )


def _build_prepared_batch() -> PreparedBatch:
    return PreparedBatch(
        form_code=FormSchema.FA3,
        offline_mode=False,
        batch_file=BatchFileInfo(
            file_size=10,
            file_hash=sha256_b64(b"plaintext"),
            parts=[
                BatchFilePart(
                    ordinal_number=1,
                    file_size=12,
                    file_hash=sha256_b64(b"encrypted"),
                )
            ],
        ),
        parts=[
            BatchPreparedPart(
                ordinal_number=1,
                content=b"encrypted",
                file_size=len(b"encrypted"),
                file_hash=sha256_b64(b"encrypted"),
            )
        ],
        encryption=BatchEncryptionData.from_bytes(
            aes_key=b"k" * 32,
            iv=b"v" * 16,
            encrypted_key=b"enc-key",
        ),
        invoices=[],
    )


class TestAsyncBatchSessionClient:
    def test_aclose_is_idempotent_and_keeps_reference_accessible(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        client = AsyncBatchSessionClient(async_fake_transport, state)
        async_fake_transport.enqueue({})

        asyncio.run(client.aclose())
        asyncio.run(client.aclose())

        assert len(async_fake_transport.calls) == 1
        assert async_fake_transport.calls[0].method == "POST"
        assert async_fake_transport.calls[0].path == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=state.reference_number
        )

        assert client.reference_number == state.reference_number
        assert client.resume_state() == state
        with pytest.deprecated_call(match="get_state"):
            assert client.get_state() == state

        with pytest.raises(KSeFClientClosedError, match="Session client is closed"):
            _ = client.part_upload_requests

    def test_upload_parts_uses_attached_prepared_batch(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        prepared_batch = PreparedBatch(
            batch_file=BatchFileInfo(
                file_size=10,
                file_hash=sha256_b64(b"plaintext"),
                parts=[
                    BatchFilePart(
                        ordinal_number=1,
                        file_size=12,
                        file_hash=sha256_b64(b"encrypted"),
                    )
                ],
            ),
            parts=[
                BatchPreparedPart(
                    ordinal_number=1,
                    content=b"encrypted",
                    file_size=len(b"encrypted"),
                    file_hash=sha256_b64(b"encrypted"),
                )
            ],
            encryption=BatchEncryptionData.from_bytes(
                aes_key=b"k" * 32,
                iv=b"v" * 16,
                encrypted_key=b"enc-key",
            ),
            invoices=[],
        )
        client = AsyncBatchSessionClient(
            async_fake_transport,
            state,
            prepared_batch=prepared_batch,
        )
        async_fake_transport.enqueue(status_code=201, json_body={})

        asyncio.run(client.upload_parts())

        assert async_fake_transport.calls[0].method == "PUT"
        assert async_fake_transport.calls[0].path == state.part_upload_requests[0].url
        assert async_fake_transport.calls[0].headers == {
            "Content-Type": "application/octet-stream",
            "x-ms-blob-type": "BlockBlob",
        }

    def test_async_context_manager_closes_batch_session_on_exit(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        async_fake_transport.enqueue(json_body={})

        async def _run() -> None:
            async with AsyncBatchSessionClient(async_fake_transport, state) as session:
                assert session.reference_number == state.reference_number

        asyncio.run(_run())

        assert async_fake_transport.calls[0].method == "POST"
        assert async_fake_transport.calls[0].path == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=state.reference_number
        )

    def test_get_status_reads_session_status(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        state = domain_batch_session_state.build()
        client = AsyncBatchSessionClient(async_fake_transport, state)
        async_fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        status = asyncio.run(client.get_status())

        assert status.status.code == 200
        assert async_fake_transport.calls[0].method == "GET"
        assert async_fake_transport.calls[
            0
        ].path == InvoiceRoutes.SESSION_STATUS.format(
            referenceNumber=state.reference_number
        )

    def test_get_upo_downloads_collective_session_upo(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        client = AsyncBatchSessionClient(async_fake_transport, state)
        async_fake_transport.enqueue(content=b"<upo />")

        upo = asyncio.run(client.get_upo(upo_reference_number="upo-ref"))

        assert upo == b"<upo />"
        assert async_fake_transport.calls[0].method == "GET"
        assert async_fake_transport.calls[
            0
        ].path == SessionRoutes.GET_SESSION_UPO.format(
            referenceNumber=state.reference_number,
            upoReferenceNumber="upo-ref",
        )


class TestAsyncAuthenticatedBatchSession:
    def test_batch_session_await_returns_client(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
    ) -> None:
        async_fake_transport.enqueue(
            session_open_batch_resp.build().model_dump(mode="json")
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
        )

        async def _run() -> AsyncBatchSessionClient:
            return await client.batch_session(prepared_batch=_build_prepared_batch())

        batch_client = asyncio.run(_run())

        assert isinstance(batch_client, AsyncBatchSessionClient)
        assert async_fake_transport.calls[0].method == "POST"
        assert async_fake_transport.calls[0].path == SessionRoutes.OPEN_BATCH

    def test_batch_session_context_manager_opens_and_closes_session(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
    ) -> None:
        open_response = session_open_batch_resp.build()
        reference_number = open_response.referenceNumber
        async_fake_transport.enqueue(open_response.model_dump(mode="json"))
        async_fake_transport.enqueue({})
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
        )

        async def _run() -> None:
            async with client.batch_session(
                prepared_batch=_build_prepared_batch()
            ) as session:
                assert session.reference_number == reference_number

        asyncio.run(_run())

        assert [call.method for call in async_fake_transport.calls] == ["POST", "POST"]
        assert async_fake_transport.calls[0].path == SessionRoutes.OPEN_BATCH
        assert async_fake_transport.calls[1].path == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=reference_number
        )

    def test_batch_session_context_manager_closes_after_exception(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
    ) -> None:
        open_response = session_open_batch_resp.build()
        reference_number = open_response.referenceNumber
        async_fake_transport.enqueue(open_response.model_dump(mode="json"))
        async_fake_transport.enqueue({})
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
        )

        async def _run() -> None:
            async with client.batch_session(prepared_batch=_build_prepared_batch()):
                raise ValueError("block failed")

        with pytest.raises(ValueError, match="block failed"):
            asyncio.run(_run())

        assert async_fake_transport.calls[1].path == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=reference_number
        )

    def test_resume_batch_session_context_manager_closes_session(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
        )
        state = domain_batch_session_state.build()
        async_fake_transport.enqueue({})

        async def _run() -> None:
            async with client.resume_batch_session(state=state) as session:
                assert session.resume_state() == state

        asyncio.run(_run())

        assert async_fake_transport.calls[0].path == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=state.reference_number
        )
