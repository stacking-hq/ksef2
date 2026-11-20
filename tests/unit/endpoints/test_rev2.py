from datetime import datetime, timezone

from ksef2 import Environment
from ksef2.raw import RawAuthenticatedClient, RawClient, spec
from tests.unit.fakes.transport import FakeTransport

REFERENCE = "0" * 36
VALID_FROM = datetime(2027, 1, 1, tzinfo=timezone.utc)


def test_rev2_token_workflow(fake_transport: FakeTransport) -> None:
    auth = RawAuthenticatedClient(
        transport=fake_transport,
        authed_transport=fake_transport,
        environment=Environment.TEST,
    )
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

    generated = auth.tokens.generate_token_rev2(
        spec.GenerateTokenRequestRev2(
            permissions=[spec.TokenPermissionType.InvoiceRead],
            description="reporting",
            validFrom=VALID_FROM,
        )
    )
    assert generated.referenceNumber == REFERENCE
    assert generated.token == "secret"
    page = auth.tokens.list_tokens_rev2(
        continuation_token="previous",
        status=[
            spec.TokenStatusFilterRev2.AwaitingApproval,
            spec.TokenStatusFilterRev2.NotYetActive,
        ],
        validFrom=VALID_FROM,
    )
    assert page.continuationToken == "next"
    status = auth.tokens.token_status_rev2(REFERENCE)
    assert status.validFrom == VALID_FROM
    assert status.status.code is spec.TokenStatusRev2Code.AwaitingApproval
    auth.tokens.approve_token(REFERENCE)
    auth.testdata.expire_token_approval(REFERENCE)

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


def test_rev2_auth_status_and_sessions(fake_transport: FakeTransport) -> None:
    root = RawClient(fake_transport, Environment.TEST)
    auth = RawAuthenticatedClient(
        transport=fake_transport,
        authed_transport=fake_transport,
        environment=Environment.TEST,
    )
    operation = {
        "startDate": "2027-01-01T00:00:00Z",
        "authenticationMethodInfo": {
            "category": {
                "code": "XadesSignature",
                "rawCode": "XadesSignature",
                "displayName": "XAdES",
            },
            "code": "QualifiedSignature",
            "displayName": "Qualified signature",
        },
        "status": {"code": 200, "description": "Authenticated"},
    }
    fake_transport.enqueue({**operation, "referenceNumber": REFERENCE})
    fake_transport.enqueue(
        {"items": [{**operation, "referenceNumber": REFERENCE, "isCurrent": True}]}
    )

    status = root.auth.auth_status_rev2("temporary", REFERENCE)
    assert status.authenticationMethodInfo.code == "QualifiedSignature"
    sessions = auth.auth.list_sessions_rev2(continuation_token="previous", pageSize=10)
    assert sessions.items[0].referenceNumber == REFERENCE
    assert sessions.items[0].isCurrent is True

    status_call, sessions_call = fake_transport.calls
    assert (status_call.method, status_call.path) == ("GET", f"/auth/rev2/{REFERENCE}")
    assert status_call.headers == {"Authorization": "Bearer temporary"}
    assert (sessions_call.method, sessions_call.path) == ("GET", "/auth/sessions/rev2")
    assert sessions_call.headers == {"x-continuation-token": "previous"}
    assert sessions_call.params is not None
    assert sessions_call.params["pageSize"] == "10"
