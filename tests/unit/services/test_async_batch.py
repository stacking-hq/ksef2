from io import BytesIO
from zipfile import ZipFile
import asyncio

import pytest
from polyfactory import BaseFactory

from ksef2.clients.async_batch import AsyncBatchSessionClient
from ksef2.core.crypto import decrypt_aes_cbc, sha256_b64
from ksef2.core.exceptions import (
    KSeFBatchSessionTimeoutError,
    KSeFSessionError,
    KSeFValidationError,
)
from ksef2.domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchInvoice,
    BatchPreparedPart,
    BatchSessionState,
    PartUploadRequest,
    PreparedBatch,
)
from ksef2.domain.models.session import FormSchema
from ksef2.infra.schema.api import spec
from ksef2.services.async_batch import AsyncBatchService
from tests.unit.fakes.transport import AsyncFakeTransport
from tests.unit.helpers import VALID_PUBLIC_KEY_ID


def _build_service(
    async_fake_transport: AsyncFakeTransport,
    *,
    open_batch_session,
    get_encryption_key=None,
) -> AsyncBatchService:
    async def _default_get_encryption_key() -> tuple[bytes, bytes, bytes, str | None]:
        return b"k" * 32, b"v" * 16, b"enc-key", VALID_PUBLIC_KEY_ID

    return AsyncBatchService(
        authed_transport=async_fake_transport,
        upload_transport=async_fake_transport,
        get_encryption_key=get_encryption_key or _default_get_encryption_key,
        open_batch_session=open_batch_session,
    )


class TestAsyncBatchService:
    def test_prepare_batch_builds_zip_metadata_and_encrypted_part(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        async def _open_batch_session(**_):
            raise AssertionError("not used")

        service = _build_service(
            async_fake_transport,
            open_batch_session=_open_batch_session,
        )
        invoices = [
            BatchInvoice(file_name="invoice-1.xml", content=b"<Invoice>1</Invoice>"),
            BatchInvoice(file_name="invoice-2.xml", content=b"<Invoice>2</Invoice>"),
        ]

        prepared = asyncio.run(
            service.prepare_batch(invoices=invoices, form_code=FormSchema.FA3)
        )

        assert prepared.form_code is FormSchema.FA3
        assert len(prepared.parts) == 1
        assert prepared.encryption.public_key_id == VALID_PUBLIC_KEY_ID
        assert prepared.invoices[0].invoice_hash == sha256_b64(invoices[0].content)
        assert prepared.invoices[1].invoice_hash == sha256_b64(invoices[1].content)

        decrypted_zip = decrypt_aes_cbc(
            prepared.parts[0].content,
            key=prepared.encryption.get_aes_key_bytes(),
            iv=prepared.encryption.get_iv_bytes(),
        )
        with ZipFile(BytesIO(decrypted_zip)) as archive:
            assert sorted(archive.namelist()) == ["invoice-1.xml", "invoice-2.xml"]
            assert archive.read("invoice-1.xml") == b"<Invoice>1</Invoice>"
            assert archive.read("invoice-2.xml") == b"<Invoice>2</Invoice>"

    def test_prepare_batch_rejects_duplicate_file_names(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        async def _open_batch_session(**_):
            raise AssertionError("not used")

        service = _build_service(
            async_fake_transport,
            open_batch_session=_open_batch_session,
        )

        with pytest.raises(KSeFValidationError, match="must be unique"):
            asyncio.run(
                service.prepare_batch(
                    invoices=[
                        BatchInvoice(file_name="invoice.xml", content=b"1"),
                        BatchInvoice(file_name="invoice.xml", content=b"2"),
                    ]
                )
            )

    def test_upload_parts_uses_presigned_urls_without_auth_header(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionState],
    ) -> None:
        async def _open_batch_session(**_):
            raise AssertionError("not used")

        service = _build_service(
            async_fake_transport,
            open_batch_session=_open_batch_session,
        )
        state = domain_batch_session_state.build(
            part_upload_requests=[
                PartUploadRequest(
                    ordinal_number=1,
                    method="PUT",
                    url="https://example.com/upload/part-1",
                    headers={"x-ms-blob-type": "BlockBlob"},
                )
            ]
        )
        session = AsyncBatchSessionClient(async_fake_transport, state)
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
        async_fake_transport.enqueue(status_code=201, json_body={})

        asyncio.run(
            service.upload_parts(session=session, prepared_batch=prepared_batch)
        )

        assert async_fake_transport.calls[0].method == "PUT"
        assert async_fake_transport.calls[0].path == "https://example.com/upload/part-1"
        assert async_fake_transport.calls[0].headers == {
            "Content-Type": "application/octet-stream",
            "x-ms-blob-type": "BlockBlob",
        }

    def test_submit_prepared_batch_uploads_parts_and_closes_session(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionState],
    ) -> None:
        state = domain_batch_session_state.build(
            reference_number="batch-ref",
            part_upload_requests=[
                PartUploadRequest(
                    ordinal_number=1,
                    method="PUT",
                    url="https://example.com/upload/part-1",
                    headers={"x-ms-blob-type": "BlockBlob"},
                )
            ],
        )

        async def _open_batch_session(**kwargs):
            return AsyncBatchSessionClient(
                async_fake_transport,
                state,
                prepared_batch=kwargs.get("prepared_batch"),
            )

        service = _build_service(
            async_fake_transport,
            open_batch_session=_open_batch_session,
        )
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
        async_fake_transport.enqueue(status_code=201, json_body={})
        async_fake_transport.enqueue(json_body={})

        result = asyncio.run(
            service.submit_prepared_batch(prepared_batch=prepared_batch)
        )

        assert result.reference_number == "batch-ref"
        assert async_fake_transport.calls[0].method == "PUT"
        assert async_fake_transport.calls[1].method == "POST"

    def test_wait_for_completion_returns_terminal_success(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        async def _open_batch_session(**_):
            raise AssertionError("not used")

        service = _build_service(
            async_fake_transport,
            open_batch_session=_open_batch_session,
        )
        async_fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=100, description="In progress"),
            ).model_dump(mode="json")
        )
        async_fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        status = asyncio.run(
            service.wait_for_completion(
                session="batch-ref",
                timeout=1.0,
                poll_interval=0.0,
            )
        )

        assert status.status.code == 200
        assert len(async_fake_transport.calls) == 2

    def test_wait_for_completion_raises_on_terminal_failure(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        async def _open_batch_session(**_):
            raise AssertionError("not used")

        service = _build_service(
            async_fake_transport,
            open_batch_session=_open_batch_session,
        )
        async_fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=450, description="Rejected"),
            ).model_dump(mode="json")
        )

        with pytest.raises(KSeFSessionError, match="Rejected"):
            asyncio.run(
                service.wait_for_completion(
                    session="batch-ref",
                    timeout=1.0,
                    poll_interval=0.0,
                )
            )

    def test_wait_for_completion_raises_on_timeout(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        async def _open_batch_session(**_):
            raise AssertionError("not used")

        service = _build_service(
            async_fake_transport,
            open_batch_session=_open_batch_session,
        )
        async_fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=100, description="In progress"),
            ).model_dump(mode="json")
        )

        with pytest.raises(KSeFBatchSessionTimeoutError, match="not ready"):
            asyncio.run(
                service.wait_for_completion(
                    session="batch-ref",
                    timeout=0.0,
                    poll_interval=0.0,
                )
            )
