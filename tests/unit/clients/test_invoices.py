from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from polyfactory import BaseFactory
import pytest
from pydantic import ValidationError

from ksef2.clients.invoices import InvoicesClient
from ksef2.core.routes import InvoiceRoutes
from ksef2.domain.models import invoices
from ksef2.domain.models.session import FormSchema
from ksef2.domain.models.pagination import InvoiceMetadataParams
from ksef2.infra.mappers.invoices import to_spec
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport
from tests.unit.helpers import VALID_PUBLIC_KEY_ID


def _with_metadata_page_state(
    response: spec.QueryInvoicesMetadataResponse,
    *,
    has_more: bool,
    is_truncated: bool,
    permanent_storage_date: datetime | None = None,
) -> spec.QueryInvoicesMetadataResponse:
    if permanent_storage_date is None:
        return response.model_copy(
            update={"hasMore": has_more, "isTruncated": is_truncated}
        )

    invoice = response.invoices[0].model_copy(
        update={"permanentStorageDate": permanent_storage_date}
    )
    return response.model_copy(
        update={
            "hasMore": has_more,
            "isTruncated": is_truncated,
            "invoices": [invoice],
        }
    )


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

    def test_invoice_metadata_params_allow_documented_page_size_limit(self) -> None:
        params = InvoiceMetadataParams(page_size=250)

        assert params.to_query_params().get("pageSize") == 250

        with pytest.raises(ValidationError):
            _ = InvoiceMetadataParams(page_size=251)

    def test_query_metadata_pages_follows_has_more(
        self,
        invoices_client: InvoicesClient,
        fake_transport: FakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        first = _with_metadata_page_state(
            inv_query_metadata_resp.build(),
            has_more=True,
            is_truncated=False,
        )
        second = _with_metadata_page_state(
            inv_query_metadata_resp.build(),
            has_more=False,
            is_truncated=False,
        )
        fake_transport.enqueue(first.model_dump(mode="json"))
        fake_transport.enqueue(second.model_dump(mode="json"))

        pages = list(
            invoices_client.query_metadata_pages(
                filters=inv_export_filters.build(),
                params=InvoiceMetadataParams(page_size=250),
            )
        )

        assert len(pages) == 2
        assert len(fake_transport.calls) == 2
        assert fake_transport.calls[0].params is not None
        assert fake_transport.calls[0].params["pageOffset"] == "0"
        assert fake_transport.calls[0].params["pageSize"] == "250"
        assert fake_transport.calls[1].params is not None
        assert fake_transport.calls[1].params["pageOffset"] == "1"
        assert fake_transport.calls[1].params["pageSize"] == "250"

    @pytest.mark.parametrize(
        ("sort_order", "narrows_from"),
        [
            ("asc", True),
            ("desc", False),
        ],
    )
    def test_query_metadata_pages_resets_offset_and_narrows_truncated_range(
        self,
        sort_order: invoices.SortOrder,
        narrows_from: bool,
        invoices_client: InvoicesClient,
        fake_transport: FakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        boundary = datetime(2026, 1, 3, 13, 45, tzinfo=timezone.utc)
        first = _with_metadata_page_state(
            inv_query_metadata_resp.build(),
            has_more=True,
            is_truncated=True,
            permanent_storage_date=boundary,
        )
        second = _with_metadata_page_state(
            inv_query_metadata_resp.build(),
            has_more=False,
            is_truncated=False,
        )
        fake_transport.enqueue(first.model_dump(mode="json"))
        fake_transport.enqueue(second.model_dump(mode="json"))
        filters = inv_export_filters.build(date_type="permanent_storage")

        pages = list(
            invoices_client.query_metadata_pages(
                filters=filters,
                params=InvoiceMetadataParams(
                    page_size=250,
                    page_offset=39,
                    sort_order=sort_order,
                ),
            )
        )

        assert len(pages) == 2
        assert len(fake_transport.calls) == 2
        first_call, second_call = fake_transport.calls
        assert first_call.params is not None
        assert first_call.params["pageOffset"] == "39"
        assert second_call.params is not None
        assert second_call.params["pageOffset"] == "0"
        assert second_call.json is not None
        second_request = spec.InvoiceQueryFilters.model_validate(second_call.json)
        if narrows_from:
            assert second_request.dateRange.from_ == boundary
        else:
            assert second_request.dateRange.to == boundary

    def test_all_metadata_yields_items_from_all_pages(
        self,
        invoices_client: InvoicesClient,
        fake_transport: FakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        first = _with_metadata_page_state(
            inv_query_metadata_resp.build(),
            has_more=True,
            is_truncated=False,
        )
        second = _with_metadata_page_state(
            inv_query_metadata_resp.build(),
            has_more=False,
            is_truncated=False,
        )
        fake_transport.enqueue(first.model_dump(mode="json"))
        fake_transport.enqueue(second.model_dump(mode="json"))

        metadata = list(
            invoices_client.all_metadata(
                filters=inv_export_filters.build(),
                params=InvoiceMetadataParams(page_size=250),
            )
        )

        assert len(metadata) == len(first.invoices) + len(second.invoices)
        assert len(fake_transport.calls) == 2

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
            encryption_public_key_id=VALID_PUBLIC_KEY_ID,
            only_metadata=True,
        )
        expected_request = to_spec(
            invoices.ExportInvoicesPayload(
                filter=filters,
                encrypted_symmetric_key="ZW5jLWtleQ==",
                initialization_vector="dnZ2dnZ2dnZ2dnZ2dnZ2dg==",
                public_key_id=VALID_PUBLIC_KEY_ID,
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
