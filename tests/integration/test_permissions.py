"""Integration tests for permissions endpoints.

These tests require:
    - .env.test with KSEF_TEST_SUBJECT_NIP, KSEF_TEST_PERSON_NIP, KSEF_TEST_PERSON_PESEL
    - Access to the KSeF TEST environment

Run with:
    source .env.test && uv run pytest tests/integration/test_permissions.py -v -m integration
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Generator, TypedDict

import pytest

from ksef2 import Client, FormSchema
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.clients.online import OnlineSessionClient
from ksef2.core.tools import generate_nip
from ksef2.xades import generate_test_certificate
from ksef2.domain.models.permissions import (
    AuthorizationPermissionsQuery,
    AuthorizationPermissionsQueryResponse,
    EntityPermission,
    EuEntityPermissionsQuery,
    EuEntityPermissionsQueryResponse,
    PersonalPermissionsQuery,
    PersonalPermissionsQueryResponse,
    PersonPermissionDetail,
    PersonPermissionsQuery,
    PersonPermissionsQueryResponse,
    SubordinateEntityRolesQuery,
    SubordinateEntityRolesQueryResponse,
    SubunitPermissionsQuery,
    SubunitPermissionsQueryResponse,
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


def _wait_for_permission_operation(
    auth: AuthenticatedClient,
    *,
    reference_number: str,
    timeout: float = 60.0,
    poll_interval: float = 2.0,
) -> None:
    deadline = time.monotonic() + timeout
    last_code = None

    while time.monotonic() < deadline:
        status = auth.permissions.get_operation_status(
            reference_number=reference_number,
        )
        last_code = status.status.code
        if last_code == 200:
            return
        if last_code >= 400:
            raise AssertionError(
                f"Permission operation failed: {last_code} {status.status.description}"
            )
        time.sleep(poll_interval)

    raise AssertionError(
        f"Permission operation did not finish within {timeout} seconds; "
        f"last status={last_code}"
    )


@pytest.fixture(scope="module")
def permissions_context(
    real_client: Client,
    ksef_credentials: KSeFCredentials,
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
def test_get_entity_roles(permissions_context: PermissionContext):
    """Get entity roles."""
    auth = permissions_context["auth"]

    response = auth.permissions.get_entity_roles()

    assert response is not None
    assert hasattr(response, "roles")
    assert hasattr(response, "has_more")
    assert isinstance(response.roles, list)
    assert isinstance(response.has_more, bool)


# ---------------------------------------------------------------------------
# Query endpoints (POST)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_query_authorizations(permissions_context: PermissionContext):
    """Query authorization permissions."""
    auth = permissions_context["auth"]

    query = AuthorizationPermissionsQuery(
        query_type="granted",
    )

    response = auth.permissions.query_authorizations(query=query)

    assert isinstance(response, AuthorizationPermissionsQueryResponse)
    assert isinstance(response.authorization_grants, list)
    assert isinstance(response.has_more, bool)


@pytest.mark.integration
def test_query_eu_entities(permissions_context: PermissionContext):
    """Query EU entity permissions."""
    auth = permissions_context["auth"]

    query = EuEntityPermissionsQuery()

    response = auth.permissions.query_eu_entities(query=query)

    assert isinstance(response, EuEntityPermissionsQueryResponse)
    assert isinstance(response.permissions, list)
    assert isinstance(response.has_more, bool)


@pytest.mark.integration
def test_query_personal(permissions_context: PermissionContext):
    """Query personal permissions."""
    auth = permissions_context["auth"]

    query = PersonalPermissionsQuery()

    response = auth.permissions.query_personal(query=query)

    assert isinstance(response, PersonalPermissionsQueryResponse)
    assert isinstance(response.permissions, list)
    assert isinstance(response.has_more, bool)


@pytest.mark.integration
def test_query_persons(permissions_context: PermissionContext):
    """Query person permissions and verify domain response request."""
    auth = permissions_context["auth"]

    query = PersonPermissionsQuery(
        query_type="in_context",
    )

    response = auth.permissions.query_persons(query=query)

    assert isinstance(response, PersonPermissionsQueryResponse)
    assert isinstance(response.permissions, list)
    assert isinstance(response.has_more, bool)

    for perm in response.permissions:
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
def test_query_subordinate_entities(permissions_context: PermissionContext):
    """Query subordinate entity roles."""
    auth = permissions_context["auth"]

    query = SubordinateEntityRolesQuery()

    response = auth.permissions.query_subordinate_entities(query=query)

    assert isinstance(response, SubordinateEntityRolesQueryResponse)
    assert isinstance(response.roles, list)
    assert isinstance(response.has_more, bool)


@pytest.mark.integration
def test_query_subunits(permissions_context: PermissionContext):
    """Query subunit permissions."""
    auth = permissions_context["auth"]

    query = SubunitPermissionsQuery()

    response = auth.permissions.query_subunits(query=query)

    assert isinstance(response, SubunitPermissionsQueryResponse)
    assert isinstance(response.permissions, list)
    assert isinstance(response.has_more, bool)


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

    assert response is not None
    assert hasattr(response, "reference_number")
    assert response.reference_number

    time.sleep(3)

    operation_status = auth.permissions.get_operation_status(
        reference_number=response.reference_number,
    )

    assert operation_status is not None
    assert operation_status.status is not None
    assert operation_status.status.code is not None


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

    assert response is not None
    assert hasattr(response, "reference_number")
    assert response.reference_number


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

    assert response is not None
    assert hasattr(response, "reference_number")
    assert response.reference_number


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

    assert response is not None
    assert hasattr(response, "reference_number")
    assert response.reference_number


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

    _wait_for_permission_operation(
        auth,
        reference_number=grant_response.reference_number,
    )

    # Query authorizations to find the one we just created
    from ksef2.domain.models.pagination import OffsetPaginationParams

    deadline = time.monotonic() + 60.0
    permission_id = None
    while time.monotonic() < deadline and permission_id is None:
        query_response = auth.permissions.query_authorizations(
            query=AuthorizationPermissionsQuery(query_type="granted"),
            params=OffsetPaginationParams(page_size=100),
        )
        for grant in query_response.authorization_grants:
            if grant.description == "Test authorization for revoke":
                permission_id = grant.id
                break
        if permission_id is None:
            time.sleep(2.0)

    assert permission_id is not None

    revoke_response = auth.permissions.revoke_authorization(
        permission_id=permission_id,
    )

    assert revoke_response is not None
    assert hasattr(revoke_response, "reference_number")
    assert revoke_response.reference_number


@pytest.mark.integration
def test_revoke_common_permission(permissions_context: PermissionContext):
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

    _wait_for_permission_operation(
        auth,
        reference_number=grant_response.reference_number,
    )

    # Query personal permissions to find the one we just created
    from ksef2.domain.models.pagination import OffsetPaginationParams

    deadline = time.monotonic() + 60.0
    permission_id = None
    while time.monotonic() < deadline and permission_id is None:
        query_response = auth.permissions.query_persons(
            query=PersonPermissionsQuery(
                query_type="in_context",
                authorized_type="nip",
                authorized_value=person_nip,
                permission_types=["invoice_read"],
            ),
            params=OffsetPaginationParams(page_size=100),
        )
        for perm in query_response.permissions:
            if perm.description == "Test common permission for revoke":
                permission_id = perm.id
                break
        if permission_id is None:
            time.sleep(2.0)

    assert permission_id is not None

    revoke_response = auth.permissions.revoke_common(
        permission_id=permission_id,
    )

    assert revoke_response is not None
    assert hasattr(revoke_response, "reference_number")
    assert revoke_response.reference_number
