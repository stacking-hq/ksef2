from datetime import datetime, timezone

import pytest
from polyfactory import BaseFactory

from ksef2.core.exceptions import KSeFExportTimeoutError, KSeFInvoiceQueryTimeoutError
from ksef2.core.stores import CertificateStore
from ksef2.domain.models import invoices
from ksef2.infra.schema.api import spec
from ksef2.services.invoices import InvoicesService
from tests.unit.fakes.transport import FakeTransport


def _build_service(fake_transport: FakeTransport) -> InvoicesService:
    return InvoicesService(fake_transport, CertificateStore())


def _ready_export_package() -> spec.InvoicePackage:
    return spec.InvoicePackage.model_validate(
        {
            "invoiceCount": 1,
            "size": 128,
            "parts": [
                {
                    "ordinalNumber": 1,
                    "partName": "part-1.zip.enc",
                    "method": "GET",
                    "url": "https://example.com/export/part-1",
                    "partSize": 64,
                    "partHash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                    "encryptedPartSize": 128,
                    "encryptedPartHash": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=",
                    "expirationDate": datetime.now(timezone.utc),
                }
            ],
            "isTruncated": False,
        }
    )


class TestInvoicesService:
    def test_wait_for_invoices_returns_when_metadata_appears(
        self,
        fake_transport: FakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = _build_service(fake_transport)
        filters = inv_export_filters.build()
        fake_transport.enqueue(
            inv_query_metadata_resp.build(invoices=[]).model_dump(mode="json")
        )
        fake_transport.enqueue(inv_query_metadata_resp.build().model_dump(mode="json"))

        result = service.wait_for_invoices(
            filters=filters,
            timeout=1.0,
            poll_interval=0.0,
        )

        assert result.invoices
        assert len(fake_transport.calls) == 2

    def test_wait_for_invoices_raises_on_timeout(
        self,
        fake_transport: FakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = _build_service(fake_transport)
        fake_transport.enqueue(
            inv_query_metadata_resp.build(invoices=[]).model_dump(mode="json")
        )

        with pytest.raises(KSeFInvoiceQueryTimeoutError):
            _ = service.wait_for_invoices(
                filters=inv_export_filters.build(),
                timeout=0.0,
                poll_interval=0.0,
            )

    def test_wait_for_export_package_returns_when_parts_are_ready(
        self,
        fake_transport: FakeTransport,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        service = _build_service(fake_transport)
        fake_transport.enqueue(
            inv_export_status_resp.build(package=None).model_dump(mode="json")
        )
        fake_transport.enqueue(
            inv_export_status_resp.build(package=_ready_export_package()).model_dump(
                mode="json"
            )
        )

        package = service.wait_for_export_package(
            reference_number="export-ref",
            timeout=1.0,
            poll_interval=0.0,
        )

        assert package.parts
        assert len(fake_transport.calls) == 2

    def test_wait_for_export_package_raises_on_timeout(
        self,
        fake_transport: FakeTransport,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        service = _build_service(fake_transport)
        fake_transport.enqueue(
            inv_export_status_resp.build(package=None).model_dump(mode="json")
        )

        with pytest.raises(KSeFExportTimeoutError):
            _ = service.wait_for_export_package(
                reference_number="export-ref",
                timeout=0.0,
                poll_interval=0.0,
            )
