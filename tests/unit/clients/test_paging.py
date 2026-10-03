"""Every collection method returns the shared pager: items, ``pages()`` and ``first_page()``."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory

from ksef2._clients._async_pager import AsyncPager
from ksef2._clients._pager import Pager
from ksef2._clients.async_certificates import AsyncCertificatesClient
from ksef2._clients.async_collective_identifiers import AsyncCollectiveIdentifiersClient
from ksef2._clients.async_invoice_sessions import AsyncInvoiceSessionsClient
from ksef2._clients.async_peppol import AsyncPeppolClient
from ksef2._clients.async_permissions import AsyncPermissionsClient
from ksef2._clients.async_session_management import AsyncSessionManagementClient
from ksef2._clients.async_tokens import AsyncTokensClient
from ksef2._clients.certificates import CertificatesClient
from ksef2._clients.collective_identifiers import CollectiveIdentifiersClient
from ksef2._clients.invoice_sessions import InvoiceSessionsClient
from ksef2._clients.peppol import PeppolClient
from ksef2._clients.permissions import PermissionsClient
from ksef2._clients.session_management import SessionManagementClient
from ksef2._clients.tokens import TokensClient
from ksef2._domain.models.collective_identifiers import CollectiveIdentifiersQuery
from tests.unit.factories.auth import AuthenticationListResponseFactory
from tests.unit.factories.certificates import QueryCertificatesResponseFactory
from tests.unit.factories.collective_identifiers import (
    CollectiveIdentifierInvoicesResponseFactory,
    CollectiveIdentifiersByKsefNumberResponseFactory,
    CollectiveIdentifiersQueryResponseFactory,
)
from tests.unit.factories.peppol import QueryPeppolProvidersResponseFactory
from tests.unit.factories.permissions import (
    DomainAuthorizationPermissionsQueryFactory,
    DomainEntityPermissionsQueryFactory,
    DomainEuEntityPermissionsQueryFactory,
    DomainPersonalPermissionsQueryFactory,
    DomainPersonPermissionsQueryFactory,
    DomainSubordinateEntityRolesQueryFactory,
    DomainSubunitPermissionsQueryFactory,
    QueryEntityAuthorizationPermissionsResponseFactory,
    QueryEntityPermissionsResponseFactory,
    QueryEntityRolesResponseFactory,
    QueryEuEntityPermissionsResponseFactory,
    QueryPersonalPermissionsResponseFactory,
    QueryPersonPermissionsResponseFactory,
    QuerySubordinateEntityRolesResponseFactory,
    QuerySubunitPermissionsResponseFactory,
)
from tests.unit.factories.session import SessionsQueryResponseFactory
from tests.unit.factories.tokens import QueryTokensResponseFactory
from tests.unit.flavors import Flavor

KSEF_NUMBER = "1234567890-20250625-ABC123-DEF456-07"
COLLECTIVE_NUMBER = "1111111111-IZ202607-65ED02180000-E7"

# ``continuationToken`` pages carry a cursor; the other collections page by offset.
CURSOR = "continuationToken"
OFFSET = "hasMore"


def _no_args() -> tuple[Any, ...]:
    return ()


@dataclass(frozen=True)
class Collection:
    """One paged collection: how to call it and how its responses carry items and paging."""

    id: str
    sync_cls: type[Any]
    async_cls: type[Any]
    factory: type[ModelFactory[Any]]
    items_field: str
    paging: str
    method: str
    args: Callable[[], tuple[Any, ...]] = _no_args

    def call(self, client: Any) -> Any:
        """Call the new ``list_*`` method the way the docs show."""
        return getattr(client, self.method)(*self.args())


def _collective_filters() -> tuple[Any, ...]:
    return (
        CollectiveIdentifiersQuery(
            date_created_from=datetime(2026, 1, 1, tzinfo=UTC),
            date_created_to=datetime(2026, 2, 1, tzinfo=UTC),
        ),
    )


def _args(*values: Any) -> Callable[[], tuple[Any, ...]]:
    return lambda: values


def _query_args(
    query_factory: type[ModelFactory[Any]],
) -> Callable[[], tuple[Any, ...]]:
    return lambda: (query_factory.build(),)


COLLECTIONS = [
    Collection(
        "tokens.list",
        TokensClient,
        AsyncTokensClient,
        QueryTokensResponseFactory,
        "tokens",
        CURSOR,
        "list",
    ),
    Collection(
        "certificates.list",
        CertificatesClient,
        AsyncCertificatesClient,
        QueryCertificatesResponseFactory,
        "certificates",
        OFFSET,
        "list",
    ),
    Collection(
        "peppol.list",
        PeppolClient,
        AsyncPeppolClient,
        QueryPeppolProvidersResponseFactory,
        "peppolProviders",
        OFFSET,
        "list",
    ),
    Collection(
        "sessions.list",
        SessionManagementClient,
        AsyncSessionManagementClient,
        AuthenticationListResponseFactory,
        "items",
        CURSOR,
        "list",
    ),
    Collection(
        "invoice_sessions.list",
        InvoiceSessionsClient,
        AsyncInvoiceSessionsClient,
        SessionsQueryResponseFactory,
        "sessions",
        CURSOR,
        "list",
        _args("online"),
    ),
    Collection(
        "collective_identifiers.list",
        CollectiveIdentifiersClient,
        AsyncCollectiveIdentifiersClient,
        CollectiveIdentifiersQueryResponseFactory,
        "collectiveIdentifiers",
        CURSOR,
        "list",
        _collective_filters,
    ),
    Collection(
        "collective_identifiers.list_for_invoice",
        CollectiveIdentifiersClient,
        AsyncCollectiveIdentifiersClient,
        CollectiveIdentifiersByKsefNumberResponseFactory,
        "collectiveIdentifiers",
        CURSOR,
        "list_for_invoice",
        _args(KSEF_NUMBER),
    ),
    Collection(
        "collective_identifiers.list_invoices",
        CollectiveIdentifiersClient,
        AsyncCollectiveIdentifiersClient,
        CollectiveIdentifierInvoicesResponseFactory,
        "invoices",
        CURSOR,
        "list_invoices",
        _args([COLLECTIVE_NUMBER]),
    ),
    Collection(
        "permissions.list_entity_roles",
        PermissionsClient,
        AsyncPermissionsClient,
        QueryEntityRolesResponseFactory,
        "roles",
        OFFSET,
        "list_entity_roles",
    ),
    Collection(
        "permissions.list_authorizations",
        PermissionsClient,
        AsyncPermissionsClient,
        QueryEntityAuthorizationPermissionsResponseFactory,
        "authorizationGrants",
        OFFSET,
        "list_authorizations",
        _query_args(DomainAuthorizationPermissionsQueryFactory),
    ),
    Collection(
        "permissions.list_entities",
        PermissionsClient,
        AsyncPermissionsClient,
        QueryEntityPermissionsResponseFactory,
        "permissions",
        OFFSET,
        "list_entities",
        _query_args(DomainEntityPermissionsQueryFactory),
    ),
    Collection(
        "permissions.list_eu_entities",
        PermissionsClient,
        AsyncPermissionsClient,
        QueryEuEntityPermissionsResponseFactory,
        "permissions",
        OFFSET,
        "list_eu_entities",
        _query_args(DomainEuEntityPermissionsQueryFactory),
    ),
    Collection(
        "permissions.list_personal",
        PermissionsClient,
        AsyncPermissionsClient,
        QueryPersonalPermissionsResponseFactory,
        "permissions",
        OFFSET,
        "list_personal",
        _query_args(DomainPersonalPermissionsQueryFactory),
    ),
    Collection(
        "permissions.list_persons",
        PermissionsClient,
        AsyncPermissionsClient,
        QueryPersonPermissionsResponseFactory,
        "permissions",
        OFFSET,
        "list_persons",
        _query_args(DomainPersonPermissionsQueryFactory),
    ),
    Collection(
        "permissions.list_subordinate_entities",
        PermissionsClient,
        AsyncPermissionsClient,
        QuerySubordinateEntityRolesResponseFactory,
        "roles",
        OFFSET,
        "list_subordinate_entities",
        _query_args(DomainSubordinateEntityRolesQueryFactory),
    ),
    Collection(
        "permissions.list_subunits",
        PermissionsClient,
        AsyncPermissionsClient,
        QuerySubunitPermissionsResponseFactory,
        "permissions",
        OFFSET,
        "list_subunits",
        _query_args(DomainSubunitPermissionsQueryFactory),
    ),
]


def _page(collection: Collection, *, more: bool) -> dict[str, Any]:
    """Build one response page; ``more`` says whether KSeF reports a next page."""
    overrides: dict[str, Any]
    if collection.paging == CURSOR:
        overrides = {CURSOR: "next-page" if more else None}
    else:
        overrides = {OFFSET: more}
    page = collection.factory.build(**overrides).model_dump(mode="json")
    page[collection.items_field] = page[collection.items_field][:2] or []
    return page


def _client(collection: Collection, flavor: Flavor) -> Any:
    return flavor.client(collection.sync_cls, collection.async_cls)


@pytest.fixture(params=COLLECTIONS, ids=lambda collection: collection.id)
def collection(request: pytest.FixtureRequest) -> Collection:
    return request.param


class TestPaging:
    def _enqueue_two_pages(
        self, collection: Collection, flavor: Flavor
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        first = _page(collection, more=True)
        second = _page(collection, more=False)
        for page in (first, second):
            assert page[collection.items_field], "factory must build at least one item"
            flavor.transport.enqueue(page)
        return first, second

    def test_returns_the_shared_pager_and_requests_nothing_until_consumed(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        pager = collection.call(_client(collection, flavor))

        assert isinstance(pager, AsyncPager if flavor.is_async else Pager)
        assert flavor.transport.calls == []

    def test_iterating_yields_the_items_of_every_page(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        first, second = self._enqueue_two_pages(collection, flavor)

        items = flavor.collect(collection.call(_client(collection, flavor)))

        assert len(items) == len(first[collection.items_field]) + len(
            second[collection.items_field]
        )
        assert len(flavor.transport.calls) == 2

    def test_pages_yields_one_list_per_page(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        first, second = self._enqueue_two_pages(collection, flavor)

        pages = flavor.collect(collection.call(_client(collection, flavor)).pages())

        assert [len(page) for page in pages] == [
            len(first[collection.items_field]),
            len(second[collection.items_field]),
        ]
        assert all(isinstance(page, list) for page in pages)

    def test_first_page_fetches_only_the_first_page(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        first, _ = self._enqueue_two_pages(collection, flavor)

        page = flavor.run(collection.call(_client(collection, flavor)).first_page())

        assert len(page) == len(first[collection.items_field])
        assert len(flavor.transport.calls) == 1

    def test_first_page_of_an_empty_collection_is_empty(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        empty = _page(collection, more=False)
        empty[collection.items_field] = []
        flavor.transport.enqueue(empty)

        page = flavor.run(collection.call(_client(collection, flavor)).first_page())

        assert page == []

    def test_following_pages_use_the_paging_state_of_the_previous_one(
        self, collection: Collection, flavor: Flavor
    ) -> None:
        _ = self._enqueue_two_pages(collection, flavor)

        _ = flavor.collect(collection.call(_client(collection, flavor)))

        second = flavor.transport.calls[1]
        if collection.paging == CURSOR:
            assert (second.headers or {}).get("x-continuation-token") == "next-page"
        else:
            assert second.params is not None
            assert second.params["pageOffset"] == "1"
