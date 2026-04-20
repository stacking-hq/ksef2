from unittest.mock import patch, MagicMock

from polyfactory import BaseFactory

from ksef2.clients.invoices import InvoicesClient
from ksef2.core.routes import InvoiceRoutes
from ksef2.domain.models import invoices
from ksef2.domain.models.session import FormSchema
from ksef2.domain.models.pagination import InvoiceMetadataParams
from ksef2.infra.mappers.invoices import to_spec
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport


class TestInvoicesClient:
    def test_initialization(self, invoices_client: InvoicesClient) -> None:
        assert invoices_client is not None

    def test_query_metadata(
        self,
        invoices_client: InvoicesClient,
        fake_transport: FakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        expected = inv_query_metadata_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        filters = inv_export_filters.build(invoice_schema=FormSchema.FA_RR1)
        result = invoices_client.query_metadata(
            filters=filters,
            params=InvoiceMetadataParams(
                page_size=20,
                page_offset=1,
                sort_order="asc",
            ),
        )
        expected_request = to_spec(filters)

        assert isinstance(result, invoices.QueryInvoicesMetadataResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == InvoiceRoutes.QUERY_METADATA
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request
        assert call.params is not None
        assert call.params["pageSize"] == "20"
        assert call.params["pageOffset"] == "1"
        assert call.params["sortOrder"] == "Asc"

    def test_download_invoice(
        self,
        invoices_client: InvoicesClient,
        fake_transport: FakeTransport,
    ) -> None:
        fake_transport.enqueue(content=b"<Invoice />")

        result = invoices_client.download_invoice(ksef_number="ksef-123")

        assert result == b"<Invoice />"
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == InvoiceRoutes.DOWNLOAD.format(ksefNumber="ksef-123")

    @patch("ksef2.clients.invoices.encrypt_symmetric_key", return_value=b"enc-key")
    @patch(
        "ksef2.clients.invoices.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_schedule_export(
        self,
        _mock_generate_session_key: MagicMock,
        _mock_encrypt_symmetric_key: MagicMock,
        invoices_client: InvoicesClient,
        fake_transport: FakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_export_resp: BaseFactory[spec.ExportInvoicesResponse],
    ) -> None:
        expected = inv_export_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        filters = inv_export_filters.build()
        result = invoices_client.schedule_export(
            filters=filters,
            encryption_certificate="ZmFrZS1jZXJ0",
            only_metadata=True,
        )
        expected_request = to_spec(
            invoices.ExportInvoicesPayload(
                filter=filters,
                encrypted_symmetric_key="ZW5jLWtleQ==",
                initialization_vector="dnZ2dnZ2dnZ2dnZ2dnZ2dg==",
                only_metadata=True,
            )
        )

        assert isinstance(result, invoices.ExportHandle)
        assert result.reference_number == expected.referenceNumber
        assert result.aes_key == b"k" * 32
        assert result.iv == b"v" * 16
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == InvoiceRoutes.EXPORT
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request

    def test_get_export_status(
        self,
        invoices_client: InvoicesClient,
        fake_transport: FakeTransport,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        expected = inv_export_status_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = invoices_client.get_export_status(reference_number="export-ref")

        assert isinstance(result, invoices.InvoiceExportStatusResponse)
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == InvoiceRoutes.EXPORT_STATUS.format(
            referenceNumber="export-ref"
        )
