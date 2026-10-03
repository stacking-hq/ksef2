"""Aliases kept by the consistent-surface change warn exactly once and still work (sync and async)."""

import inspect
import os
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import BaseModel

from tests.unit.clients.test_paging import (
    COLLECTIONS,
    COLLECTIVE_NUMBER,
    KSEF_NUMBER,
    _client,  # pyright: ignore[reportPrivateUsage]
    _page,  # pyright: ignore[reportPrivateUsage]
)
from tests.unit.flavors import Flavor

SUFFIX = "will be removed in ksef2 1.10.0; use `{new}` instead."
BY_ID = {collection.id: collection for collection in COLLECTIONS}


def once(flavor: Flavor, call: Callable[[], Any], old: str, new: str) -> Any:
    """Call, drain, and assert exactly one DeprecationWarning with the 1.10.0 message."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = call()
        if inspect.isgenerator(value) or inspect.isasyncgen(value):
            result = flavor.collect(value)
        else:
            result = flavor.run(value)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecations) == 1, [str(w.message) for w in deprecations]
    message = str(deprecations[0].message)
    assert message.startswith(f"`{old}` is deprecated and ")
    assert message.endswith(SUFFIX.format(new=new))
    if not os.environ.get("KSEF2_RUNTIME_CHECKS"):
        assert deprecations[0].filename == __file__
    return result


@dataclass(frozen=True)
class PagingAlias:
    """A deprecated paging method, its replacement and what it still returns."""

    collection: str
    old: str
    kwargs: Callable[[Any], dict[str, Any]]
    returns: str  # "page": one response model, "pages": a list of them, "items": a list of items

    @property
    def new(self) -> str:
        return BY_ID[self.collection].method

    @property
    def id(self) -> str:
        return f"{self.collection.split('.')[0]}.{self.old}"


def _none(_: Any) -> dict[str, Any]:
    return {}


def _filters(collection: Any) -> dict[str, Any]:
    return {"filters": collection.args()[0]}


def _query(collection: Any) -> dict[str, Any]:
    return {"query": collection.args()[0]}


def _alias(
    collection: str,
    old: str,
    returns: str,
    kwargs: Callable[[Any], dict[str, Any]] = _none,
) -> PagingAlias:
    return PagingAlias(collection, old, kwargs, returns)


ALIASES = [
    _alias("tokens.list", "list_page", "page"),
    _alias("tokens.list", "list_all", "pages"),
    _alias("certificates.list", "query", "page"),
    _alias("certificates.list", "all", "items"),
    _alias("peppol.list", "query", "page"),
    _alias("peppol.list", "all", "items"),
    _alias("sessions.list", "query", "page"),
    _alias("sessions.list", "all", "pages"),
    _alias(
        "invoice_sessions.list", "query", "page", lambda _: {"session_type": "online"}
    ),
    _alias(
        "invoice_sessions.list", "all", "pages", lambda _: {"session_type": "online"}
    ),
    _alias("collective_identifiers.list", "query", "page", _filters),
    _alias("collective_identifiers.list", "query_all", "pages", _filters),
    _alias(
        "collective_identifiers.list_for_invoice",
        "query_by_ksef_number",
        "page",
        lambda _: {"ksef_number": KSEF_NUMBER},
    ),
    _alias(
        "collective_identifiers.list_for_invoice",
        "query_all_by_ksef_number",
        "pages",
        lambda _: {"ksef_number": KSEF_NUMBER},
    ),
    _alias(
        "collective_identifiers.list_invoices",
        "list_all_invoices",
        "pages",
        lambda _: {"collective_identifier_numbers": [COLLECTIVE_NUMBER]},
    ),
    _alias("permissions.list_entity_roles", "get_entity_roles", "page"),
    _alias("permissions.list_authorizations", "query_authorizations", "page", _query),
    _alias("permissions.list_entities", "query_entities", "page", _query),
    _alias("permissions.list_eu_entities", "query_eu_entities", "page", _query),
    _alias("permissions.list_personal", "query_personal", "page", _query),
    _alias("permissions.list_persons", "query_persons", "page", _query),
    _alias(
        "permissions.list_subordinate_entities",
        "query_subordinate_entities",
        "page",
        _query,
    ),
    _alias("permissions.list_subunits", "query_subunits", "page", _query),
]


@pytest.fixture(params=ALIASES, ids=lambda alias: alias.id)
def alias(request: pytest.FixtureRequest) -> PagingAlias:
    return request.param


class TestDeprecatedPagingAliases:
    def test_alias_warns_once_and_keeps_its_old_return_type(
        self, alias: PagingAlias, flavor: Flavor
    ) -> None:
        collection = BY_ID[alias.collection]
        page = _page(collection, more=False)
        flavor.transport.enqueue(page)
        client = _client(collection, flavor)
        method = getattr(client, alias.old)

        result = once(
            flavor,
            lambda: method(**alias.kwargs(collection)),
            f"{alias.old}()",
            f"{alias.new}()",
        )

        item_count = len(page[collection.items_field])
        if alias.returns == "page":
            # One response model carrying the items, not a pager and not a list.
            assert not isinstance(result, list)
            assert isinstance(result, BaseModel)
        elif alias.returns == "pages":
            assert len(result) == 1
            assert isinstance(result[0], BaseModel)
        else:
            assert len(result) == item_count
        assert len(flavor.transport.calls) == 1
