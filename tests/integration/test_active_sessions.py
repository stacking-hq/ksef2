import pytest

from ksef2 import Client
from ksef2._clients.authenticated import AuthenticatedClient


@pytest.mark.integration
def test_list_active_sessions(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
):
    """List active authentication sessions."""
    client, auth = xades_authenticated_context

    sessions = auth.sessions.list().first_page()

    assert isinstance(sessions, list)


@pytest.mark.integration
def test_list_active_sessions_with_pagination(xades_authenticated_context):
    """List active sessions with pagination."""
    client, auth = xades_authenticated_context

    sessions = auth.sessions.list(page_size=15).first_page()  # 10 to 100

    assert len(sessions) <= 15


@pytest.mark.integration
def test_terminate_current_session(xades_authenticated_context):
    """Terminate the current authentication session."""
    client, auth = xades_authenticated_context

    auth.sessions.terminate_current()


@pytest.mark.integration
def test_terminate_specific_session(xades_authenticated_context):
    """Terminate a specific authentication session by reference number."""
    client, auth = xades_authenticated_context

    sessions = auth.sessions.list().first_page()

    if sessions:
        ref_to_delete = sessions[0].reference_number

        auth.sessions.terminate(ref_to_delete)
