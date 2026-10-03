"""search / download / export on the invoices service, sync and async."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._core.crypto import encrypt_invoice
from ksef2._core.exceptions import (
    ExceptionCode,
    KSeFApiError,
    KSeFExportFailedError,
    KSeFExportTimeoutError,
    KSeFInvoiceDownloadTimeoutError,
    KSeFInvoiceQueryTimeoutError,
)
from ksef2._domain.models.invoices import ExportHandle, InvoicesFilter
from ksef2._domain.models.pagination import InvoiceMetadataParams
from ksef2._infra.schema.api import spec
from tests.unit.flavors import Flavor
from tests.unit.payloads import (
    KSEF_1,
    KSEF_2,
    archive,
    metadata_page,
    package_status,
)

KEY = b"k" * 32
IV = b"v" * 16


def _filters() -> InvoicesFilter:
    return InvoicesFilter(
        role="seller",
        date_type="issue_date",
        date_from=datetime(2026, 1, 1, tzinfo=UTC),
        date_to=datetime(2026, 2, 1, tzinfo=UTC),
    )


class TestSearch:
    def test_iterating_follows_pages(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=1, has_more=True)
        )
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=2, has_more=False)
        )

        items = flavor.collect(service.search(_filters()))

        assert len(items) == 3
        assert len(flavor.transport.calls) == 2
        assert [
            (call.params or httpx.QueryParams())["pageOffset"]
            for call in flavor.transport.calls
        ] == [
            "0",
            "1",
        ]

    def test_search_is_lazy_and_pages_and_first_page_work(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        pager = service.search(_filters(), InvoiceMetadataParams(page_size=10))
        assert flavor.transport.calls == []

        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=2, has_more=True)
        )
        assert len(flavor.run(pager.first_page())) == 2
        assert len(flavor.transport.calls) == 1

        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=1, has_more=True)
        )
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=3, has_more=False)
        )
        assert [len(page) for page in flavor.collect(pager.pages())] == [1, 3]
        assert (flavor.transport.calls[1].params or httpx.QueryParams())[
            "pageSize"
        ] == "10"

    def test_wait_polls_until_an_invoice_is_indexed(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=0, has_more=False)
        )
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=1, has_more=False)
        )
        pager = service.search(_filters())

        assert flavor.run(pager.wait(timeout=1.0, poll_interval=0.0)) is pager
        assert len(flavor.transport.calls) == 2

    def test_wait_times_out_with_the_invoice_query_error(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=0, has_more=False)
        )

        with pytest.raises(KSeFInvoiceQueryTimeoutError):
            flavor.run(service.search(_filters()).wait(timeout=0.0, poll_interval=0.0))


def _not_processed_yet() -> KSeFApiError:
    return KSeFApiError(
        status_code=400,
        exception_code=ExceptionCode.NOT_PROCESSED_YET,
        message="not processed",
    )


class TestDownload:
    def test_downloads_once_by_default(self, flavor: Flavor) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(content=b"<Invoice />")

        assert flavor.run(service.download(KSEF_1)) == b"<Invoice />"
        assert len(flavor.transport.calls) == 1

    def test_does_not_poll_without_a_timeout(self, flavor: Flavor) -> None:
        service = flavor.invoices_service()
        calls: list[str] = []

        async def _async_download(*, ksef_number: str) -> bytes:
            calls.append(ksef_number)
            raise _not_processed_yet()

        def _sync_download(*, ksef_number: str) -> bytes:
            calls.append(ksef_number)
            raise _not_processed_yet()

        with patch.object(
            service._client,
            "download_invoice",
            _async_download if flavor.is_async else _sync_download,
        ):
            with pytest.raises(KSeFApiError):
                flavor.run(service.download(KSEF_1))

        assert calls == [KSEF_1]

    def test_polls_until_available_when_a_timeout_is_given(
        self, flavor: Flavor
    ) -> None:
        service = flavor.invoices_service()
        results: list[Any] = [_not_processed_yet(), b"<Invoice />"]

        async def _async_download(*, ksef_number: str) -> bytes:
            del ksef_number
            result = results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        def _sync_download(*, ksef_number: str) -> bytes:
            return flavor.run(_async_download(ksef_number=ksef_number))

        with patch.object(
            service._client,
            "download_invoice",
            _async_download if flavor.is_async else _sync_download,
        ):
            xml = flavor.run(service.download(KSEF_1, timeout=1.0, poll_interval=0.0))

        assert xml == b"<Invoice />"
        assert results == []

    def test_raises_a_download_timeout(self, flavor: Flavor) -> None:
        service = flavor.invoices_service()

        async def _async_download(*, ksef_number: str) -> bytes:
            del ksef_number
            raise _not_processed_yet()

        def _sync_download(*, ksef_number: str) -> bytes:
            raise _not_processed_yet()

        with patch.object(
            service._client,
            "download_invoice",
            _async_download if flavor.is_async else _sync_download,
        ):
            with pytest.raises(KSeFInvoiceDownloadTimeoutError):
                flavor.run(service.download(KSEF_1, timeout=0.0, poll_interval=0.0))


def _export_job(flavor: Flavor) -> Any:
    service = flavor.invoices_service()
    handle = ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)

    async def _async_schedule(**_: Any) -> ExportHandle:
        return handle

    def _sync_schedule(**_: Any) -> ExportHandle:
        return handle

    with patch.object(
        service,
        "_schedule_export",
        _async_schedule if flavor.is_async else _sync_schedule,
    ):
        return flavor.run(service.export(_filters()))


class TestExport:
    def test_wait_downloads_decrypts_joins_and_unzips(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        job = _export_job(flavor)
        payload = archive()
        # KSeF encrypts each part on its own; the SDK decrypts and then joins them.
        first, second = payload[: len(payload) // 2], payload[len(payload) // 2 :]
        flavor.transport.enqueue(package_status(inv_export_status_resp, 100))
        flavor.transport.enqueue(package_status(inv_export_status_resp, 200, 2))
        flavor.transport.enqueue(content=encrypt_invoice(first, key=KEY, iv=IV))
        flavor.transport.enqueue(content=encrypt_invoice(second, key=KEY, iv=IV))

        exported = flavor.run(job.wait(timeout=1.0, poll_interval=0.0))

        assert exported.archive == payload
        assert list(exported.invoices()) == [(KSEF_1, b"<one />"), (KSEF_2, b"<two />")]
        assert exported.metadata == []
        assert exported.package is not None
        assert exported.package.invoice_count == 2
        assert job.reference_number == "export-ref"

    def test_wait_raises_when_ksef_fails_the_export(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        job = _export_job(flavor)
        flavor.transport.enqueue(package_status(inv_export_status_resp, 415))

        with pytest.raises(KSeFExportFailedError) as exc_info:
            flavor.run(job.wait(timeout=1.0, poll_interval=0.0))

        assert exc_info.value.export_status_code == 415
        assert exc_info.value.reference_number == "export-ref"

    def test_wait_raises_when_the_export_expired(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        job = _export_job(flavor)
        flavor.transport.enqueue(package_status(inv_export_status_resp, 210))

        with pytest.raises(KSeFExportFailedError):
            flavor.run(job.wait(timeout=1.0, poll_interval=0.0))

    def test_wait_times_out(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        job = _export_job(flavor)
        flavor.transport.enqueue(package_status(inv_export_status_resp, 100))

        with pytest.raises(KSeFExportTimeoutError):
            flavor.run(job.wait(timeout=0.0, poll_interval=0.0))

    def test_an_export_without_invoices_is_empty(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        job = _export_job(flavor)
        flavor.transport.enqueue(package_status(inv_export_status_resp, 200))

        exported = flavor.run(job.wait(timeout=1.0, poll_interval=0.0))

        assert exported.archive == b""
        assert list(exported.invoices()) == []

    def test_get_status_does_not_wait(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        job = _export_job(flavor)
        flavor.transport.enqueue(package_status(inv_export_status_resp, 100))

        assert flavor.run(job.get_status()).status.code == 100
        assert len(flavor.transport.calls) == 1
