from unittest.mock import patch

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._clients.batch import BatchSessionClient
from ksef2._core.exceptions import KSeFBatchUploadError, KSeFClientClosedError
from ksef2._core.routes import InvoiceRoutes, SessionRoutes
from ksef2._domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchPreparedPart,
    BatchSessionResumeState,
    PartUploadRequest,
    PreparedBatch,
)
from ksef2._core.crypto import sha256_b64
from ksef2._infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport


def _build_prepared_batch() -> PreparedBatch:
    return PreparedBatch(
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


class TestBatchSessionClient:
    def test_close_is_idempotent_and_keeps_reference_accessible(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        client = BatchSessionClient(fake_transport, state)
        fake_transport.enqueue({})

        client.close()
        client.close()

        assert len(fake_transport.calls) == 1
        assert fake_transport.calls[0].method == "POST"
        assert fake_transport.calls[0].path == SessionRoutes.CLOSE_BATCH.format(
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
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        prepared_batch = _build_prepared_batch()
        client = BatchSessionClient(
            fake_transport,
            state,
            prepared_batch=prepared_batch,
        )
        fake_transport.enqueue(status_code=201, json_body={})

        client.upload_parts()

        assert fake_transport.calls[0].method == "PUT"
        assert fake_transport.calls[0].path == state.part_upload_requests[0].url
        assert fake_transport.calls[0].headers == {
            "Content-Type": "application/octet-stream",
            "x-ms-blob-type": "BlockBlob",
        }

    def test_context_manager_closes_batch_session_on_exit(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        fake_transport.enqueue(json_body={})

        with BatchSessionClient(fake_transport, state) as session:
            assert session.reference_number == state.reference_number

        assert fake_transport.calls[0].method == "POST"
        assert fake_transport.calls[0].path == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=state.reference_number
        )

    def test_context_manager_does_not_close_after_ambiguous_upload_failure(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        signed_url = "https://storage.example/upload/part-1?sig=secret"
        state = domain_batch_session_state.build(
            reference_number="batch-ref",
            part_upload_requests=[
                PartUploadRequest(
                    ordinal_number=1,
                    method="PUT",
                    url=signed_url,
                    headers={"x-ms-blob-type": "BlockBlob"},
                )
            ],
        )
        client = BatchSessionClient(
            fake_transport,
            state,
            upload_transport=fake_transport,
            prepared_batch=_build_prepared_batch(),
        )
        lost_response = httpx.ReadTimeout(
            "response lost",
            request=httpx.Request("PUT", signed_url),
        )

        with patch.object(
            fake_transport,
            "request",
            side_effect=lost_response,
        ) as request:
            with pytest.raises(KSeFBatchUploadError) as exc_info:
                with client:
                    client.upload_parts()

        error = exc_info.value
        assert error.outcome_ambiguous is True
        assert error.recovery_state() is state
        assert "sig=secret" not in str(error)
        assert "sig=secret" not in repr(error.context)
        assert client.part_upload_requests == state.part_upload_requests
        request.assert_called_once()

    def test_context_manager_propagates_close_failure_and_keeps_state_resumable(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        client = BatchSessionClient(fake_transport, state)

        with pytest.raises(RuntimeError, match="no more queued responses"):
            with client:
                pass

        assert client.resume_state() is state
        assert client.part_upload_requests == state.part_upload_requests
        assert len(fake_transport.calls) == 1

    def test_get_status_reads_session_status(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        state = domain_batch_session_state.build()
        client = BatchSessionClient(fake_transport, state)
        fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        status = client.get_status()

        assert status.status.code == 200
        assert fake_transport.calls[0].method == "GET"
        assert fake_transport.calls[0].path == InvoiceRoutes.SESSION_STATUS.format(
            referenceNumber=state.reference_number
        )

    def test_list_invoices_reads_batch_session_invoice_page(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_invoices_resp: BaseFactory[spec.SessionInvoicesResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        state = domain_batch_session_state.build()
        client = BatchSessionClient(fake_transport, state)
        fake_transport.enqueue(
            inv_session_invoices_resp.build(
                invoices=[
                    inv_session_invoice_status_resp.build(
                        referenceNumber="20250625-EE-319D7EE000-B67F415CDC-2C",
                        invoiceHash="x" * 44,
                    )
                ]
            ).model_dump(mode="json")
        )

        result = client.list_invoices(page_size=25, continuation_token="next")

        assert len(result.invoices) == 1
        assert fake_transport.calls[0].method == "GET"
        assert fake_transport.calls[
            0
        ].path == InvoiceRoutes.LIST_SESSION_INVOICES.format(
            referenceNumber=state.reference_number
        )
        assert fake_transport.calls[0].headers == {"x-continuation-token": "next"}

    def test_get_upo_downloads_collective_session_upo(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        client = BatchSessionClient(fake_transport, state)
        fake_transport.enqueue(content=b"<upo />")

        upo = client.get_upo(upo_reference_number="upo-ref")

        assert upo == b"<upo />"
        assert fake_transport.calls[0].method == "GET"
        assert fake_transport.calls[0].path == SessionRoutes.GET_SESSION_UPO.format(
            referenceNumber=state.reference_number,
            upoReferenceNumber="upo-ref",
        )
