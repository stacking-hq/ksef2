"""Integration tests for 'Status wysylki i UPO' endpoints.

These tests require:
    - .env.test with KSEF_TEST_SUBJECT_NIP, KSEF_TEST_PERSON_NIP, KSEF_TEST_PERSON_PESEL
    - Access to the KSeF TEST environment

Run with:
    source .env.test && uv run pytest tests/integration/test_invoices_status.py -v -m integration
"""

from __future__ import annotations

import pytest

from ksef2 import Client, Environment, FormSchema
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.core.tools import generate_nip, generate_pesel
from ksef2.xades import generate_test_certificate
from ksef2.domain.models.session import (
    ListSessionsResponse,
    SessionInvoicesResponse,
    SessionInvoiceStatusResponse,
    SessionStatusEnum,
    SessionStatusResponse,
)
from ksef2.domain.models.testdata import (
    Identifier,
    Permission,
)
from tests.integration.conftest import KSeFCredentials
from tests.integration.invoice_payload import invoice_seller_nip
from tests.integration.invoice_payload import load_test_invoice_xml


@pytest.fixture(scope="module")
def session_with_invoice(ksef_credentials: KSeFCredentials):
    """Open an online session, send one invoice, close the session, return context.

    Yields (client, access_token, session_ref, invoice_ref, session).
    """
    client = Client(environment=Environment.TEST)

    seller_nip = invoice_seller_nip(ksef_credentials.subject_nip)
    buyer_nip = generate_nip()
    person_nip = generate_nip()
    person_pesel = generate_pesel()

    with client.testdata.temporal() as temp:
        if seller_nip != ksef_credentials.subject_nip:
            temp.create_subject(
                nip=seller_nip,
                subject_type="enforcement_authority",
                description="Integration test seller",
            )
        temp.create_subject(
            nip=buyer_nip,
            subject_type="enforcement_authority",
            description="Integration test buyer",
        )
        temp.create_person(
            nip=person_nip,
            pesel=person_pesel,
            description="Integration test person",
        )
        temp.grant_permissions(
            permissions=[
                Permission(
                    type="invoice_write",
                    description="Send invoices",
                ),
                Permission(
                    type="introspection",
                    description="Introspect sessions",
                ),
            ],
            grant_to=Identifier(type="nip", value=person_nip),
            in_context_of=Identifier(type="nip", value=seller_nip),
        )

        cert, private_key = generate_test_certificate(seller_nip)
        auth = client.authentication.with_xades(
            nip=seller_nip,
            cert=cert,
            private_key=private_key,
        )
        access_token = auth.access_token

        with auth.online_session(form_code=FormSchema.FA3) as session:
            result = session.send_invoice(invoice_xml=load_test_invoice_xml())
            invoice_ref = result.reference_number
            session_ref = session.get_state().reference_number

            yield client, access_token, session_ref, invoice_ref, session


# ---------------------------------------------------------------------------
# List sessions (via auth.invoice_sessions)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_list_sessions(xades_authenticated_context: tuple[Client, AuthenticatedClient]):
    """List sessions filtered by type."""
    _client, auth = xades_authenticated_context

    response = auth.invoice_sessions.query(session_type="online")

    assert isinstance(response, ListSessionsResponse)
    assert hasattr(response, "sessions")
    assert hasattr(response, "continuation_token")


@pytest.mark.integration
def test_list_sessions_batch(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
):
    """List batch sessions."""
    _client, auth = xades_authenticated_context

    response = auth.invoice_sessions.query(session_type="batch")

    assert isinstance(response, ListSessionsResponse)


@pytest.mark.integration
def test_list_sessions_with_status_filter(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
):
    """List sessions filtered by statuses."""
    _client, auth = xades_authenticated_context

    response = auth.invoice_sessions.query(
        session_type="online",
        statuses=[SessionStatusEnum.SUCCEEDED, SessionStatusEnum.IN_PROGRESS],
    )

    assert isinstance(response, ListSessionsResponse)


# ---------------------------------------------------------------------------
# Session status & invoice status (requires an active/closed session)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_session_status(session_with_invoice):
    """Get status of a session with at least one invoice."""
    _client, _token, _session_ref, _invoice_ref, session = session_with_invoice

    response = session.get_status()

    assert isinstance(response, SessionStatusResponse)
    assert response.status is not None
    assert response.status.code is not None
    assert response.date_created is not None


@pytest.mark.integration
def test_list_session_invoices(session_with_invoice):
    """List invoices within a session."""
    _client, _token, _session_ref, _invoice_ref, session = session_with_invoice

    response = session.list_invoices(page_size=10)

    assert isinstance(response, SessionInvoicesResponse)
    assert len(response.invoices) >= 1


@pytest.mark.integration
def test_get_session_invoice_status(session_with_invoice):
    """Get status of a specific invoice in a session."""
    _client, _token, _session_ref, invoice_ref, session = session_with_invoice

    response = session.get_invoice_status(invoice_reference_number=invoice_ref)

    assert isinstance(response, SessionInvoiceStatusResponse)
    assert response.reference_number == invoice_ref
    assert response.status is not None


@pytest.mark.integration
def test_list_failed_session_invoices(session_with_invoice):
    """List failed invoices within a session (may be empty)."""
    _client, _token, _session_ref, _invoice_ref, session = session_with_invoice

    response = session.list_failed_invoices(page_size=10)

    assert isinstance(response, SessionInvoicesResponse)
    assert hasattr(response, "invoices")
