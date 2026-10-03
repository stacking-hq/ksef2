import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._core.exceptions import (
    ExceptionCode,
    KSeFApiError,
    KSeFExportTimeoutError,
    KSeFInvoiceDownloadTimeoutError,
    KSeFInvoiceQueryTimeoutError,
)
from ksef2._core.stores import CertificateStore
from ksef2._domain.models import invoices
from ksef2._infra.schema.api import spec
from ksef2._services.async_invoices import AsyncInvoicesService
from tests.unit.fakes.transport import AsyncFakeTransport


def _build_service(async_fake_transport: AsyncFakeTransport) -> AsyncInvoicesService:
    return AsyncInvoicesService(
        async_fake_transport,
        async_fake_transport,
        CertificateStore(),
    )


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
                    "url": "https://example.com/export/part-1?sig=secret",
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


def _invoice_package_with_part_name(part_name: str) -> invoices.InvoicePackage:
    return invoices.InvoicePackage.model_validate(
        {
            "invoice_count": 1,
            "size": 128,
            "parts": [
                {
                    "ordinal_number": 1,
                    "part_name": part_name,
                    "method": "GET",
                    "url": "https://example.com/export/part-1?sig=secret",
                    "part_size": 64,
                    "part_hash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                    "encrypted_part_size": 128,
                    "encrypted_part_hash": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=",
                    "expiration_date": datetime.now(timezone.utc),
                }
            ],
            "is_truncated": False,
        }
    )


def _not_processed_yet_error() -> KSeFApiError:
    return KSeFApiError(
        status_code=400,
        exception_code=ExceptionCode.NOT_PROCESSED_YET,
        message="not ready",
    )


class TestAsyncInvoicesService:
    def test_wait_for_invoice_download_retries_until_invoice_is_available(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        service = _build_service(async_fake_transport)
        download_invoice = AsyncMock(
            side_effect=[_not_processed_yet_error(), b"<Invoice />"]
        )

        with patch.object(service, "download_invoice", download_invoice):
            result = asyncio.run(
                service.wait_for_invoice_download(
                    ksef_number="ksef-123",
                    timeout=1.0,
                    poll_interval=0.0,
                )
            )

        assert result == b"<Invoice />"
        assert download_invoice.call_count == 2

    def test_wait_for_invoice_download_raises_on_timeout(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        service = _build_service(async_fake_transport)
        download_invoice = AsyncMock(side_effect=_not_processed_yet_error())

        with patch.object(service, "download_invoice", download_invoice):
            with pytest.raises(KSeFInvoiceDownloadTimeoutError):
                _ = asyncio.run(
                    service.wait_for_invoice_download(
                        ksef_number="ksef-123",
                        timeout=0.0,
                        poll_interval=0.0,
                    )
                )

    def test_wait_for_invoice_download_propagates_non_transient_errors(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        service = _build_service(async_fake_transport)
        bad_request = KSeFApiError(
            status_code=400,
            exception_code=ExceptionCode.VALIDATION_ERROR,
            message="invalid request",
        )
        download_invoice = AsyncMock(side_effect=bad_request)

        with patch.object(service, "download_invoice", download_invoice):
            with pytest.raises(KSeFApiError) as exc_info:
                _ = asyncio.run(
                    service.wait_for_invoice_download(
                        ksef_number="ksef-123",
                        timeout=1.0,
                        poll_interval=0.0,
                    )
                )

        assert exc_info.value.exception_code == ExceptionCode.VALIDATION_ERROR

    @pytest.mark.parametrize(
        ("part_name", "expected_name"),
        [
            ("../unsafe/subdir/part-1.zip.aes", "part-1.zip"),
            ("..\\unsafe\\subdir\\part-2.zip.aes", "part-2.zip"),
            ("../unsafe\\subdir/part-3.zip.aes", "part-3.zip"),
        ],
    )
    def test_fetch_package_sanitizes_part_name_and_removes_aes_suffix(
        self,
        part_name: str,
        expected_name: str,
        async_fake_transport: AsyncFakeTransport,
        tmp_path: Path,
    ) -> None:
        service = _build_service(async_fake_transport)
        package = _invoice_package_with_part_name(part_name)
        handle = invoices.ExportHandle(
            reference_number="ref",
            aes_key=b"0" * 32,
            iv=b"1" * 16,
        )
        async_fake_transport.responses.append(
            httpx.Response(
                status_code=200,
                content=b"encrypted",
                request=httpx.Request("GET", "https://example.com/export/part-1"),
            )
        )

        with (
            patch(
                "ksef2._services.async_invoices.decrypt_aes_cbc",
                return_value=b"decrypted",
            ),
            patch("ksef2._services.async_invoices.logger.info") as log_info,
        ):
            saved_files = asyncio.run(
                service.fetch_package(
                    package=package,
                    export=handle,
                    target_directory=tmp_path,
                )
            )

        assert saved_files == [tmp_path / expected_name]
        assert saved_files[0].read_bytes() == b"decrypted"
        assert not (tmp_path.parent / expected_name).exists()
        assert "sig=secret" not in repr(log_info.call_args_list)

    @pytest.mark.parametrize(
        "part_name", [".", "..", ".aes", ".hidden.zip.aes", "bad\x00.zip.aes"]
    )
    def test_fetch_package_rejects_invalid_part_names(
        self,
        part_name: str,
        async_fake_transport: AsyncFakeTransport,
        tmp_path: Path,
    ) -> None:
        service = _build_service(async_fake_transport)
        package = _invoice_package_with_part_name(part_name)
        handle = invoices.ExportHandle(
            reference_number="ref",
            aes_key=b"0" * 32,
            iv=b"1" * 16,
        )
        async_fake_transport.responses.append(
            httpx.Response(
                status_code=200,
                content=b"encrypted",
                request=httpx.Request("GET", "https://example.com/export/part-1"),
            )
        )

        with patch("ksef2._services.async_invoices.decrypt_aes_cbc", return_value=b"x"):
            with pytest.raises(ValueError, match="Invalid export package part name"):
                _ = asyncio.run(
                    service.fetch_package(
                        package=package,
                        export=handle,
                        target_directory=tmp_path,
                    )
                )

    def test_wait_for_invoices_returns_when_metadata_appears(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = _build_service(async_fake_transport)
        async_fake_transport.enqueue(
            inv_query_metadata_resp.build(invoices=[]).model_dump(mode="json")
        )
        async_fake_transport.enqueue(
            inv_query_metadata_resp.build().model_dump(mode="json")
        )

        result = asyncio.run(
            service.wait_for_invoices(
                filters=inv_export_filters.build(),
                timeout=1.0,
                poll_interval=0.0,
            )
        )

        assert result.invoices
        assert len(async_fake_transport.calls) == 2

    def test_wait_for_invoices_raises_on_timeout(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = _build_service(async_fake_transport)
        async_fake_transport.enqueue(
            inv_query_metadata_resp.build(invoices=[]).model_dump(mode="json")
        )

        with pytest.raises(KSeFInvoiceQueryTimeoutError):
            _ = asyncio.run(
                service.wait_for_invoices(
                    filters=inv_export_filters.build(),
                    timeout=0.0,
                    poll_interval=0.0,
                )
            )

    def test_wait_for_export_package_returns_when_parts_are_ready(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        service = _build_service(async_fake_transport)
        async_fake_transport.enqueue(
            inv_export_status_resp.build(package=None).model_dump(mode="json")
        )
        async_fake_transport.enqueue(
            inv_export_status_resp.build(package=_ready_export_package()).model_dump(
                mode="json"
            )
        )

        package = asyncio.run(
            service.wait_for_export_package(
                reference_number="export-ref",
                timeout=1.0,
                poll_interval=0.0,
            )
        )

        assert package.parts
        assert len(async_fake_transport.calls) == 2

    def test_wait_for_export_package_raises_on_timeout(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        service = _build_service(async_fake_transport)
        async_fake_transport.enqueue(
            inv_export_status_resp.build(package=None).model_dump(mode="json")
        )

        with pytest.raises(KSeFExportTimeoutError):
            _ = asyncio.run(
                service.wait_for_export_package(
                    reference_number="export-ref",
                    timeout=0.0,
                    poll_interval=0.0,
                )
            )
