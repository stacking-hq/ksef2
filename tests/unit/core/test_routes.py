import json

from ksef2._core import routes


def test_route_constant_is_its_path_string() -> None:
    query = routes.CollectiveIdentifierRoutes.QUERY

    assert query == "/collective-identifiers/query"
    assert f"{query}" == "/collective-identifiers/query"
    assert json.dumps({"path": query}) == '{"path": "/collective-identifiers/query"}'


def test_route_constant_carries_its_http_method() -> None:
    send = routes.InvoiceRoutes.SEND

    assert send.method == routes.HttpMethod.POST
    assert send.path == "/sessions/online/{referenceNumber}/invoices"


def test_two_methods_on_one_path_stay_separate_routes() -> None:
    generate = routes.TokenRoutes.GENERATE_TOKEN
    listing = routes.TokenRoutes.LIST_TOKENS

    assert generate.path == "/tokens"
    assert listing.path == "/tokens"
    assert generate.method == routes.HttpMethod.POST
    assert listing.method == routes.HttpMethod.GET


def test_every_registered_route_is_a_distinct_method_and_path() -> None:
    pairs = [(route.method, route.path) for route in routes.ALL_ROUTES]

    assert len(pairs) == len(set(pairs))


def test_retryable_post_paths_lookup_by_plain_path_string() -> None:
    assert "/auth/challenge" in routes.RETRYABLE_POST_PATHS
    assert "/auth/sessions" not in routes.RETRYABLE_POST_PATHS
