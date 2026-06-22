from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Generator

import pytest

# WeasyPrint (used by InvoicePDFExporter) needs native glib/pango libraries.
# On macOS with Homebrew these live under /opt/homebrew/lib and the dynamic
# linker only finds them when DYLD_FALLBACK_LIBRARY_PATH includes that path.
# Interactive shells typically pick this up from .zshrc, but pytest and CI
# runners often don'request source the user profile, so we set it explicitly.
if sys.platform == "darwin":
    _brew_lib = "/opt/homebrew/lib"
    _cur = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    if _brew_lib not in _cur:
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            f"{_brew_lib}:{_cur}" if _cur else _brew_lib
        )

from ksef2 import Client
from ksef2.clients.testdata import TemporalTestData
from ksef2.config import Environment
from ksef2.xades import generate_test_certificate
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.logging import get_logger


from dotenv import load_dotenv

_ = load_dotenv(".env.test")

logger = get_logger(__name__)


@dataclass(frozen=True)
class KSeFCredentials:
    subject_nip: str
    person_nip: str
    person_pesel: str


@pytest.fixture(scope="session")
def ksef_credentials() -> KSeFCredentials:
    """Load KSeF TEST credentials from environment variables.

    Required env vars:
        KSEF_TEST_SUBJECT_NIP - NIP for test subject
        KSEF_TEST_PERSON_NIP  - NIP for test person
        KSEF_TEST_PERSON_PESEL - PESEL for test person
    """
    subject_nip = os.environ.get("KSEF_TEST_SUBJECT_NIP")
    person_nip = os.environ.get("KSEF_TEST_PERSON_NIP")
    person_pesel = os.environ.get("KSEF_TEST_PERSON_PESEL")

    missing = []
    if not subject_nip:
        missing.append("KSEF_TEST_SUBJECT_NIP")
    if not person_nip:
        missing.append("KSEF_TEST_PERSON_NIP")
    if not person_pesel:
        missing.append("KSEF_TEST_PERSON_PESEL")

    if missing:
        pytest.skip(f"Missing required env vars: {', '.join(missing)}")

    assert subject_nip and person_nip and person_pesel

    return KSeFCredentials(
        subject_nip=subject_nip,
        person_nip=person_nip,
        person_pesel=person_pesel,
    )


@pytest.fixture(scope="session")
def real_client() -> Client:
    """Create a client pointing to the KSeF TEST environment."""
    return Client(environment=Environment.TEST)


@pytest.fixture
def test_context(real_client: Client, ksef_credentials: KSeFCredentials):
    """Create a test context with TemporalTestData for setup/teardown.

    This fixture provides a TemporalTestData context manager that automatically
    cleans up created subjects, persons, and permissions when the test completes.
    """
    return real_client.testdata.temporal()


@pytest.fixture
def xades_authenticated_context(
    real_client: Client,
    ksef_credentials: KSeFCredentials,
    test_context: TemporalTestData,
) -> Generator[tuple[Client, AuthenticatedClient], None, None]:
    """Create an authenticated context using XAdES with self-signed certificate.

    This is the entry point for tests that don'request have a KSeF token yet.
    Uses self-signed certificate for authentication (allowed on TEST env only).

    Sets up:
        1. Test subject (VAT_GROUP) - or uses existing
        2. Generates self-signed certificate for the subject
        3. Authenticates using XAdES with that certificate
        4. Yields (client, tokens)

    Note: Token generation may not work with self-signed certs - it requires
    the authenticated entity to have CredentialsManage permission which needs
    to be granted via the testdata API.

    Cleanup (automatic via TemporalTestData):
        1. Delete subject
    """
    cert, private_key = generate_test_certificate(ksef_credentials.subject_nip)

    tokens = real_client.authentication.with_xades(
        nip=ksef_credentials.subject_nip,
        cert=cert,
        private_key=private_key,
    )

    yield real_client, tokens


@pytest.fixture
def authenticated_context(
    real_client: Client,
    ksef_credentials: KSeFCredentials,
    test_context: TemporalTestData,
) -> Generator[tuple[Client, AuthenticatedClient], None, None]:
    """Create an authenticated context using XAdES authentication.

    Note: We use XAdES instead of KSeF token authentication because:
    1. Token authentication requires encrypting the token with RSA-OAEP
    2. The KSeF token must fit within ~190 bytes (2048-bit key limit)
    3. Pre-generated tokens from env are typically JWTs that are too long

    Sets up:
        1. Test subject (VAT_GROUP) - or uses existing
        2. Authenticates using XAdES with self-signed certificate
        3. Yields (client, tokens)

    Cleanup (automatic via TemporalTestData):
        1. Delete subject
    """
    cert, private_key = generate_test_certificate(ksef_credentials.subject_nip)

    tokens = real_client.authentication.with_xades(
        nip=ksef_credentials.subject_nip,
        cert=cert,
        private_key=private_key,
    )

    yield real_client, tokens
