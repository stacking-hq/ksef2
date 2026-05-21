from io import BytesIO
from zipfile import ZipFile

import pytest
from polyfactory import BaseFactory

from ksef2.clients.batch import BatchSessionClient
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
from ksef2.services.batch import BatchService
from tests.unit.fakes.transport import FakeTransport
from tests.unit.helpers import VALID_PUBLIC_KEY_ID


def _build_service(
    fake_transport: FakeTransport,
    *,
    open_batch_session,
    get_encryption_key=None,
) -> BatchService:
    return BatchService(
        authed_transport=fake_transport,
        upload_transport=fake_transport,
        get_encryption_key=get_encryption_key
        or (lambda: (b"k" * 32, b"v" * 16, b"enc-key", VALID_PUBLIC_KEY_ID)),
        open_batch_session=open_batch_session,
    )


class TestBatchService:
    def test_prepare_batch_builds_zip_metadata_and_encrypted_part(
        self,
        fake_transport: FakeTransport,
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=lambda **_: pytest.fail("not used"),
        )
        invoices = [
            BatchInvoice(file_name="invoice-1.xml", content=b"<Invoice>1</Invoice>"),
            BatchInvoice(file_name="invoice-2.xml", content=b"<Invoice>2</Invoice>"),
        ]

        prepared = service.prepare_batch(invoices=invoices, form_code=FormSchema.FA3)

        assert prepared.form_code is FormSchema.FA3
        assert len(prepared.parts) == 1
        assert prepared.batch_file.compression_type == "zip"
        assert prepared.invoices[0].invoice_hash == sha256_b64(invoices[0].content)
        assert prepared.invoices[1].invoice_hash == sha256_b64(invoices[1].content)
        assert prepared.encryption.public_key_id == VALID_PUBLIC_KEY_ID

        decrypted_zip = decrypt_aes_cbc(
            prepared.parts[0].content,
            key=prepared.encryption.get_aes_key_bytes(),
            iv=prepared.encryption.get_iv_bytes(),
        )
        with ZipFile(BytesIO(decrypted_zip)) as archive:
            assert sorted(archive.namelist()) == ["invoice-1.xml", "invoice-2.xml"]
            assert archive.read("invoice-1.xml") == b"<Invoice>1</Invoice>"
            assert archive.read("invoice-2.xml") == b"<Invoice>2</Invoice>"

        assert prepared.batch_file.file_size == len(decrypted_zip)
        assert prepared.batch_file.file_hash == sha256_b64(decrypted_zip)
        assert prepared.batch_file.parts[0].file_size == len(prepared.parts[0].content)
        assert prepared.batch_file.parts[0].file_hash == sha256_b64(
            prepared.parts[0].content
        )

    def test_prepare_batch_rejects_duplicate_file_names(
        self,
        fake_transport: FakeTransport,
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=lambda **_: pytest.fail("not used"),
        )

        with pytest.raises(KSeFValidationError, match="must be unique"):
            _ = service.prepare_batch(
                invoices=[
                    BatchInvoice(file_name="invoice.xml", content=b"1"),
                    BatchInvoice(file_name="invoice.xml", content=b"2"),
                ]
            )

    def test_upload_parts_uses_presigned_urls_without_auth_header(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionState],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=lambda **_: pytest.fail("not used"),
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
        session = BatchSessionClient(fake_transport, state)
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
        fake_transport.enqueue(status_code=201, json_body={})

        service.upload_parts(session=session, prepared_batch=prepared_batch)

        assert fake_transport.calls[0].method == "PUT"
        assert fake_transport.calls[0].path == "https://example.com/upload/part-1"
        assert fake_transport.calls[0].headers == {
            "Content-Type": "application/octet-stream",
            "x-ms-blob-type": "BlockBlob",
        }

    def test_submit_prepared_batch_uploads_parts_and_closes_session(
        self,
        fake_transport: FakeTransport,
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
        service = _build_service(
            fake_transport,
            open_batch_session=lambda **kwargs: BatchSessionClient(
                fake_transport,
                state,
                prepared_batch=kwargs.get("prepared_batch"),
            ),
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
        fake_transport.enqueue(status_code=201, json_body={})
        fake_transport.enqueue(json_body={})

        result = service.submit_prepared_batch(prepared_batch=prepared_batch)

        assert result.reference_number == "batch-ref"
        assert fake_transport.calls[0].method == "PUT"
        assert fake_transport.calls[1].method == "POST"

    def test_wait_for_completion_returns_terminal_success(
        self,
        fake_transport: FakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=lambda **_: pytest.fail("not used"),
        )
        fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=100, description="In progress"),
            ).model_dump(mode="json")
        )
        fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        status = service.wait_for_completion(
            session="batch-ref",
            timeout=1.0,
            poll_interval=0.0,
        )

        assert status.status.code == 200
        assert len(fake_transport.calls) == 2

    def test_wait_for_completion_raises_on_terminal_failure(
        self,
        fake_transport: FakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=lambda **_: pytest.fail("not used"),
        )
        fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=450, description="Rejected"),
            ).model_dump(mode="json")
        )

        with pytest.raises(KSeFSessionError, match="Rejected"):
            _ = service.wait_for_completion(
                session="batch-ref",
                timeout=1.0,
                poll_interval=0.0,
            )

    def test_wait_for_completion_raises_on_timeout(
        self,
        fake_transport: FakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=lambda **_: pytest.fail("not used"),
        )
        for _ in range(3):
            fake_transport.enqueue(
                inv_session_status_resp.build(
                    status=spec.StatusInfo(code=100, description="In progress"),
                ).model_dump(mode="json")
            )

        with pytest.raises(KSeFBatchSessionTimeoutError, match="not ready"):
            _ = service.wait_for_completion(
                session="batch-ref",
                timeout=0.0,
                poll_interval=0.0,
            )
