"""Public invoice search response access over local HTTP mocks."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
import re

import httpx
import pytest
from respx import MockRouter
from pydantic import SecretStr

from ksef2 import AsyncClient, Client, Environment, KSeFValidationError
from ksef2.clients import AsyncAuthenticatedClient, AuthenticatedClient
from ksef2.models import (
    AuthenticationResumeState,
    InvoiceMetadataParams,
    InvoicesFilter,
    QueryInvoicesMetadataResponse,
    InvoiceMetadata,
)
from tests.unit.flavors import Flavor

HWM = datetime(2026, 6, 25, 9, tzinfo=UTC)
ROW = {
    "ksefNumber": "5261040828-20260625-ABCDEF-123456-7A",
    "invoiceNumber": "FV/42/2026",
    "issueDate": "2026-06-25",
    "invoicingDate": "2026-06-25T08:00:00Z",
    "acquisitionDate": "2026-06-25T08:00:00Z",
    "permanentStorageDate": "2026-06-25T08:00:00Z",
    "seller": {"nip": "5261040828", "name": "Mock seller"},
    "buyer": {
        "identifier": {"type": "Nip", "value": "5261040829"},
        "name": "Mock buyer",
    },
    "netAmount": 100,
    "grossAmount": 123,
    "vatAmount": 23,
    "currency": "PLN",
    "invoicingMode": "Online",
    "invoiceType": "Vat",
    "formCode": {"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"},
    "isSelfInvoicing": False,
    "hasAttachment": False,
    "invoiceHash": "A" * 44,
}
FILTERS = InvoicesFilter.for_buyer(
    date_type="permanent_storage",
    date_from="2026-06-25T00:00:00Z",
    date_to="2026-06-26T00:00:00Z",
    restrict_to_permanent_storage_hwm_date=True,
)


@pytest.fixture
def auth(
    flavor: Flavor, respx_mock: MockRouter
) -> Iterator[AuthenticatedClient | AsyncAuthenticatedClient]:
    # Synthetic credentials stay in memory; the HTTP mock rejects unregistered calls.
    state = AuthenticationResumeState(
        access_token=SecretStr("mock-access-token"),
        access_token_valid_until=datetime(2099, 1, 1, tzinfo=UTC),
        refresh_token=SecretStr("mock-refresh-token"),
        refresh_token_valid_until=datetime(2099, 1, 1, tzinfo=UTC),
    )
    client = (
        AsyncClient(Environment.TEST) if flavor.is_async else Client(Environment.TEST)
    )
    try:
        yield client.authentication.resume(state)
    finally:
        _ = flavor.run(
            client.aclose() if isinstance(client, AsyncClient) else client.close()
        )


def test_empty_first_response_preserves_checkpoint(
    auth: AuthenticatedClient | AsyncAuthenticatedClient,
    flavor: Flavor,
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(
        "https://api-test.ksef.mf.gov.pl/v2/invoices/query/metadata"
    ).respond(
        200,
        json={
            "hasMore": False,
            "isTruncated": False,
            "invoices": [],
            "permanentStorageHwmDate": HWM.isoformat(),
        },
    )
    pager = auth.invoices.search(
        FILTERS, InvoiceMetadataParams(page_size=10, page_offset=2, sort_order="asc")
    )
    assert route.call_count == 0
    page = flavor.run(pager.first_response())
    assert isinstance(page, QueryInvoicesMetadataResponse)
    assert page.invoices == []
    assert page.permanent_storage_hwm_date == HWM
    assert page.has_more is False
    assert page.is_truncated is False
    assert route.call_count == 1
    request = route.calls.last.request
    assert dict(request.url.params) == {
        "pageSize": "10",
        "pageOffset": "2",
        "sortOrder": "Asc",
    }
    assert b'"restrictToPermanentStorageHwmDate":true' in request.content


@pytest.mark.parametrize("truncated", [False, True])
def test_responses_preserve_each_page_and_restart(
    truncated: bool,
    auth: AuthenticatedClient | AsyncAuthenticatedClient,
    flavor: Flavor,
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(
        "https://api-test.ksef.mf.gov.pl/v2/invoices/query/metadata"
    )
    route.side_effect = [
        httpx.Response(
            200,
            json={
                "hasMore": True,
                "isTruncated": truncated,
                "invoices": [ROW],
                "permanentStorageHwmDate": HWM.isoformat(),
            },
        ),
        httpx.Response(
            200,
            json={
                "hasMore": False,
                "isTruncated": False,
                "invoices": [],
                "permanentStorageHwmDate": None,
            },
        ),
    ] * 2
    pager = auth.invoices.search(FILTERS)
    assert route.call_count == 0
    for _ in range(2):
        pages = flavor.collect(pager.responses())
        assert len(pages) == 2
        assert all(isinstance(page, QueryInvoicesMetadataResponse) for page in pages)
        assert [page.permanent_storage_hwm_date for page in pages] == [HWM, None]
        assert pages[0].invoices[0].ksef_number == ROW["ksefNumber"]
        assert pages[1].invoices == []
        assert [page.has_more for page in pages] == [True, False]
        assert [page.is_truncated for page in pages] == [truncated, False]
    offsets = [call.request.url.params["pageOffset"] for call in route.calls]
    assert offsets == (["0", "0", "0", "0"] if truncated else ["0", "1", "0", "1"])
    if truncated:
        assert b'"from":"2026-06-25T08:00:00Z"' in route.calls[1].request.content


def test_existing_list_and_legacy_response_contracts(
    auth: AuthenticatedClient | AsyncAuthenticatedClient,
    flavor: Flavor,
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(
        "https://api-test.ksef.mf.gov.pl/v2/invoices/query/metadata"
    ).respond(
        200,
        json={
            "hasMore": False,
            "isTruncated": False,
            "invoices": [],
            "permanentStorageHwmDate": HWM.isoformat(),
        },
    )
    pager = auth.invoices.search(FILTERS)
    assert flavor.run(pager.first_page()) == []
    assert flavor.collect(pager.pages()) == [[]]
    assert flavor.collect(pager) == []
    with pytest.warns(DeprecationWarning, match="no earlier than ksef2 2.0.0"):
        page = flavor.run(auth.invoices.query_metadata(filters=FILTERS))
    assert isinstance(page, QueryInvoicesMetadataResponse)
    assert page.permanent_storage_hwm_date == HWM
    assert route.call_count == 4


@pytest.mark.parametrize("language", ["en", "pl"])
@pytest.mark.parametrize("scenario", ["empty", "multiple", "no_hwm", "persist_failure"])
def test_documented_sync_persists_before_checkpoint(
    language: str, scenario: str, respx_mock: MockRouter
) -> None:
    route = respx_mock.post(
        "https://api-test.ksef.mf.gov.pl/v2/invoices/query/metadata"
    )
    route.side_effect = [
        httpx.Response(
            200,
            json={
                "hasMore": False,
                "isTruncated": False,
                "invoices": [ROW]
                if scenario in ("multiple", "persist_failure")
                else [],
                "permanentStorageHwmDate": None
                if scenario == "no_hwm"
                else HWM.isoformat(),
            },
        )
    ]
    if scenario == "multiple":
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "hasMore": True,
                    "isTruncated": False,
                    "invoices": [ROW],
                    "permanentStorageHwmDate": HWM.isoformat(),
                },
            ),
            httpx.Response(
                200,
                json={
                    "hasMore": False,
                    "isTruncated": False,
                    "invoices": [],
                    "permanentStorageHwmDate": HWM.isoformat(),
                },
            ),
        ]
    events: list[InvoiceMetadata | datetime] = []
    state = AuthenticationResumeState(
        access_token=SecretStr("mock-access-token"),
        access_token_valid_until=datetime(2099, 1, 1, tzinfo=UTC),
        refresh_token=SecretStr("mock-refresh-token"),
        refresh_token_valid_until=datetime(2099, 1, 1, tzinfo=UTC),
    )
    path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / language
        / "concepts/querying-and-exports.md"
    )
    code = re.findall(r"```python\n(.*?)```", path.read_text(), re.DOTALL)[0]

    def persist_metadata(invoice: InvoiceMetadata) -> None:
        if scenario == "persist_failure":
            raise OSError("mock storage unavailable")
        events.append(invoice)

    with Client(Environment.TEST) as client:
        namespace = {
            "auth": client.authentication.resume(state),
            "last_synced_at": datetime(2026, 1, 1, tzinfo=UTC),
            "persist_metadata": persist_metadata,
            "save_checkpoint": events.append,
        }
        if scenario == "persist_failure":
            with pytest.raises(OSError, match="mock storage unavailable"):
                exec(code, namespace)
        else:
            exec(code, namespace)
    if scenario == "multiple":
        assert len(events) == 2
        assert isinstance(events[0], InvoiceMetadata)
        assert events[0].ksef_number == ROW["ksefNumber"]
        assert events[1] == HWM
    else:
        assert events == ([HWM] if scenario == "empty" else [])
    assert route.call_count == (2 if scenario == "multiple" else 1)


def test_first_response_preserves_validation_cause(
    auth: AuthenticatedClient | AsyncAuthenticatedClient,
    flavor: Flavor,
    respx_mock: MockRouter,
) -> None:
    route = respx_mock.post(
        "https://api-test.ksef.mf.gov.pl/v2/invoices/query/metadata"
    ).respond(
        200,
        json={
            "hasMore": False,
            "isTruncated": False,
            "invoices": [],
            "permanentStorageHwmDate": "invalid-date",
        },
    )
    with pytest.raises(KSeFValidationError) as caught:
        _ = flavor.run(auth.invoices.search(FILTERS).first_response())
    assert caught.value.__cause__ is not None
    assert "permanentStorageHwmDate" in str(caught.value.__cause__)
    assert route.call_count == 1
