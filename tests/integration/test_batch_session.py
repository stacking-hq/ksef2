"""Integration tests for batch session endpoints."""

import pytest

from ksef2 import Client, Environment
from ksef2.domain.models import BatchSessionState
from ksef2.domain.models.batch import (
    BatchFileInfo,
    BatchFilePart,
    BatchInvoice,
    PartUploadRequest,
)
from ksef2.domain.models.session import FormSchema
from tests.integration.conftest import KSeFCredentials
from tests.integration.invoice_payload import invoice_seller_nip
from tests.integration.invoice_payload import load_test_invoice_xml


@pytest.mark.integration
class TestBatchSession:
    """Tests for batch session endpoints.

    These tests verify the batch session lifecycle:
    - POST /sessions/batch (open batch session)
    - POST /sessions/batch/{referenceNumber}/close (close batch session)
    """

    def test_open_batch_session(self, ksef_credentials: KSeFCredentials) -> None:
        """Open, upload, close, and inspect a real batch session."""
        client = Client(environment=Environment.TEST)
        seller_nip = invoice_seller_nip(ksef_credentials.subject_nip)
        invoice_xml = load_test_invoice_xml()

        with client.testdata.temporal() as temp:
            if seller_nip != ksef_credentials.subject_nip:
                temp.create_subject(
                    nip=seller_nip,
                    subject_type="enforcement_authority",
                    description="Integration batch session seller",
                )
            auth = client.authentication.with_test_certificate(nip=seller_nip)
            invoice = BatchInvoice(
                file_name="invoice-01.xml",
                content=invoice_xml,
            )

            prepared_batch = auth.batch.prepare_batch(
                invoices=[invoice],
                form_code=FormSchema.FA3,
            )

            with auth.batch_session(prepared_batch=prepared_batch) as batch_session:
                assert batch_session.reference_number
                assert len(batch_session.reference_number) == 36
                assert batch_session.part_upload_requests
                assert len(batch_session.part_upload_requests) == 1

                upload_req = batch_session.part_upload_requests[0]
                assert upload_req.ordinal_number == 1
                assert upload_req.method == "PUT"
                assert upload_req.url
                assert upload_req.headers

                batch_session.upload_parts()
                state = batch_session.get_state()

            status = auth.batch.wait_for_completion(
                session=state,
                timeout=120.0,
                poll_interval=2.0,
            )
            assert status.status.code == 200
            assert status.invoice_count == 1
            assert status.successful_invoice_count == 1
            assert status.failed_invoice_count == 0

            invoices_page = auth.batch.list_invoices(session=state)
            assert len(invoices_page.invoices) == 1
            assert invoices_page.invoices[0].reference_number

    def test_batch_file_info_model(self) -> None:
        """Test that BatchFileInfo request validates correctly."""
        batch_file = BatchFileInfo(
            file_size=1000,
            file_hash="WO86CC+1Lef11wEosItld/NPwxGN8tobOMLqk9PQjgs=",
            parts=[
                BatchFilePart(
                    ordinal_number=1,
                    file_size=1000,
                    file_hash="23ZyDAN0H/+yhC/En2xbNfF0tajAWSfejDaXD7fc2AE=",
                )
            ],
        )

        assert batch_file.file_size == 1000
        assert len(batch_file.parts) == 1
        assert batch_file.parts[0].ordinal_number == 1

    def test_batch_file_info_multiple_parts(self) -> None:
        """Test BatchFileInfo with multiple parts."""
        parts = [
            BatchFilePart(
                ordinal_number=i,
                file_size=1000 * i,
                file_hash=f"hash{i}",
            )
            for i in range(1, 6)
        ]

        batch_file = BatchFileInfo(
            file_size=15000,
            file_hash="totalhash",
            parts=parts,
        )

        assert len(batch_file.parts) == 5
        assert batch_file.parts[0].ordinal_number == 1
        assert batch_file.parts[4].ordinal_number == 5

    def test_batch_session_state_serialization(self) -> None:
        """Test that BatchSessionState can be serialized and restored."""
        upload_requests = [
            PartUploadRequest(
                ordinal_number=1,
                method="PUT",
                url="https://example.com/upload/1",
                headers={"x-ms-blob-type": "BlockBlob"},
            )
        ]

        state = BatchSessionState.from_encoded(
            reference_number="20250217-SB-TEST123456-ABCDEF1234-E9",
            aes_key=b"0123456789abcdef0123456789abcdef",
            iv=b"0123456789abcdef",
            access_token="test-access-token",
            form_code=FormSchema.FA3,
            part_upload_requests=upload_requests,
        )

        # Serialize to JSON
        state_json = state.model_dump_json()

        # Restore from JSON
        restored = BatchSessionState.model_validate_json(state_json)

        assert restored.reference_number == state.reference_number
        assert restored.access_token == state.access_token
        assert restored.form_code == FormSchema.FA3
        assert len(restored.part_upload_requests) == 1
        assert restored.part_upload_requests[0].url == "https://example.com/upload/1"

        # Verify bytes can be decoded
        assert restored.get_aes_key_bytes() == b"0123456789abcdef0123456789abcdef"
        assert restored.get_iv_bytes() == b"0123456789abcdef"
