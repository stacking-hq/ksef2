"""Integration tests for the online session workflow.

Covers: sessions.open_online (context manager), send_invoice and its handle,
invoices.download, get_status, list_invoices, list_failed_invoices,
download_invoice_upo (by KSeF number and by reference), the session wait() and
download_upo(), resume_state, sessions.resume.

Run with:
    uv run pytest tests/integration/test_session_workflow.py -v -m integration
"""

import pytest

from ksef2 import Client, Environment, FormSchema
from ksef2._clients.online import OnlineSessionClient
from ksef2._core.tools import generate_nip, generate_pesel
from ksef2.xades import generate_test_certificate
from ksef2._domain.models.session import (
    OnlineSessionResumeState,
    SessionStatusResponse,
)
from ksef2._domain.models.testdata import (
    Identifier,
    Permission,
)
from tests.integration.conftest import KSeFCredentials
from scripts.examples._common import example_invoice_xml
from tests.integration.invoice_payload import invoice_seller_nip


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

        with auth.online_session(form_code=FormSchema.FA3) as session:
            submission = session.send_invoice(
                example_invoice_xml(seller_nip=seller_nip)
            )
            status = submission.wait(timeout=90.0)

            invoices_list = session.list_invoices()

            yield {
                "client": client,
                "auth": auth,
                "session": session,
                "submission": submission,
                "invoice_ref": submission.reference_number,
                "ksef_number": status.ksef_number,
                "invoices_list": invoices_list,
            }


# ---------------------------------------------------------------------------
# resume_state
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_resume_state_returns_session_state(workflow_context):
    """resume_state returns a session state with all required fields."""
    session: OnlineSessionClient = workflow_context["session"]

    state = session.resume_state()

    assert isinstance(state, OnlineSessionResumeState)
    assert state.reference_number
    assert state.aes_key.get_secret_value()
    assert state.iv.get_secret_value()
    assert state.valid_until is not None
    assert state.form_code == FormSchema.FA3


# ---------------------------------------------------------------------------
# download_invoice
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_download_invoice_returns_xml_bytes(workflow_context):
    """invoices.download polls until the invoice is available and returns XML bytes."""
    from ksef2._clients.authenticated import AuthenticatedClient

    auth: AuthenticatedClient = workflow_context["auth"]
    ksef_number = workflow_context["ksef_number"]

    xml_bytes = auth.invoices.download(ksef_number, timeout=120.0)

    assert isinstance(xml_bytes, bytes)
    assert len(xml_bytes) > 0


# ---------------------------------------------------------------------------
# download_invoice_upo
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_download_invoice_upo_by_ksef_number(workflow_context):
    """UPO by KSeF number returns non-empty bytes."""
    session: OnlineSessionClient = workflow_context["session"]
    ksef_number = workflow_context["ksef_number"]

    upo = session.download_invoice_upo(ksef_number=ksef_number)

    assert isinstance(upo, bytes)
    assert len(upo) > 0


# ---------------------------------------------------------------------------
# download_invoice_upo by reference, and the handle
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_download_invoice_upo_by_reference(workflow_context):
    """UPO by invoice reference number returns non-empty bytes."""
    session: OnlineSessionClient = workflow_context["session"]
    invoice_ref = workflow_context["invoice_ref"]

    upo = session.download_invoice_upo(reference_number=invoice_ref)

    assert isinstance(upo, bytes)
    assert len(upo) > 0


@pytest.mark.integration
def test_submission_handle_downloads_its_upo(workflow_context):
    """The send_invoice handle exposes the reference number and downloads the UPO."""
    submission = workflow_context["submission"]

    assert submission.reference_number == workflow_context["invoice_ref"]
    upo = submission.download_upo()

    assert isinstance(upo, bytes)
    assert len(upo) > 0


# ---------------------------------------------------------------------------
# sessions.resume
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_resume_session_from_resume_state(workflow_context):
    """Resume a session from serialized state and use it."""
    from ksef2._clients.authenticated import AuthenticatedClient

    auth: AuthenticatedClient = workflow_context["auth"]
    session: OnlineSessionClient = workflow_context["session"]

    state = session.resume_state()

    # Round-trip through JSON serialization
    state_json = state.to_json()
    restored_state = OnlineSessionResumeState.from_json(state_json)

    resumed = auth.online_session(state=state_json)

    assert isinstance(resumed, OnlineSessionClient)
    assert resumed.resume_state() == restored_state

    # The handle of an invoice sent before the "restart" comes back on the resumed session.
    status_of_sent = resumed.submission(workflow_context["invoice_ref"]).wait(
        timeout=90.0
    )
    assert status_of_sent.ksef_number

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
            _ = session.send_invoice(example_invoice_xml(seller_nip=seller_nip))
            state = session.resume_state()

        # The session is closed here, so wait() returns its terminal status.
        status = session.wait(timeout=90.0)
        assert status.upo is not None
        assert status.upo.pages

        upo_pages = session.download_upo()

        assert len(upo_pages) == len(status.upo.pages)
        assert all(isinstance(page, bytes) and page for page in upo_pages)

        # A resumed session client waits without having closed the session itself.
        resumed = auth.online_session(state=state.to_json())
        assert resumed.wait(timeout=90.0).status.code == 200
        upo_xml = resumed.download_upo()[0]

        # Leaving a with block on an already-closed resumed session is a no-op.
        with auth.online_session(state=state):
            pass

        assert isinstance(upo_xml, bytes)
        assert len(upo_xml) > 0
