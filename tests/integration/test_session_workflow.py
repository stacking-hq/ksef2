"""Integration tests for the online session workflow.

Covers: sessions.open_online (context manager), send_invoice, download_invoice,
get_status, list_invoices, list_failed_invoices, get_invoice_upo_by_ksef_number,
get_invoice_upo_by_reference, get_state, sessions.resume.

Run with:
    uv run pytest tests/integration/test_session_workflow.py -v -m integration
"""

from __future__ import annotations

import time

import pytest

from ksef2 import Client, Environment, FormSchema
from ksef2.clients.online import OnlineSessionClient
from ksef2.core.tools import generate_nip, generate_pesel
from ksef2.xades import generate_test_certificate
from ksef2.domain.models.session import OnlineSessionState, SessionStatusResponse
from ksef2.domain.models.testdata import (
    Identifier,
    Permission,
)
from ksef2.endpoints.session import SessionEndpoints
from tests.integration.conftest import KSeFCredentials
from tests.integration.invoice_payload import invoice_seller_nip
from tests.integration.invoice_payload import load_test_invoice_xml


@pytest.fixture(scope="module")
def workflow_context(ksef_credentials: KSeFCredentials):
    """Full workflow: testdata → auth → open session → send invoice.

    Yields a dict with all context needed by individual tests.
    The session stays open for the duration of the module.
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
                description="Workflow test seller",
            )
        temp.create_subject(
            nip=buyer_nip,
            subject_type="enforcement_authority",
            description="Workflow test buyer",
        )
        temp.create_person(
            nip=person_nip,
            pesel=person_pesel,
            description="Workflow test person",
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

            # Give KSeF time to process the invoice
            time.sleep(5)

            invoices_list = session.list_invoices()

            yield {
                "client": client,
                "auth": auth,
                "access_token": access_token,
                "session": session,
                "invoice_ref": result.reference_number,
                "invoices_list": invoices_list,
            }


# ---------------------------------------------------------------------------
# get_state
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_state_returns_session_state(workflow_context):
    """get_state returns a SessionState with all required fields."""
    session: OnlineSessionClient = workflow_context["session"]

    state = session.get_state()

    assert isinstance(state, OnlineSessionState)
    assert state.reference_number
    assert state.access_token
    assert state.aes_key
    assert state.iv
    assert state.valid_until is not None
    assert state.form_code == FormSchema.FA3


# ---------------------------------------------------------------------------
# download_invoice
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_download_invoice_returns_xml_bytes(workflow_context):
    """download_invoice returns non-empty XML bytes."""
    from ksef2.clients.authenticated import AuthenticatedClient

    auth: AuthenticatedClient = workflow_context["auth"]
    invoices_list = workflow_context["invoices_list"]

    if not invoices_list.invoices or not invoices_list.invoices[0].ksef_number:
        pytest.skip("No processed invoice with ksef_number available")

    ksef_number = invoices_list.invoices[0].ksef_number
    xml_bytes = auth.invoices.wait_for_invoice_download(ksef_number=ksef_number)

    assert isinstance(xml_bytes, bytes)
    assert len(xml_bytes) > 0


# ---------------------------------------------------------------------------
# get_invoice_upo_by_ksef_number
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_invoice_upo_by_ksef_number(workflow_context):
    """UPO by KSeF number returns non-empty bytes."""
    session: OnlineSessionClient = workflow_context["session"]
    invoices_list = workflow_context["invoices_list"]

    if not invoices_list.invoices or not invoices_list.invoices[0].ksef_number:
        pytest.skip("No processed invoice with ksef_number available")

    ksef_number = invoices_list.invoices[0].ksef_number
    upo = session.get_invoice_upo_by_ksef_number(ksef_number=ksef_number)

    assert isinstance(upo, bytes)
    assert len(upo) > 0


# ---------------------------------------------------------------------------
# get_invoice_upo_by_reference
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_invoice_upo_by_reference(workflow_context):
    """UPO by invoice reference number returns non-empty bytes."""
    session: OnlineSessionClient = workflow_context["session"]
    invoice_ref = workflow_context["invoice_ref"]

    upo = session.get_invoice_upo_by_reference(invoice_reference_number=invoice_ref)

    assert isinstance(upo, bytes)
    assert len(upo) > 0


# ---------------------------------------------------------------------------
# sessions.resume
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_resume_session_from_state(workflow_context):
    """Resume a session from serialized state and use it."""
    from ksef2.clients.authenticated import AuthenticatedClient

    auth: AuthenticatedClient = workflow_context["auth"]
    session: OnlineSessionClient = workflow_context["session"]

    state = session.get_state()

    # Round-trip through JSON serialization
    state_json = state.model_dump_json()
    restored_state = OnlineSessionState.model_validate_json(state_json)

    resumed = auth.resume_online_session(state=restored_state)

    assert isinstance(resumed, OnlineSessionClient)

    # The resumed session should be able to query status
    status = resumed.get_status()
    assert isinstance(status, SessionStatusResponse)
    assert status.status is not None


# ---------------------------------------------------------------------------
# GetSessionUpoEndpoint - collective UPO for session
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_session_upo_by_reference(ksef_credentials: KSeFCredentials):
    """A closed online session exposes a collective UPO by reference number."""
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
                description="Session UPO test seller",
            )
        temp.create_subject(
            nip=buyer_nip,
            subject_type="enforcement_authority",
            description="Session UPO test buyer",
        )
        temp.create_person(
            nip=person_nip,
            pesel=person_pesel,
            description="Session UPO test person",
        )
        temp.grant_permissions(
            permissions=[
                Permission(type="invoice_write", description="Send invoices"),
                Permission(type="introspection", description="Inspect sessions"),
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

        with auth.online_session(form_code=FormSchema.FA3) as session:
            _ = session.send_invoice(invoice_xml=load_test_invoice_xml())
            state = session.get_state()

        resumed = auth.resume_online_session(state=state)

        deadline = time.monotonic() + 90.0
        status = resumed.get_status()
        while (
            status.upo is None or not status.upo.pages
        ) and time.monotonic() < deadline:
            time.sleep(2.0)
            status = resumed.get_status()

        assert status.upo is not None
        assert status.upo.pages

        upo_reference_number = status.upo.pages[0].reference_number
        upo_xml = SessionEndpoints(auth._authed_transport).get_session_upo(
            state.reference_number,
            upo_reference_number,
        )

        assert isinstance(upo_xml, bytes)
        assert len(upo_xml) > 0
