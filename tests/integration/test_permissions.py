"""Integration tests for permissions endpoints.

These tests require:
    - .env.test with KSEF_TEST_SUBJECT_NIP, KSEF_TEST_PERSON_NIP, KSEF_TEST_PERSON_PESEL
    - Access to the KSeF TEST environment

Run with:
    source .env.test && uv run pytest tests/integration/test_permissions.py -v -m integration
"""

import time
from typing import TYPE_CHECKING, Generator, TypedDict

import pytest

from ksef2 import Client, FormSchema
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._clients.online import OnlineSessionClient
from ksef2._core.tools import generate_nip
from ksef2.xades import generate_test_certificate
from ksef2._domain.models.permissions import (
    AuthorizationPermissionsQuery,
    EntityPermission,
    EuEntityPermissionsQuery,
    PersonalPermissionsQuery,
    PersonPermissionDetail,
    PersonPermissionsQuery,
    SubordinateEntityRolesQuery,
    SubunitPermissionsQuery,
)


if TYPE_CHECKING:
    from tests.integration.conftest import KSeFCredentials

PermissionContext = TypedDict(
    "PermissionContext",
    {
        "client": Client,
        "auth": AuthenticatedClient,
        "session": OnlineSessionClient,
        "seller_nip": str,
    },
)


@pytest.fixture(scope="module")
def permissions_context(
    real_client: Client,
    ksef_credentials: "KSeFCredentials",
) -> Generator[PermissionContext, None, None]:
    """Create an authenticated session using existing credentials.

    Uses the subject from ksef_credentials to authenticate.
    Yields a dict with client, auth, session, seller_nip.
    """
    client = real_client
    seller_nip = ksef_credentials.subject_nip

    cert, private_key = generate_test_certificate(seller_nip)
    auth = client.authentication.with_xades(
        nip=seller_nip,
        cert=cert,
        private_key=private_key,
    )

    with auth.online_session(form_code=FormSchema.FA3) as session:
        context: PermissionContext = {
            "client": client,
            "auth": auth,
            "session": session,
            "seller_nip": seller_nip,
        }

        yield context


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_attachment_permission_status(permissions_context: PermissionContext):
    """Get attachment permission status."""
    auth = permissions_context["auth"]

    response = auth.permissions.get_attachment_permission_status()

    assert response is not None
    assert hasattr(response, "is_attachment_allowed")
    assert isinstance(response.is_attachment_allowed, bool)


@pytest.mark.integration
def test_list_entity_roles(permissions_context: PermissionContext):
    """Get entity roles."""
    auth = permissions_context["auth"]

    roles = auth.permissions.list_entity_roles().first_page()

    assert isinstance(roles, list)


# ---------------------------------------------------------------------------
# Query endpoints (POST)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_list_authorizations(permissions_context: PermissionContext):
    """Query authorization permissions."""
    auth = permissions_context["auth"]

    query = AuthorizationPermissionsQuery(
        query_type="granted",
    )

    items = auth.permissions.list_authorizations(query).first_page()

    assert isinstance(items, list)


@pytest.mark.integration
def test_list_eu_entities(permissions_context: PermissionContext):
    """Query EU entity permissions."""
    auth = permissions_context["auth"]

    query = EuEntityPermissionsQuery()

    items = auth.permissions.list_eu_entities(query).first_page()

    assert isinstance(items, list)


@pytest.mark.integration
def test_list_personal(permissions_context: PermissionContext):
    """Query personal permissions."""
    auth = permissions_context["auth"]

    query = PersonalPermissionsQuery()

    items = auth.permissions.list_personal(query).first_page()

    assert isinstance(items, list)


@pytest.mark.integration
def test_list_persons(permissions_context: PermissionContext):
    """Query person permissions and verify domain response request."""
    auth = permissions_context["auth"]

    query = PersonPermissionsQuery(
        query_type="in_context",
    )

    permissions = auth.permissions.list_persons(query).first_page()

    assert isinstance(permissions, list)

    for perm in permissions:
        assert isinstance(perm, PersonPermissionDetail)
        assert perm.id
        assert perm.author_type is not None
        assert perm.authorized_type is not None
        assert perm.permission_state is not None
        assert perm.permission_type is not None
        assert perm.description
        assert perm.start_date is not None
        assert isinstance(perm.can_delegate, bool)


@pytest.mark.integration
def test_list_subordinate_entities(permissions_context: PermissionContext):
    """Query subordinate entity roles."""
    auth = permissions_context["auth"]

    query = SubordinateEntityRolesQuery()

    items = auth.permissions.list_subordinate_entities(query).first_page()

    assert isinstance(items, list)


@pytest.mark.integration
def test_list_subunits(permissions_context: PermissionContext):
    """Query subunit permissions."""
    auth = permissions_context["auth"]

    query = SubunitPermissionsQuery()

    items = auth.permissions.list_subunits(query).first_page()

    assert isinstance(items, list)


# ---------------------------------------------------------------------------
# Grant endpoints
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_grant_entity_permission(permissions_context: PermissionContext):
    """Grant permission to an entity."""
    auth = permissions_context["auth"]
    buyer_nip = generate_nip()

    response = auth.permissions.grant_entity(
        subject_value=buyer_nip,
        permissions=[
            EntityPermission(type="invoice_read", can_delegate=False),
        ],
        description="Test entity permission grant",
        entity_name="Test Buyer Entity",
    )

    assert response.reference_number

    operation_status = response.wait()

    assert operation_status.status.code == 200

    # The data getter reads the same status by reference number.
    assert (
        auth.permissions.get_operation_status(
            reference_number=response.reference_number,
        ).status.code
        == 200
    )


@pytest.mark.integration
def test_grant_authorization_permission(permissions_context: PermissionContext):
    """Grant authorization permission."""
    auth = permissions_context["auth"]
    buyer_nip = generate_nip()

    response = auth.permissions.grant_authorization(
        subject_type="nip",
        subject_value=buyer_nip,
        permission="self_invoicing",
        description="Test authorization grant",
        entity_name="Test Authorization Entity",
    )

    assert response.reference_number

    _ = response.wait()


@pytest.mark.integration
def test_grant_person_permission(permissions_context: PermissionContext):
    """Grant permission to a person."""
    auth = permissions_context["auth"]
    person_nip = generate_nip()

    response = auth.permissions.grant_person(
        subject_type="nip",
        subject_value=person_nip,
        permissions=["invoice_read"],
        description="Test person permission grant",
        first_name="Test",
        last_name="Person",
    )

    assert response.reference_number

    _ = response.wait()


@pytest.mark.integration
def test_grant_subunit_permission(permissions_context: PermissionContext):
    """Grant permission to a subunit."""
    auth = permissions_context["auth"]
    seller_nip = permissions_context["seller_nip"]

    response = auth.permissions.grant_subunit(
        subject_type="nip",
        subject_value=seller_nip,
        context_type="nip",
        context_value=seller_nip,
        description="Test subunit permission grant",
        first_name="Test",
        last_name="User",
    )

    assert response.reference_number

    _ = response.wait()


# ---------------------------------------------------------------------------
# Revoke endpoints
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_revoke_authorization_permission(permissions_context: PermissionContext):
    """Grant and then revoke an authorization permission."""
    auth = permissions_context["auth"]
    buyer_nip = generate_nip()

    # First, grant an authorization permission
    grant_response = auth.permissions.grant_authorization(
        subject_type="nip",
        subject_value=buyer_nip,
        permission="self_invoicing",
        description="Test authorization for revoke",
        entity_name="Test Entity for Revoke",
    )

    assert grant_response.reference_number

    _ = grant_response.wait()

    # List authorizations to find the one we just created
    from ksef2._domain.models.pagination import OffsetPaginationParams

    deadline = time.monotonic() + 60.0
    permission_id = None
    while time.monotonic() < deadline and permission_id is None:
        for grant in auth.permissions.list_authorizations(
            AuthorizationPermissionsQuery(query_type="granted"),
            params=OffsetPaginationParams(page_size=100),
        ):
            if grant.description == "Test authorization for revoke":
                permission_id = grant.id
                break
        if permission_id is None:
            time.sleep(2.0)

    assert permission_id is not None

    revoke_response = auth.permissions.revoke_authorization(
        permission_id=permission_id,
    )

    assert revoke_response.reference_number

    _ = revoke_response.wait()


@pytest.mark.integration
def test_revoke_permission(permissions_context: PermissionContext):
    """Grant and then revoke a common permission."""
    auth = permissions_context["auth"]
    person_nip = generate_nip()

    grant_response = auth.permissions.grant_person(
        subject_type="nip",
        subject_value=person_nip,
        permissions=["invoice_read"],
        description="Test common permission for revoke",
        first_name="Test",
        last_name="Person",
    )

    assert grant_response.reference_number

    _ = grant_response.wait()

    # Query personal permissions to find the one we just created
    from ksef2._domain.models.pagination import OffsetPaginationParams

    deadline = time.monotonic() + 60.0
    permission_id = None
    while time.monotonic() < deadline and permission_id is None:
        for perm in auth.permissions.list_persons(
            PersonPermissionsQuery(
                query_type="in_context",
                authorized_type="nip",
                authorized_value=person_nip,
                permission_types=["invoice_read"],
            ),
            params=OffsetPaginationParams(page_size=100),
        ):
            if perm.description == "Test common permission for revoke":
                permission_id = perm.id
                break
        if permission_id is None:
            time.sleep(2.0)

    assert permission_id is not None

    revoke_response = auth.permissions.revoke(
        permission_id=permission_id,
    )

    assert revoke_response.reference_number

    _ = revoke_response.wait()
