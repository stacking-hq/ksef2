"""An application written against the pre-1.0 ksef2 layout.

``tests/compat/run_legacy_consumer.py`` imports this module with only the
candidate wheel installed and proves every deprecated path used here still
works and still warns. Nothing here reaches KSeF: the one client that needs
transport gets an ``httpx.MockTransport`` that refuses every request.
"""

from datetime import UTC, datetime
import importlib

import httpx
from pydantic import SecretStr

import ksef2
from ksef2 import Client, Environment, models, xades
from ksef2.clients import AuthenticatedClient, InvoicesClient
from ksef2.core.exceptions import KSeFApiError
from ksef2.core.xades import load_certificate_from_pem
from ksef2.domain.models.invoices import InvoicesFilter
from ksef2.domain.models.session import FormSchema
from ksef2.infra.schema.fa3 import STYLESHEET_PATH
from ksef2.models import (
    AuthTokens,
    BatchSessionState,
    OnlineSessionResumeState,
    OnlineSessionState,
    TokenCredentials,
)
from ksef2.profiles import ProfileConfig
from ksef2.services.invoices import InvoicesFilter as ServiceInvoicesFilter

LEGACY_CLIENT_MODULES = (
    "_async_session",
    "_metadata_pagination",
    "async_auth",
    "async_authenticated",
    "async_base",
    "async_batch",
    "async_certificates",
    "async_collective_identifiers",
    "async_encryption",
    "async_invoice_sessions",
    "async_invoices",
    "async_limits",
    "async_online",
    "async_peppol",
    "async_permissions",
    "async_session_management",
    "async_testdata",
    "async_tokens",
    "auth",
    "authenticated",
    "base",
    "batch",
    "certificates",
    "collective_identifiers",
    "encryption",
    "invoice_sessions",
    "invoices",
    "limits",
    "online",
    "peppol",
    "permissions",
    "profiles",
    "session_management",
    "testdata",
    "tokens",
)

AES_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
INITIALIZATION_VECTOR = "MDEyMzQ1Njc4OWFiY2RlZg=="
VALID_UNTIL = datetime(2099, 1, 1, tzinfo=UTC)


def _refuse(request: httpx.Request) -> httpx.Response:
    """Fail loudly if the deprecated surface tries to reach the network."""
    raise AssertionError(f"legacy code performed a live request to {request.url}")


def _online_state() -> OnlineSessionResumeState:
    return OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(INITIALIZATION_VECTOR),
        valid_until=VALID_UNTIL,
        form_code=FormSchema.FA3,
    )


def _tokens() -> AuthTokens:
    credentials = TokenCredentials(token="legacy-access-token", valid_until=VALID_UNTIL)
    return AuthTokens(access_token=credentials, refresh_token=credentials)


def run() -> None:
    """Use the deprecated API the way an application written for ksef2 0.x does."""
    # The renamed trees hand back the canonical objects, not copies.
    assert KSeFApiError is ksef2.KSeFApiError
    assert InvoicesFilter is ServiceInvoicesFilter is models.InvoicesFilter
    assert load_certificate_from_pem is xades.load_certificate_from_pem
    assert OnlineSessionState is OnlineSessionResumeState
    assert BatchSessionState is models.BatchSessionResumeState
    assert InvoicesClient.__module__ == "ksef2._clients.invoices"
    for name in LEGACY_CLIENT_MODULES:
        legacy_module = importlib.import_module(f"ksef2.clients.{name}")
        canonical_module = importlib.import_module(f"ksef2._clients.{name}")
        assert legacy_module is canonical_module, name

    # Data files stay reachable through the legacy resource path.
    assert STYLESHEET_PATH.is_file()

    state = _online_state()
    assert state.from_state(state.dump_state()) == state
    assert state.model_dump_sensitive(mode="json") == state.to_dict()
    assert state.model_dump_sensitive_json() == state.to_json()

    profile = ProfileConfig.model_validate(
        {
            "environment": "test",
            "nip": "1234567890",
            "auth": {"type": "token", "token_env": "KSEF_LEGACY_TOKEN"},
            "auth_timeout": 180,
        }
    )
    assert profile.max_poll_attempts == 180

    client = Client(
        environment=Environment.TEST,
        http_client=httpx.Client(transport=httpx.MockTransport(_refuse)),
    )
    try:
        authenticated = client.authenticated(_tokens())
        assert isinstance(authenticated, AuthenticatedClient)
        assert authenticated.resume_state().to_tokens() == _tokens()
    finally:
        client.close()
