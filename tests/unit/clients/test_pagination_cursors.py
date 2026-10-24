"""Resumable cursors: every collection continues from a stored cursor with one request."""

import base64
import json
from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, ValidationError

from ksef2._clients._pagination_cursor import (
    CURSOR_VERSION,
    ContinuationCursor,
    InvoiceSearchCursor,
    OffsetCursor,
    search_fingerprint,
)
from ksef2._core.exceptions import KSeFArgumentError
from ksef2._domain.models.invoices import InvoicesFilter
from ksef2._domain.models.pagination import (
    CollectiveIdentifierParams,
    InvoiceMetadataParams,
    ListSessionsQuery,
    OffsetPaginationParams,
    Page,
    PermissionsQueryParams,
    TokenListParams,
)
from ksef2._domain.models.session import FormSchema
from ksef2.clients import AsyncPager, Pager
from tests.unit.clients.test_paging import (
    COLLECTIONS,
    CURSOR,
    OFFSET,
    Collection,
    _client,
    _page,
)
from tests.unit.factories.auth import DomainAuthTokensFactory
from tests.unit.fakes.transport import RecordedCall
from tests.unit.support.flavors import Flavor

COLLECTIONS_BY_ID: dict[str, Collection] = {c.id: c for c in COLLECTIONS}
PERMISSION_COLLECTION_IDS = sorted(
    collection_id
    for collection_id in COLLECTIONS_BY_ID
    if collection_id.startswith("permissions.")
)
OFFSET_COLLECTIONS = [c for c in COLLECTIONS if c.paging == OFFSET]
CURSOR_COLLECTIONS = [c for c in COLLECTIONS if c.paging == CURSOR]

# The JSON keys a cursor may carry, and nothing else.
CURSOR_STATE_FIELDS = {
    "v",
    "operation",
    "continuation_token",
    "page_offset",
    "filters",
    "params",
    "previous_truncation_boundary",
}

# Paging parameters of the collections that name them, per operation.
_CollectionQuery = (
    CollectiveIdentifierParams
    | ListSessionsQuery
    | OffsetPaginationParams
    | PermissionsQueryParams
    | TokenListParams
)

# Non-default page size for every collection, plus non-default filters or identifiers
# where the method takes them, so a resumed request proves the SDK kept the caller's
# own query rather than a default one.
_COLLECTION_KWARGS: dict[str, dict[str, _CollectionQuery | int]] = {
    "tokens.list": {
        "params": TokenListParams(
            page_size=15, description="nightly", author_identifier="1234567890"
        )
    },
    "sessions.list": {"page_size": 15},
    "invoice_sessions.list": {
        "params": ListSessionsQuery(
            session_type="online", reference_number="ref-7", page_size=15
        )
    },
    "collective_identifiers.list": {"params": CollectiveIdentifierParams(page_size=15)},
    "collective_identifiers.list_for_invoice": {
        "params": CollectiveIdentifierParams(page_size=15)
    },
    "collective_identifiers.list_invoices": {
        "params": CollectiveIdentifierParams(page_size=15)
    },
    "certificates.list": {"params": OffsetPaginationParams(page_size=15)},
    "peppol.list": {"params": OffsetPaginationParams(page_size=15)},
}

# The permission queries that page through PermissionsQueryParams; list_entity_roles
# takes plain offset parameters and needs no override.
_PERMISSION_QUERY_COLLECTIONS = frozenset(
    {
        "permissions.list_authorizations",
        "permissions.list_entities",
        "permissions.list_eu_entities",
        "permissions.list_personal",
        "permissions.list_persons",
        "permissions.list_subordinate_entities",
        "permissions.list_subunits",
    }
)


def _kwargs(collection: Collection) -> dict[str, _CollectionQuery | int]:
    """Return the non-default keyword arguments for calling one collection."""
    if collection.id in _PERMISSION_QUERY_COLLECTIONS:
        return {"params": PermissionsQueryParams(page_size=15, page_offset=2)}
    return dict(_COLLECTION_KWARGS.get(collection.id, {}))


def _call(
    collection: Collection, client: object, **overrides: _CollectionQuery | int
) -> Pager[BaseModel] | AsyncPager[BaseModel]:
    """Call a collection method the way a caller would, with its own arguments."""
    kwargs = _kwargs(collection)
    kwargs.update(overrides)
    return getattr(client, collection.method)(*collection.args(), **kwargs)


def _page_at(
    flavor: Flavor,
    collection: Collection,
    client: object,
    cursor: str | None,
    **overrides: _CollectionQuery | int,
) -> Page[BaseModel]:
    """Fetch one page in this flavour; the async pager returns an awaitable."""
    pager = _call(collection, client, **overrides)
    return flavor.run(pager.page(cursor))


def _shape(items: list[BaseModel]) -> list[str]:
    """Render items so pages read by two different clients can be compared."""
    return [item.model_dump_json() for item in items]


def _carry(cursor: str) -> str:
    """Send a cursor through JSON the way a language binding would, and read it back."""
    return str(json.loads(json.dumps({"cursor": cursor}))["cursor"])


def _paging_detail(collection: Collection, call: RecordedCall) -> str:
    """Describe the paging state one recorded request carried."""
    if collection.paging == CURSOR:
        return str((call.headers or {}).get("x-continuation-token"))
    return "" if call.params is None else str(call.params.get("pageOffset"))


def _cursor_payload(cursor: str) -> str:
    """Return the JSON text stored inside a cursor."""
    return base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("utf-8")


def _cursor_state(cursor: str) -> dict[str, object]:
    """Read the JSON state stored inside a cursor as plain values."""
    state: dict[str, object] = json.loads(_cursor_payload(cursor))
    return state


def _tampered_cursor(state: dict[str, object]) -> str:
    """Build a cursor string from raw JSON state, as a caller tampering with one would."""
    return base64.urlsafe_b64encode(json.dumps(state).encode("utf-8")).decode("ascii")


def _without_version(cursor: str) -> str:
    """Return a real cursor with its format version taken off the wire."""
    state = _cursor_state(cursor)
    del state["v"]
    return _tampered_cursor(state)


def _offset_cursor(page_offset: int = 1) -> str:
    """One known cursor string, spelled exactly as the SDK writes it."""
    return OffsetCursor(
        v=CURSOR_VERSION, operation="peppol.list", page_offset=page_offset
    ).encode()


SEARCH = "a" * 64


def _invoice_search_cursor(
    boundary: date | datetime | None = None,
) -> InvoiceSearchCursor:
    """A search cursor carrying a request and, when given, the boundary it stopped on."""
    return InvoiceSearchCursor(
        v=CURSOR_VERSION,
        operation="invoices.search",
        search=SEARCH,
        search_date_to=datetime(2026, 2, 1, tzinfo=timezone.utc),
        filters=InvoicesFilter(
            role="seller",
            date_type="issue_date",
            date_from=datetime(2026, 1, 1),
        ),
        params=InvoiceMetadataParams(page_size=10, page_offset=1),
        previous_truncation_boundary=boundary,
    )


class TestCollectionCursors:
    @pytest.mark.parametrize("collection", COLLECTIONS, ids=lambda c: c.id)
    def test_every_collection_resumes_with_one_request(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        pages = [_page(collection, more=more) for more in (True, True, False)]
        for page in pages:
            assert page[collection.items_field], "factory must build at least one item"

        # Walking the collection gives the pages a resumed walk has to reproduce.
        walking = _client(collection, flavor)
        for page in pages:
            flavor.transport.enqueue(page)
        traversal = flavor.collect(_call(collection, walking).pages())
        assert len(flavor.transport.calls) == 3
        initial_paging = _paging_detail(collection, flavor.transport.calls[0])
        start = 0 if collection.paging == CURSOR else int(initial_paging or "0")

        cursor: str | None = None
        for index, walked_items in enumerate(traversal):
            flavor.transport.clear()
            client = _client(collection, flavor)
            flavor.transport.enqueue(pages[index])

            page = _page_at(
                flavor,
                collection,
                client,
                None if cursor is None else _carry(cursor),
            )

            assert isinstance(page, Page)
            assert _shape(page.items) == _shape(walked_items)
            assert len(flavor.transport.calls) == 1
            if collection.paging == CURSOR:
                expected_paging = "None" if index == 0 else "next-page"
            else:
                expected_paging = str(start + index)
            assert (
                _paging_detail(collection, flavor.transport.calls[0]) == expected_paging
            )
            if index + 1 < len(traversal):
                assert page.next_cursor is not None
                cursor = page.next_cursor
            else:
                assert page.next_cursor is None

    def test_page_rejects_a_cursor_from_another_collection(
        self, flavor: Flavor
    ) -> None:
        """Two continuation-token collections must not accept each other's cursors."""
        collection = COLLECTIONS_BY_ID["tokens.list"]
        other = COLLECTIONS_BY_ID["sessions.list"]
        flavor.transport.enqueue(_page(collection, more=True))

        first = _page_at(flavor, collection, _client(collection, flavor), None)

        assert first.next_cursor is not None
        with pytest.raises(KSeFArgumentError, match="not for sessions.list"):
            _page_at(flavor, other, _client(other, flavor), first.next_cursor)
        assert len(flavor.transport.calls) == 1

    def test_page_rejects_a_cursor_of_another_paging_style(
        self, flavor: Flavor
    ) -> None:
        """An offset collection rejects a continuation cursor before sending anything."""
        collection = COLLECTIONS_BY_ID["tokens.list"]
        other = COLLECTIONS_BY_ID["peppol.list"]
        flavor.transport.enqueue(_page(collection, more=True))

        first = _page_at(flavor, collection, _client(collection, flavor), None)

        assert first.next_cursor is not None
        with pytest.raises(KSeFArgumentError, match="Invalid pagination cursor"):
            _page_at(flavor, other, _client(other, flavor), first.next_cursor)
        assert len(flavor.transport.calls) == 1

    @pytest.mark.parametrize(
        "collection",
        [COLLECTIONS_BY_ID["peppol.list"], COLLECTIONS_BY_ID["tokens.list"]],
        ids=["offset", "continuation"],
    )
    def test_cursor_missing_version_is_rejected(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        """A cursor that dropped its version stops a real request on either paging style."""
        flavor.transport.enqueue(_page(collection, more=True))
        issued = _page_at(flavor, collection, _client(collection, flavor), None)

        assert issued.next_cursor is not None
        versionless = _without_version(issued.next_cursor)
        flavor.transport.clear()

        with pytest.raises(KSeFArgumentError, match="its v is missing"):
            _page_at(flavor, collection, _client(collection, flavor), versionless)

        assert flavor.transport.calls == []

    @pytest.mark.parametrize("method", PERMISSION_COLLECTION_IDS)
    def test_cursor_wrong_operation_is_rejected(
        self, method: str, flavor: Flavor
    ) -> None:
        """The permissions queries share one pager builder, so their cursors must not mix."""
        collection = COLLECTIONS_BY_ID[method]
        flavor.transport.enqueue(_page(collection, more=True))

        first = _page_at(flavor, collection, _client(collection, flavor), None)

        assert first.next_cursor is not None
        other_id = next(other for other in PERMISSION_COLLECTION_IDS if other != method)
        other = COLLECTIONS_BY_ID[other_id]
        with pytest.raises(KSeFArgumentError, match=f"not for {other_id}"):
            _page_at(flavor, other, _client(other, flavor), first.next_cursor)
        assert len(flavor.transport.calls) == 1

    @pytest.mark.parametrize("collection", OFFSET_COLLECTIONS, ids=lambda c: c.id)
    def test_resume_uses_the_cursor_offset_not_the_new_pagers_offset(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        flavor.transport.enqueue(_page(collection, more=True))
        first = _page_at(
            flavor,
            collection,
            _client(collection, flavor),
            None,
            params=OffsetPaginationParams(page_size=15, page_offset=2),
        )

        assert _paging_detail(collection, flavor.transport.calls[0]) == "2"
        assert first.next_cursor is not None

        flavor.transport.enqueue(_page(collection, more=False))
        resumed = _page_at(
            flavor,
            collection,
            _client(collection, flavor),
            first.next_cursor,
            params=OffsetPaginationParams(page_size=15, page_offset=9),
        )

        assert resumed.next_cursor is None
        assert len(flavor.transport.calls) == 2
        assert _paging_detail(collection, flavor.transport.calls[1]) == "3"

    @pytest.mark.parametrize("collection", CURSOR_COLLECTIONS, ids=lambda c: c.id)
    def test_resume_sends_ksefs_continuation_token(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        flavor.transport.enqueue(_page(collection, more=True))
        first = _page_at(flavor, collection, _client(collection, flavor), None)

        assert first.next_cursor is not None
        assert _paging_detail(collection, flavor.transport.calls[0]) == "None"

        flavor.transport.enqueue(_page(collection, more=False))
        resumed = _page_at(
            flavor, collection, _client(collection, flavor), first.next_cursor
        )

        assert resumed.next_cursor is None
        assert len(flavor.transport.calls) == 2
        assert _paging_detail(collection, flavor.transport.calls[1]) == "next-page"

    def test_cursor_carries_pagination_state_and_no_credentials(
        self, flavor: Flavor
    ) -> None:
        tokens = DomainAuthTokensFactory.build()
        client = flavor.authenticated(tokens)
        flavor.transport.enqueue(_page(COLLECTIONS_BY_ID["tokens.list"], more=True))

        page = flavor.run(client.tokens.list().page(None))

        assert page.next_cursor is not None
        payload = _cursor_payload(page.next_cursor)
        assert set(json.loads(payload)) <= CURSOR_STATE_FIELDS
        assert tokens.access_token.token not in page.next_cursor
        assert tokens.access_token.token not in payload
        assert tokens.refresh_token.token not in payload
        assert "authorization" not in payload.lower()
        assert "bearer" not in payload.lower()
        recorded = flavor.transport.calls[0].headers or {}
        assert recorded["Authorization"].endswith(tokens.access_token.token)

    def test_cursor_payload_is_decoded_by_the_same_sdk_only(
        self, flavor: Flavor
    ) -> None:
        collection = COLLECTIONS_BY_ID["peppol.list"]
        flavor.transport.enqueue(_page(collection, more=True))

        page = _page_at(
            flavor,
            collection,
            _client(collection, flavor),
            None,
            params=OffsetPaginationParams(page_offset=1),
        )

        assert page.next_cursor is not None
        assert (
            OffsetCursor.decode(page.next_cursor, operation="peppol.list").page_offset
            == 2
        )


class TestCursorValidation:
    @pytest.mark.parametrize(
        ("cursor", "reason"),
        [
            ("", "it is empty"),
            ("not a cursor!!", "not URL-safe Base64"),
            ("a", "not valid Base64"),
            (base64.urlsafe_b64encode(b"\xff\xfe").decode("ascii"), "not valid UTF-8"),
            ("bm90IGpzb24=", "not valid JSON"),
            ("Imp1c3QgYSBzdHJpbmci", "not a JSON object"),
        ],
        ids=[
            "empty",
            "bad-alphabet",
            "bad-length",
            "not-utf8",
            "not-json",
            "not-an-object",
        ],
    )
    def test_malformed_cursor_is_rejected(self, cursor: str, reason: str) -> None:
        with pytest.raises(KSeFArgumentError, match=reason):
            OffsetCursor.decode(cursor, operation="peppol.list")

    @pytest.mark.parametrize(
        "version", [2, True, "1", 1.0], ids=["two", "bool", "str", "float"]
    )
    def test_cursor_with_an_unsupported_version_is_rejected(
        self, version: object
    ) -> None:
        cursor = _tampered_cursor(
            {"v": version, "operation": "peppol.list", "page_offset": 1}
        )

        with pytest.raises(KSeFArgumentError, match="its v is invalid"):
            OffsetCursor.decode(cursor, operation="peppol.list")

    def test_cursor_without_a_version_is_rejected(self) -> None:
        """A cursor that names no format version is refused rather than read as v1."""
        offset = _tampered_cursor({"operation": "peppol.list", "page_offset": 1})
        continuation = _tampered_cursor(
            {"operation": "tokens.list", "continuation_token": "next-page"}
        )
        search = _without_version(_invoice_search_cursor(date(2026, 1, 5)).encode())

        with pytest.raises(KSeFArgumentError, match="its v is missing"):
            OffsetCursor.decode(offset, operation="peppol.list")
        with pytest.raises(KSeFArgumentError, match="its v is missing"):
            ContinuationCursor.decode(continuation, operation="tokens.list")
        with pytest.raises(KSeFArgumentError, match="its v is missing"):
            InvoiceSearchCursor.decode(search, operation="invoices.search")

    @pytest.mark.parametrize(
        ("cursor", "reason"),
        [
            ("+/+/", "not URL-safe Base64"),
            ("-_-_", "not valid UTF-8"),
            (" eyJ2Ijox", "not URL-safe Base64"),
            ("eyJ2 Ijox", "not URL-safe Base64"),
            ("eyJ2Ijox\u00e9", "not URL-safe Base64"),
            (f"{_offset_cursor()}=======", "Base64 padding is malformed"),
            (f"{_offset_cursor()[:-2]}===", "Base64 padding is malformed"),
            (f"{_offset_cursor()[:-1]}", "Base64 padding is malformed"),
            (f"={_offset_cursor()}", "Base64 padding is misplaced"),
            (
                f"{_offset_cursor()[:10]}={_offset_cursor()[10:]}",
                "Base64 padding is misplaced",
            ),
        ],
        ids=[
            "standard-alphabet",
            "url-safe-alphabet",
            "leading-space",
            "inner-space",
            "non-ascii",
            "padding-appended",
            "padding-overstated",
            "padding-short",
            "padding-leading",
            "padding-interior",
        ],
    )
    def test_cursor_spelling_is_checked_before_it_is_read(
        self, cursor: str, reason: str
    ) -> None:
        """Only the URL-safe alphabet and canonical padding (or none) reach the payload.

        The url-safe-alphabet case carries the same bytes as the standard-alphabet one
        above and fails further in, on the UTF-8 read: that is how it shows the alphabet
        itself was accepted.
        """
        with pytest.raises(KSeFArgumentError, match=reason):
            OffsetCursor.decode(cursor, operation="peppol.list")

    @pytest.mark.parametrize(
        "padding", ["kept", "stripped"], ids=["padded", "unpadded"]
    )
    def test_cursor_is_read_with_or_without_its_padding(self, padding: str) -> None:
        """The SDK writes canonical padding and still reads a cursor someone trimmed."""
        cursor = _offset_cursor(page_offset=7)
        if padding == "stripped":
            cursor = cursor.rstrip("=")

        assert OffsetCursor.decode(cursor, operation="peppol.list").page_offset == 7

    @pytest.mark.parametrize(
        "page_offset", [-1, "3", True, 1.5], ids=["negative", "str", "bool", "float"]
    )
    def test_cursor_with_an_invalid_page_offset_is_rejected(
        self, page_offset: object
    ) -> None:
        cursor = _tampered_cursor(
            {"v": 1, "operation": "peppol.list", "page_offset": page_offset}
        )

        with pytest.raises(KSeFArgumentError, match="its page_offset is invalid"):
            OffsetCursor.decode(cursor, operation="peppol.list")

    def test_cursor_with_an_unknown_field_is_rejected(self) -> None:
        cursor = _tampered_cursor(
            {
                "v": 1,
                "operation": "peppol.list",
                "page_offset": 1,
                "page_size": 999,
            }
        )

        with pytest.raises(KSeFArgumentError, match="its page_size is invalid"):
            OffsetCursor.decode(cursor, operation="peppol.list")

    def test_cursor_missing_a_field_is_rejected(self) -> None:
        cursor = _tampered_cursor({"v": 1, "operation": "peppol.list"})

        with pytest.raises(KSeFArgumentError, match="its page_offset is missing"):
            OffsetCursor.decode(cursor, operation="peppol.list")

    def test_error_never_echoes_the_cursor(self) -> None:
        cursor = _tampered_cursor(
            {"v": 1, "operation": "peppol.list", "page_offset": -5}
        )

        with pytest.raises(KSeFArgumentError) as caught:
            OffsetCursor.decode(cursor, operation="peppol.list")

        assert cursor not in str(caught.value)
        assert cursor not in str(caught.value.context)


class TestInvoiceSearchCursorState:
    """Invoice search resumes with the request and boundary it stopped on."""

    @pytest.mark.parametrize("member", FormSchema)
    def test_cursor_keeps_invoice_schema(self, member: FormSchema) -> None:
        filters = InvoicesFilter(
            role="seller",
            date_type="issue_date",
            date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
            invoice_schema=member,
        )
        cursor = InvoiceSearchCursor(
            v=CURSOR_VERSION,
            operation="invoices.search",
            search=SEARCH,
            search_date_to=datetime(2026, 2, 1, tzinfo=timezone.utc),
            filters=filters,
            params=InvoiceMetadataParams(),
        )

        resumed = InvoiceSearchCursor.decode(
            cursor.encode(), operation="invoices.search"
        )

        assert resumed.filters == filters

    @pytest.mark.parametrize(
        "boundary",
        [
            date(2026, 1, 5),
            datetime(2026, 1, 5, 0, 0),
            datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 5, 0, 0, tzinfo=timezone(timedelta(hours=2))),
            datetime(2026, 1, 5, 12, 30, 45, 123456),
            datetime(2026, 1, 5, 12, 30, 45),
        ],
        ids=[
            "date",
            "naive-midnight",
            "utc-midnight",
            "offset-midnight",
            "fractional-seconds",
            "non-midnight",
        ],
    )
    def test_boundary_keeps_its_own_type_through_a_cursor(
        self, boundary: date | datetime
    ) -> None:
        """A resumed search compares date with date and timestamp with timestamp.

        A boundary that came back as the other type would never compare equal to the next
        one, so the search would miss that KSeF stopped advancing. A midnight timestamp is
        the sharp case: read carelessly it looks exactly like the calendar date under it.
        """
        cursor = _invoice_search_cursor(boundary)

        resumed = InvoiceSearchCursor.decode(
            cursor.encode(), operation="invoices.search"
        )

        resumed_boundary = resumed.previous_truncation_boundary
        assert resumed_boundary == boundary
        assert type(resumed_boundary) is type(boundary)
        if isinstance(boundary, datetime) and isinstance(resumed_boundary, datetime):
            assert resumed_boundary.utcoffset() == boundary.utcoffset()
            assert resumed_boundary.microsecond == boundary.microsecond


class TestSearchFingerprint:
    """The fingerprint names a search, not how far it has progressed."""

    FILTERS = InvoicesFilter(
        role="seller",
        date_type="issue_date",
        date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_to=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )

    def test_fingerprint_ignores_date_to_and_page_offset(self) -> None:
        later = self.FILTERS.model_copy(
            update={"date_to": datetime(2030, 1, 1, tzinfo=timezone.utc)}
        )

        assert search_fingerprint(
            self.FILTERS, InvoiceMetadataParams(page_offset=0)
        ) == search_fingerprint(later, InvoiceMetadataParams(page_offset=7))

    @pytest.mark.parametrize(
        ("filters", "params"),
        [
            (
                FILTERS.model_copy(update={"buyer_nip": "5260250274"}),
                InvoiceMetadataParams(),
            ),
            (
                FILTERS.model_copy(
                    update={"date_from": datetime(2025, 1, 1, tzinfo=timezone.utc)}
                ),
                InvoiceMetadataParams(),
            ),
            (FILTERS, InvoiceMetadataParams(page_size=50)),
            (FILTERS, InvoiceMetadataParams(sort_order="desc")),
        ],
        ids=["filter", "date-from", "page-size", "sort-order"],
    )
    def test_fingerprint_changes_with_the_search(
        self, filters: InvoicesFilter, params: InvoiceMetadataParams
    ) -> None:
        assert search_fingerprint(filters, params) != search_fingerprint(
            self.FILTERS, InvoiceMetadataParams()
        )

    def test_decode_search_rejects_a_cursor_of_another_search(self) -> None:
        cursor = _invoice_search_cursor().encode()

        assert (
            InvoiceSearchCursor.decode_search(
                cursor, operation="invoices.search", search=SEARCH
            ).search
            == SEARCH
        )
        with pytest.raises(KSeFArgumentError, match="different search") as caught:
            _ = InvoiceSearchCursor.decode_search(
                cursor, operation="invoices.search", search="b" * 64
            )
        assert cursor not in str(caught.value)

    @pytest.mark.parametrize("search", ["", "A" * 64, "a" * 63, "g" * 64])
    def test_cursor_requires_a_lowercase_hex_fingerprint(self, search: str) -> None:
        with pytest.raises(ValidationError):
            _ = InvoiceSearchCursor(
                v=CURSOR_VERSION,
                operation="invoices.search",
                search=search,
                search_date_to=self.FILTERS.date_to,
                filters=self.FILTERS,
                params=InvoiceMetadataParams(),
            )
