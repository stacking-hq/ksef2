from datetime import datetime, timezone

import pytest

from ksef2 import Environment
from ksef2.clients import (
    AsyncTestDataClient,
    AsyncTokensClient,
    TestDataClient as SandboxClient,
    TokensClient,
)
from ksef2.models import TokenListParams
from ksef2.raw import (
    AsyncRawAuthenticatedClient,
    AsyncRawClient,
    ListTokensRev2QueryParams,
    RawAuthenticatedClient,
    RawClient,
    spec,
)
from ksef2.raw.mappers.auth import from_spec
from tests.unit.fakes.transport import AsyncFakeTransport
from tests.unit.factories.tokens import (
    QueryTokensResponseItemRev2Factory,
    token_status_rev2,
)
from tests.unit.support.flavors import Flavor
from ksef2._core.exceptions import KSeFArgumentError

REFERENCE = "0" * 36
VALID_FROM = datetime(2027, 1, 1, tzinfo=timezone.utc)


def _raw_clients(
    flavor: Flavor,
) -> tuple[
    RawClient | AsyncRawClient, RawAuthenticatedClient | AsyncRawAuthenticatedClient
]:
    transport = flavor.transport
    if isinstance(transport, AsyncFakeTransport):
        return (
            AsyncRawClient(transport, Environment.TEST),
            AsyncRawAuthenticatedClient(
                transport=transport,
                authed_transport=transport,
                environment=Environment.TEST,
            ),
        )
    return (
        RawClient(transport, Environment.TEST),
        RawAuthenticatedClient(
            transport=transport,
            authed_transport=transport,
            environment=Environment.TEST,
        ),
    )


def test_rev2_token_workflow(flavor: Flavor) -> None:
    _, auth = _raw_clients(flavor)
    fake_transport = flavor.transport
    fake_transport.enqueue({"referenceNumber": REFERENCE, "token": "secret"}, 202)
    fake_transport.enqueue({"tokens": [], "continuationToken": "next"})
    token_status = {
        "referenceNumber": REFERENCE,
        "authorIdentifier": {
            "type": {"code": "Nip", "rawCode": "Nip", "displayName": "NIP"},
            "value": "1111111111",
        },
        "contextIdentifier": {
            "type": {"code": "Nip", "rawCode": "Nip", "displayName": "NIP"},
            "value": "2222222222",
        },
        "description": "reporting",
        "requestedPermissions": [],
        "dateCreated": "2026-12-31T12:00:00Z",
        "validFrom": "2027-01-01T00:00:00Z",
        "validTo": "2027-04-01T00:00:00Z",
        "status": {
            "code": "AwaitingApproval",
            "rawCode": "AwaitingApproval",
            "displayName": "Awaiting approval",
        },
    }
    fake_transport.enqueue(token_status)
    fake_transport.enqueue(status_code=204)
    fake_transport.enqueue(status_code=204)

    generated = flavor.run(
        auth.tokens.generate_token_rev2(
            spec.GenerateTokenRequestRev2(
                permissions=[spec.TokenPermissionType.InvoiceRead],
                description="reporting",
                validFrom=VALID_FROM,
            )
        )
    )
    assert generated.referenceNumber == REFERENCE
    assert generated.token == "secret"
    filters: ListTokensRev2QueryParams = {
        "status": (spec.TokenStatusFilterRev2.AwaitingApproval, "NotYetActive"),
        "validFrom": "2027-01-01T00:00:00Z",
    }
    page = flavor.run(
        auth.tokens.list_tokens_rev2(continuation_token="previous", **filters)
    )
    assert page.continuationToken == "next"
    status = flavor.run(auth.tokens.token_status_rev2(REFERENCE))
    assert status.validFrom == VALID_FROM
    assert status.status.code is spec.TokenStatusRev2Code.AwaitingApproval
    flavor.run(auth.tokens.approve_token(REFERENCE))
    flavor.run(auth.testdata.expire_token_approval(REFERENCE))

    create, listing, get_status, approve, expire = fake_transport.calls
    assert (create.method, create.path) == ("POST", "/tokens/rev2")
    assert create.json == {
        "permissions": ["InvoiceRead"],
        "description": "reporting",
        "validFrom": "2027-01-01T00:00:00Z",
    }
    assert (listing.method, listing.path) == ("GET", "/tokens/rev2")
    assert listing.headers == {"x-continuation-token": "previous"}
    assert listing.params is not None
    assert listing.params.get_list("status") == ["AwaitingApproval", "NotYetActive"]
    assert listing.params["validFrom"] == "2027-01-01T00:00:00+00:00"
    assert (get_status.method, get_status.path) == ("GET", f"/tokens/rev2/{REFERENCE}")
    assert (approve.method, approve.path) == ("POST", f"/tokens/{REFERENCE}/approve")
    assert (expire.method, expire.path) == (
        "POST",
        f"/testdata/tokens/{REFERENCE}/expire-approval",
    )
    assert approve.json is expire.json is None


def test_rev2_auth_status_and_sessions(flavor: Flavor) -> None:
    root, auth = _raw_clients(flavor)
    fake_transport = flavor.transport
    operation = {
        "startDate": "2027-01-01T00:00:00Z",
        "authenticationMethodInfo": {
            "category": {
                "code": "XadesSignature",
                "rawCode": "XadesSignature",
                "displayName": "XAdES",
            },
            "code": "xades.qualified-signature",
            "displayName": "Qualified signature",
        },
        "status": {"code": 200, "description": "Authenticated"},
    }
    fake_transport.enqueue({**operation, "referenceNumber": REFERENCE})
    fake_transport.enqueue(
        {"items": [{**operation, "referenceNumber": REFERENCE, "isCurrent": True}]}
    )

    status = flavor.run(root.auth.auth_status_rev2("temporary", REFERENCE))
    assert status.authenticationMethodInfo.code == "xades.qualified-signature"
    sessions = flavor.run(
        auth.auth.list_sessions_rev2(continuation_token="previous", pageSize=10)
    )
    assert sessions.items[0].referenceNumber == REFERENCE
    assert sessions.items[0].isCurrent is True
    assert from_spec(status).authentication_method_category == "xades_signature"
    assert from_spec(sessions).items[0].is_current is True

    status_call, sessions_call = fake_transport.calls
    assert (status_call.method, status_call.path) == ("GET", f"/auth/rev2/{REFERENCE}")
    assert status_call.headers == {"Authorization": "Bearer temporary"}
    assert (sessions_call.method, sessions_call.path) == ("GET", "/auth/sessions/rev2")
    assert sessions_call.headers == {"x-continuation-token": "previous"}
    assert sessions_call.params is not None
    assert sessions_call.params["pageSize"] == "10"


def test_high_level_token_approval_and_test_expiry(flavor: Flavor) -> None:
    tokens = flavor.client(TokensClient, AsyncTokensClient)
    testdata = flavor.client(SandboxClient, AsyncTestDataClient)
    for operation in (tokens.approve, testdata.expire_token_approval):
        with pytest.raises(KSeFArgumentError):
            flavor.run(operation(reference_number=" "))

    assert flavor.transport.calls == []
    flavor.transport.enqueue(status_code=204)
    flavor.transport.enqueue(status_code=204)

    flavor.run(tokens.approve(reference_number=REFERENCE))
    flavor.run(testdata.expire_token_approval(reference_number=REFERENCE))

    assert [(call.method, call.path) for call in flavor.transport.calls] == [
        ("POST", f"/tokens/{REFERENCE}/approve"),
        ("POST", f"/testdata/tokens/{REFERENCE}/expire-approval"),
    ]


def test_high_level_token_list_filters_and_failure_details(flavor: Flavor) -> None:
    tokens = flavor.client(TokensClient, AsyncTokensClient)
    token = QueryTokensResponseItemRev2Factory.build(
        status=token_status_rev2(spec.TokenStatusRev2Code.ApprovalExpired),
        failure=spec.TokenFailureRev2(code="Expired", description="Approval expired"),
    )
    flavor.transport.enqueue({"tokens": [token.model_dump(mode="json")]})
    params = TokenListParams(
        status=["approval_expired"],
        author_identifier="1234567890",
        author_identifier_type="nip",
        valid_to=VALID_FROM,
    )

    items = flavor.run(tokens.list(params=params).first_page())

    call = flavor.transport.calls[0]
    assert call.path == "/tokens/rev2"
    assert call.params is not None
    assert call.params["status"] == "ApprovalExpired"
    assert call.params["authorIdentifierType"] == "Nip"
    assert call.params["validTo"] == "2027-01-01T00:00:00+00:00"
    assert items[0].status == "approval_expired"
    assert items[0].valid_to == token.validTo
    assert items[0].failure.code == "Expired"
