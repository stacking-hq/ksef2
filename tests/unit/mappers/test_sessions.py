from polyfactory import BaseFactory

from ksef2.domain.models.batch import (
    BatchFileInfo,
    OpenBatchSessionRequest,
    OpenBatchSessionResponse,
    PartUploadRequest,
)
from ksef2.domain.models.pagination import ListSessionsQuery
from ksef2.domain.models.session import (
    FormSchema,
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SessionInvoicesResponse,
    SessionStatusResponse,
)
from ksef2.infra.mappers.sessions import from_spec, to_spec
from ksef2.infra.schema.api import spec


class TestSessionRequestMapper:
    def test_to_spec_form_schema_fa_rr1(self) -> None:
        result = to_spec(FormSchema.FA_RR1)

        assert isinstance(result, spec.FormCode)
        assert result.systemCode == "FA_RR (1)"
        assert result.schemaVersion == "1-1E"
        assert result.value == "FA_RR"

    def test_to_spec_open_online_session_request(
        self,
        domain_session_open_online_req: BaseFactory[OpenOnlineSessionRequest],
    ) -> None:
        request = domain_session_open_online_req.build(
            encrypted_key=b"secret",
            iv=b"\x00" * 16,
            form_code=FormSchema.PEF3,
        )

        result = to_spec(request)

        assert isinstance(result, spec.OpenOnlineSessionRequest)
        assert result.formCode.systemCode == "PEF (3)"
        assert result.formCode.schemaVersion == "2-1"
        assert result.formCode.value == "PEF"
        assert result.encryption.encryptedSymmetricKey == "c2VjcmV0"
        assert result.encryption.initializationVector == "AAAAAAAAAAAAAAAAAAAAAA=="
        assert result.encryption.publicKeyId == request.public_key_id

    def test_to_spec_open_batch_session_request(
        self,
        domain_session_open_batch_req: BaseFactory[OpenBatchSessionRequest],
        domain_batch_file_info: BaseFactory[BatchFileInfo],
    ) -> None:
        request = domain_session_open_batch_req.build(
            encrypted_key=b"batch-secret",
            iv=b"\x01" * 16,
            form_code=FormSchema.FA2,
            offline_mode=True,
            batch_file=domain_batch_file_info.build(
                file_size=2048,
                file_hash="ZmFrZS1iYXRjaC1oYXNoLWJhc2U2NA==",
            ),
        )

        result = to_spec(request)

        assert isinstance(result, spec.OpenBatchSessionRequest)
        assert result.formCode.systemCode == "FA (2)"
        assert result.formCode.schemaVersion == "1-0E"
        assert result.formCode.value == "FA"
        assert result.batchFile.fileSize == 2048
        assert result.batchFile.fileHash == "ZmFrZS1iYXRjaC1oYXNoLWJhc2U2NA=="
        assert result.encryption.encryptedSymmetricKey == "YmF0Y2gtc2VjcmV0"
        assert result.encryption.initializationVector == "AQEBAQEBAQEBAQEBAQEBAQ=="
        assert result.encryption.publicKeyId == request.public_key_id
        assert result.offlineMode is True

    def test_list_sessions_query_params(
        self,
        domain_session_list_query: BaseFactory[ListSessionsQuery],
    ) -> None:
        request = domain_session_list_query.build(
            page_size=25,
            session_type="online",
            date_created_from="2026-03-05T10:00:00+00:00",
        ).to_query_params()

        assert request is not None
        assert isinstance(request, dict)
        assert request.get("pageSize") == 25
        assert request.get("sessionType") == "Online"
        assert request.get("dateCreatedFrom") == "2026-03-05T10:00:00Z"


class TestSessionResponseMapper:
    def test_from_spec_open_online_session_response(
        self,
        session_open_online_resp: BaseFactory[spec.OpenOnlineSessionResponse],
    ) -> None:
        response = session_open_online_resp.build(
            referenceNumber="20250625-SO-2C3E6C8000-B675CF5D68-07",
            validUntil="2026-03-05T11:00:00+00:00",
        )

        result = from_spec(response)

        assert isinstance(result, OpenOnlineSessionResponse)
        assert result.reference_number == response.referenceNumber
        assert result.valid_until == response.validUntil

    def test_from_spec_open_batch_session_response(
        self,
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
        session_part_upload_req: BaseFactory[spec.PartUploadRequest],
    ) -> None:
        response = session_open_batch_resp.build(
            referenceNumber="20250625-SB-2C3E6C8000-B675CF5D68-07",
            partUploadRequests=[
                session_part_upload_req.build(
                    ordinalNumber=1,
                    method="PUT",
                    url="https://example.com/upload/part-1",
                    headers={"x-ms-blob-type": "BlockBlob"},
                )
            ],
        )

        result = from_spec(response)

        assert isinstance(result, OpenBatchSessionResponse)
        assert result.reference_number == response.referenceNumber
        assert result.part_upload_requests == [
            PartUploadRequest(
                ordinal_number=1,
                method="PUT",
                url="https://example.com/upload/part-1",
                headers={"x-ms-blob-type": "BlockBlob"},
            )
        ]

    def test_from_spec_session_status_response(
        self,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        response = inv_session_status_resp.build(
            status=spec.StatusInfo(code=100, description="Open", details=["ok"]),
            dateCreated="2026-03-05T10:00:00+00:00",
            dateUpdated="2026-03-05T10:01:00+00:00",
            validUntil="2026-03-05T11:00:00+00:00",
            invoiceCount=3,
            successfulInvoiceCount=2,
            failedInvoiceCount=1,
        )

        result = from_spec(response)

        assert isinstance(result, SessionStatusResponse)
        assert result.status.code == 100
        assert result.invoice_count == 3
        assert result.successful_invoice_count == 2
        assert result.failed_invoice_count == 1

    def test_from_spec_session_invoices_response(
        self,
        inv_session_invoices_resp: BaseFactory[spec.SessionInvoicesResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        response = inv_session_invoices_resp.build(
            continuationToken="next-page",
            invoices=[
                inv_session_invoice_status_resp.build(
                    ordinalNumber=1,
                    invoiceNumber="FV/1",
                    referenceNumber="20250625-EE-319D7EE000-B67F415CDC-2C",
                    invoiceHash="x" * 44,
                    invoicingDate="2026-03-05T10:00:00+00:00",
                    status=spec.InvoiceStatusInfo(
                        code=200,
                        description="Processed",
                        details=None,
                        extensions={"key": "value"},
                    ),
                )
            ],
        )

        result = from_spec(response)

        assert isinstance(result, SessionInvoicesResponse)
        assert result.continuation_token == "next-page"
        assert result.invoices[0].status.extensions == {"key": "value"}
