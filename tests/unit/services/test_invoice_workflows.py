"""search / download / export on the invoices service, sync and async."""

import json
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._core.crypto import encrypt_invoice
from ksef2._core.exceptions import (
    ExceptionCode,
    KSeFApiError,
    KSeFArgumentError,
    KSeFMetadataPaginationError,
    KSeFExportFailedError,
    KSeFExportTimeoutError,
    KSeFInvoiceDownloadTimeoutError,
    KSeFInvoiceQueryTimeoutError,
)
from ksef2._domain.models.invoices import ExportHandle, InvoicesFilter
from ksef2._domain.models.pagination import InvoiceMetadataParams
from ksef2._domain.models.session import FormSchema
from ksef2._infra.schema.api import spec
from ksef2.clients import ExportedInvoices
from tests.unit.fakes.transport import RecordedCall
from tests.unit.support.flavors import Flavor
from tests.unit.support.payloads import (
    InvoiceMetadataFactory,
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
        # Both flavours return the same class and support restoring archive bytes.
        assert type(exported) is ExportedInvoices
        restored = ExportedInvoices.from_archive(exported.archive)
        assert list(restored.invoices()) == [(KSEF_1, b"<one />"), (KSEF_2, b"<two />")]
        assert restored.metadata == []
        assert restored.package is None

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


def _row(boundary: str) -> dict[str, object]:
    """One deterministic metadata row whose boundary dates are all the same instant.

    Setting issue, invoicing and permanent-storage dates together keeps the fixtures
    readable for every ``date_type`` the search follows.
    """
    return InvoiceMetadataFactory.build(
        ksefNumber=f"{KSEF_1[:-2]}{boundary[8:10]}",
        issueDate=date.fromisoformat(boundary[:10]),
        invoicingDate=datetime.fromisoformat(boundary),
        permanentStorageDate=datetime.fromisoformat(boundary),
        acquisitionDate=datetime.fromisoformat(boundary),
    ).model_dump(mode="json")


def _boundary_page(
    factory: BaseFactory[spec.QueryInvoicesMetadataResponse],
    *,
    has_more: bool,
    truncated: bool,
    boundaries: list[str],
) -> dict[str, object]:
    """A metadata page carrying the given boundary instants."""
    return factory.build(
        hasMore=has_more,
        isTruncated=truncated,
        permanentStorageHwmDate=None,
        invoices=[_row(boundary) for boundary in boundaries],
    ).model_dump(mode="json")


def _request_body(call: RecordedCall) -> dict[str, object]:
    """Return the JSON body one recorded metadata request sent."""
    body = call.json
    assert body is not None
    return body


def _request_date_range(call: RecordedCall) -> dict[str, object]:
    """Return the ``dateRange`` object one recorded metadata request sent."""
    date_range = _request_body(call)["dateRange"]
    assert isinstance(date_range, dict)
    return date_range


def _request_dates(call: RecordedCall) -> tuple[str, str | None]:
    """Return the date range one recorded metadata request sent."""
    date_range = _request_date_range(call)
    date_to = date_range.get("to")
    assert date_to is None or isinstance(date_to, str)
    return str(date_range["from"]), date_to


def _request_offset(call: RecordedCall) -> str:
    params = call.params or httpx.QueryParams()
    return str(params["pageOffset"])


_SEARCH_DATE_TYPES = ["issue_date", "invoicing_date", "permanent_storage"]

# Where a search truncated at 2026-02-05T10:00Z, the next request starts (asc) or ends
# (desc). Issue dates are calendar dates, so the SDK reads the day's start in Warsaw.
_TRUNCATION_REQUEST_DATE = {
    "issue_date": "2026-02-04T23:00:00Z",
    "invoicing_date": "2026-02-05T10:00:00Z",
    "permanent_storage": "2026-02-05T10:00:00Z",
}

# Run in a fresh interpreter: it rebuilds the search from scratch and resumes only from
# the cursor in argv, which proves the cursor carries no process-local state. The
# rebuilt filters leave out ``date_to``, which defaults to the moment they are built.
_RESUME_CHILD = """
import json
import sys

from ksef2._domain.models.invoices import InvoicesFilter
from ksef2._domain.models.pagination import InvoiceMetadataParams
from tests.unit.factories.invoices import QueryInvoicesMetadataResponseFactory
from tests.unit.support.flavors import Flavor
from tests.unit.services.test_invoice_workflows import _boundary_page

flavor = Flavor("sync")
service = flavor.invoices_service()
flavor.transport.enqueue(
    _boundary_page(
        QueryInvoicesMetadataResponseFactory,
        has_more=False,
        truncated=False,
        boundaries=["2026-02-02T09:00:00+00:00"],
    )
)
page = service.search(
    InvoicesFilter(
        role="seller",
        date_type="issue_date",
        date_from="2026-01-01T00:00:00+00:00",
    ),
    InvoiceMetadataParams(page_size=15),
).page(sys.argv[1])
call = flavor.transport.calls[0]
print(
    json.dumps(
        {
            "page_offset": (call.params or __import__("httpx").QueryParams())["pageOffset"],
            "page_size": (call.params or __import__("httpx").QueryParams())["pageSize"],
            "date_from": call.json["dateRange"]["from"],
            "count": len(page.items),
            "next_cursor": page.next_cursor,
        }
    )
)
"""


class TestSearchCursors:
    @pytest.mark.parametrize("sort_order", ["asc", "desc"])
    @pytest.mark.parametrize("date_type", _SEARCH_DATE_TYPES)
    def test_cursor_resumes_across_truncation(
        self,
        flavor: Flavor,
        sort_order: str,
        date_type: str,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        filters = InvoicesFilter(
            role="seller",
            date_type=date_type,  # pyright: ignore[reportArgumentType]
            date_from=datetime(2026, 1, 1, tzinfo=UTC),
            date_to=datetime(2026, 3, 1, tzinfo=UTC),
        )
        params = InvoiceMetadataParams(page_size=10, sort_order=sort_order)  # pyright: ignore[reportArgumentType]
        truncated_at = "2026-02-05T10:00:00+00:00"
        service = flavor.invoices_service()
        pager = service.search(filters, params)

        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=True,
                boundaries=["2026-01-20T09:00:00+00:00", truncated_at],
            )
        )
        first = flavor.run(pager.page(None))

        assert len(first.items) == 2
        assert first.next_cursor is not None

        # The next request narrows the range at the boundary and restarts the offset.
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=False,
                boundaries=["2026-02-06T09:00:00+00:00"],
            )
        )
        resumed = flavor.run(service.search(filters, params).page(first.next_cursor))

        assert len(flavor.transport.calls) == 2
        boundary = _TRUNCATION_REQUEST_DATE[date_type]
        original_from = "2026-01-01T00:00:00Z"
        original_to = "2026-03-01T00:00:00Z"
        narrowed = _request_dates(flavor.transport.calls[1])
        if sort_order == "asc":
            assert narrowed == (boundary, original_to)
        else:
            assert narrowed == (original_from, boundary)
        assert _request_offset(flavor.transport.calls[1]) == "0"
        assert resumed.next_cursor is not None

        # One more page advances by offset without losing the narrowed range.
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=False,
                truncated=False,
                boundaries=["2026-02-07T09:00:00+00:00"],
            )
        )
        last = flavor.run(service.search(filters, params).page(resumed.next_cursor))

        assert last.next_cursor is None
        assert _request_offset(flavor.transport.calls[2]) == "1"
        assert _request_dates(flavor.transport.calls[2]) == narrowed

    @pytest.mark.parametrize(
        "date_type", _SEARCH_DATE_TYPES, ids=lambda date_type: str(date_type)
    )
    def test_cursor_keeps_previous_boundary_and_rejects_stall(
        self,
        flavor: Flavor,
        date_type: str,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        filters = InvoicesFilter(
            role="seller",
            date_type=date_type,  # pyright: ignore[reportArgumentType]
            date_from=datetime(2026, 1, 1, tzinfo=UTC),
            date_to=datetime(2026, 3, 1, tzinfo=UTC),
        )
        stalled_at = "2026-02-05T10:00:00+00:00"
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=True,
                boundaries=[stalled_at],
            )
        )
        first = flavor.run(service.search(filters).page(None))

        assert first.next_cursor is not None
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=True,
                boundaries=[stalled_at, stalled_at],
            )
        )

        # The second truncation lands on the boundary the cursor already carried. Its
        # invoices are still returned, and the error waits behind the page's cursor.
        second = flavor.run(service.search(filters).page(first.next_cursor))
        assert len(second.items) == 2
        assert second.next_cursor is not None
        with pytest.raises(KSeFMetadataPaginationError, match="did not advance"):
            flavor.run(service.search(filters).page(second.next_cursor))
        assert len(flavor.transport.calls) == 2

    @pytest.mark.parametrize(
        "date_type", _SEARCH_DATE_TYPES, ids=lambda date_type: str(date_type)
    )
    def test_resumed_midnight_truncation_stall_is_rejected(
        self,
        flavor: Flavor,
        date_type: str,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        """A search that truncates twice on the same midnight still reports the stall.

        Midnight is the instant at which a stored boundary can be read back as the other
        kind of value: a timestamp that looks exactly like the calendar date under it, and
        which then never compares equal to the next timestamp at that same instant. Reading
        the boundary back as its own kind is what keeps this search from paging forever.
        """
        filters = InvoicesFilter(
            role="seller",
            date_type=date_type,  # pyright: ignore[reportArgumentType]
            date_from=datetime(2026, 1, 1, tzinfo=UTC),
            date_to=datetime(2026, 3, 1, tzinfo=UTC),
        )
        stalled_at = "2026-02-05T00:00:00+00:00"
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=True,
                boundaries=[stalled_at],
            )
        )
        first = flavor.run(service.search(filters).page(None))

        assert first.next_cursor is not None
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=True,
                boundaries=[stalled_at, stalled_at],
            )
        )

        second = flavor.run(service.search(filters).page(first.next_cursor))
        assert second.next_cursor is not None
        with pytest.raises(KSeFMetadataPaginationError, match="did not advance"):
            flavor.run(service.search(filters).page(second.next_cursor))
        assert len(flavor.transport.calls) == 2

    def test_cursor_keeps_filters_and_params_after_restart(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        filters = InvoicesFilter(
            role="buyer",
            date_type="invoicing_date",
            date_from=datetime(2026, 1, 1, tzinfo=UTC),
            date_to=datetime(2026, 3, 1, tzinfo=UTC),
            invoice_number="FV/42/2026",
            currency_codes=["PLN"],
        )
        params = InvoiceMetadataParams(page_size=20, page_offset=3, sort_order="desc")
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=False,
                boundaries=["2026-02-01T09:00:00+00:00"],
            )
        )
        first = flavor.run(service.search(filters, params).page(None))

        assert _request_offset(flavor.transport.calls[0]) == "3"
        assert first.next_cursor is not None
        cursor = str(
            json.loads(json.dumps({"cursor": str(first.next_cursor)}))["cursor"]
        )

        # A search rebuilt after a restart resumes the original request, whatever page
        # offset it was rebuilt with.
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=False,
                truncated=False,
                boundaries=["2026-02-02T09:00:00+00:00"],
            )
        )
        resumed = flavor.run(
            service.search(
                filters,
                InvoiceMetadataParams(page_size=20, page_offset=99, sort_order="desc"),
            ).page(cursor)
        )

        assert resumed.next_cursor is None
        assert len(flavor.transport.calls) == 2
        resumed_call = flavor.transport.calls[1]
        assert _request_offset(resumed_call) == "4"
        assert (resumed_call.params or httpx.QueryParams())["pageSize"] == "20"
        body = _request_body(resumed_call)
        assert body["invoiceNumber"] == "FV/42/2026"
        assert body["subjectType"] == "Subject2"
        assert _request_date_range(resumed_call)["dateType"] == "Invoicing"

    def test_cursor_keeps_invoice_schema_after_restart(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        filters = InvoicesFilter(
            role="buyer",
            date_type="invoicing_date",
            date_from=datetime(2026, 1, 1, tzinfo=UTC),
            invoice_schema=FormSchema.PEF3,
        )
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=False,
                boundaries=["2026-02-01T09:00:00+00:00"],
            )
        )
        first = flavor.run(service.search(filters).page(None))

        assert len(flavor.transport.calls) == 1
        assert first.next_cursor is not None
        cursor = str(
            json.loads(json.dumps({"cursor": str(first.next_cursor)}))["cursor"]
        )
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=False,
                truncated=False,
                boundaries=["2026-02-02T09:00:00+00:00"],
            )
        )

        resumed = flavor.run(service.search(filters).page(cursor))

        assert resumed.next_cursor is None
        assert len(flavor.transport.calls) == 2
        assert _request_body(flavor.transport.calls[1])["formType"] == "PEF"

    @pytest.mark.parametrize(
        "other",
        [
            lambda f: (f.model_copy(update={"invoice_number": "FV/1/2026"}), None),
            lambda f: (f.model_copy(update={"role": "buyer"}), None),
            lambda f: (f.model_copy(update={"date_type": "invoicing_date"}), None),
            lambda f: (
                f.model_copy(update={"date_from": datetime(2025, 1, 1, tzinfo=UTC)}),
                None,
            ),
            lambda f: (f, InvoiceMetadataParams(page_size=50)),
            lambda f: (f, InvoiceMetadataParams(sort_order="desc")),
        ],
        ids=["number", "role", "date-type", "date-from", "page-size", "sort-order"],
    )
    def test_cursor_from_another_search_is_rejected_before_any_request(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
        other: Any,
    ) -> None:
        filters = _filters()
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=False,
                boundaries=["2026-02-01T09:00:00+00:00"],
            )
        )
        first = flavor.run(service.search(filters).page(None))
        assert first.next_cursor is not None

        other_filters, other_params = other(filters)
        with pytest.raises(KSeFArgumentError, match="different search") as caught:
            flavor.run(
                service.search(other_filters, other_params).page(first.next_cursor)
            )

        assert first.next_cursor not in str(caught.value)
        assert len(flavor.transport.calls) == 1

    def test_empty_truncated_page_is_returned_then_reported(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        filters = _filters()
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp, has_more=True, truncated=True, boundaries=[]
            )
        )

        page = flavor.run(service.search(filters).page(None))

        assert page.items == []
        assert page.next_cursor is not None
        with pytest.raises(KSeFMetadataPaginationError, match="without invoices"):
            flavor.run(service.search(filters).page(page.next_cursor))
        assert len(flavor.transport.calls) == 1

    def test_cursor_empty_terminal_page(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        pager = service.search(_filters())
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=False,
                boundaries=["2026-02-01T09:00:00+00:00"],
            )
        )
        first = flavor.run(pager.page(None))

        assert first.next_cursor is not None
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp, has_more=False, truncated=False, boundaries=[]
            )
        )
        empty = flavor.run(service.search(_filters()).page(first.next_cursor))

        assert empty.items == []
        assert empty.next_cursor is None
        assert _request_offset(flavor.transport.calls[1]) == "1"

    def test_cursor_page_matches_traversal_page_by_page(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        filters = _filters()
        pages = [
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=False,
                boundaries=["2026-02-01T09:00:00+00:00", "2026-02-02T09:00:00+00:00"],
            ),
            _boundary_page(
                inv_query_metadata_resp,
                has_more=False,
                truncated=False,
                boundaries=["2026-02-03T09:00:00+00:00"],
            ),
        ]
        service = flavor.invoices_service()
        for page in pages:
            flavor.transport.enqueue(page)
        traversal = flavor.collect(service.search(filters).pages())

        cursor: str | None = None
        for index, walked in enumerate(traversal):
            flavor.transport.clear()
            flavor.transport.enqueue(pages[index])
            page = flavor.run(service.search(filters).page(cursor))

            assert [item.ksef_number for item in page.items] == [
                item.ksef_number for item in walked
            ]
            assert len(flavor.transport.calls) == 1
            cursor = page.next_cursor if index == 0 else None
            if index == 0:
                assert cursor is not None
        assert cursor is None

    def test_cursor_survives_a_fresh_interpreter(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        filters = _filters()
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            _boundary_page(
                inv_query_metadata_resp,
                has_more=True,
                truncated=False,
                boundaries=["2026-02-01T09:00:00+00:00"],
            )
        )
        first = flavor.run(
            service.search(filters, InvoiceMetadataParams(page_size=15)).page(None)
        )

        assert first.next_cursor is not None
        completed = subprocess.run(
            [sys.executable, "-c", _RESUME_CHILD, str(first.next_cursor)],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[3],
        )
        result = json.loads(completed.stdout)

        assert result["page_offset"] == "1"
        assert result["page_size"] == "15"
        assert result["count"] == 1
        assert result["next_cursor"] is None
        assert result["date_from"] == "2026-01-01T00:00:00Z"


@pytest.mark.parametrize("factory", ["direct", "buyer", "seller"])
def test_resume_checks_explicit_end_date(
    flavor: Flavor,
    inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    factory: str,
) -> None:
    def build(end: datetime | None = None) -> InvoicesFilter:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        if factory == "buyer":
            return InvoicesFilter.for_buyer(date_from=start, date_to=end)
        if factory == "seller":
            return InvoicesFilter.for_seller(date_from=start, date_to=end)
        if end is None:
            return InvoicesFilter(
                role="seller", date_type="issue_date", date_from=start
            )
        return InvoicesFilter(
            role="seller", date_type="issue_date", date_from=start, date_to=end
        )

    service = flavor.invoices_service()
    original = build(datetime(2026, 2, 1, tzinfo=UTC))
    flavor.transport.enqueue(
        metadata_page(inv_query_metadata_resp, count=1, has_more=True)
    )
    first = flavor.run(service.search(original).page())
    assert first.next_cursor is not None
    with pytest.raises(KSeFArgumentError, match="different search"):
        flavor.run(
            service.search(build(datetime(2026, 3, 1, tzinfo=UTC))).page(
                first.next_cursor
            )
        )
    assert len(flavor.transport.calls) == 1

    # An omitted upper bound after restart resumes the saved bound, not today's date.
    flavor.transport.enqueue(
        metadata_page(inv_query_metadata_resp, count=1, has_more=True)
    )
    second = flavor.run(service.search(build()).page(first.next_cursor))
    assert second.next_cursor is not None
    assert (
        _request_date_range(flavor.transport.calls[-1])["to"] == "2026-02-01T00:00:00Z"
    )

    # Saving and reloading the original filters makes the end date explicit again.
    restored = InvoicesFilter.model_validate_json(original.model_dump_json())
    flavor.transport.enqueue(
        metadata_page(inv_query_metadata_resp, count=1, has_more=False)
    )
    flavor.run(service.search(restored).page(second.next_cursor))
    assert len(flavor.transport.calls) == 3
