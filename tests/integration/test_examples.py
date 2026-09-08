"""End-to-end tests that execute the example scripts against Environment.TEST.

Each test imports and calls the main() function of a self-contained example.
Invoice-submission examples use a fresh FA(3) invoice for the TEST seller.

Skipped examples (require external config not available in CI):
  - auth/auth_xades_demo.py    — needs MCU certificate files
"""

import os
from pathlib import Path

import pytest

import scripts.examples.auth.auth_refresh as auth_refresh_example
import scripts.examples.auth.auth_xades as auth_xades_example
import scripts.examples.auth.token_management as token_management_example
import scripts.examples.invoices.send_batch as send_batch_example
import scripts.examples.invoices.send_invoice as send_invoice_example
import scripts.examples.invoices.send_query_export_download as send_example
import scripts.examples.invoices.submit_batch as submit_batch_example
import scripts.examples.limits.limits_modify as limits_modify_example
import scripts.examples.limits.limits_query as limits_query_example
import scripts.examples.permissions.grant_permissions as grant_permissions_example
import scripts.examples.permissions.query_permissions as query_permissions_example
import scripts.examples.quickstart as quickstart_example
import scripts.examples.session.session_management as session_management_example
import scripts.examples.session.session_resume as session_resume_example
import scripts.examples.testdata.attachments as attachments_example
import scripts.examples.testdata.block_context as block_context_example
import scripts.examples.testdata.setup_test_data as setup_test_data_example
from ksef2 import Client
from tests.integration.conftest import KSeFCredentials
from tests.integration.invoice_payload import load_test_invoice_xml


@pytest.fixture
def example_invoice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ksef_credentials: KSeFCredentials,
) -> None:
    seller_nip = os.environ.get(
        "KSEF2_EXAMPLE_SELLER_NIP", ksef_credentials.subject_nip
    )
    if not os.environ.get("KSEF2_EXAMPLE_INVOICE_XML"):
        invoice_path = tmp_path / "invoice.xml"
        invoice_path.write_bytes(load_test_invoice_xml(seller_nip=seller_nip))
        monkeypatch.setenv("KSEF2_EXAMPLE_INVOICE_XML", str(invoice_path))
    monkeypatch.setenv("KSEF2_EXAMPLE_SELLER_NIP", seller_nip)


# ── auth ──────────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_example_auth_xades() -> None:
    """XAdES authentication with a self-signed certificate.

    Covers: challenge → sign → submit → poll → redeem tokens.
    """
    auth_xades_example.main()


@pytest.mark.integration
def test_example_auth_refresh() -> None:
    """Token refresh after initial XAdES authentication.

    Covers: XAdES auth → list sessions → refresh access token.
    """
    auth_refresh_example.main()


@pytest.mark.integration
def test_example_token_management() -> None:
    """KSeF token lifecycle: generate, check status, revoke.

    Covers: testdata setup → XAdES auth → generate token →
    check status → revoke → verify revocation → cleanup.
    """
    token_management_example.main()


# ── session ───────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_example_session_management() -> None:
    """Authentication session listing and termination.

    Covers: XAdES auth → list active sessions → terminate current session.
    """
    session_management_example.main()


@pytest.mark.integration
def test_example_session_resume() -> None:
    """Session state serialization and resume from saved state.

    Covers: testdata setup → open session (manual) → serialize state →
    restore state → resume session → terminate.
    """
    session_resume_example.main()


# ── invoices ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.usefixtures("example_invoice")
def test_example_quickstart() -> None:
    """Quickstart: authenticate and send an invoice with a managed session.

    Covers: XAdES auth → open session via context manager → send invoice →
    close the session.
    """
    quickstart_example.main()


@pytest.mark.integration
@pytest.mark.usefixtures("example_invoice")
def test_example_send_invoice() -> None:
    """Send a single invoice and immediately download it by KSeF number.

    Covers: testdata setup → XAdES auth → open session → send invoice →
    download invoice XML → cleanup.
    """
    send_invoice_example.main()


@pytest.mark.integration
@pytest.mark.usefixtures("example_invoice")
def test_example_send_query_export_download() -> None:
    """Full invoice lifecycle: send, query status, schedule export, download.

    Covers: testdata setup → XAdES auth → open session → send invoice →
    poll status → schedule export → fetch package → cleanup.
    """
    send_example.main()


@pytest.mark.integration
@pytest.mark.usefixtures("example_invoice")
def test_example_send_batch(capsys: pytest.CaptureFixture[str]) -> None:
    """Prepare, upload, and process a batch session end to end."""
    send_batch_example.main()
    assert "(total=1, ok=1, failed=0)" in capsys.readouterr().out


@pytest.mark.integration
@pytest.mark.usefixtures("example_invoice")
def test_example_submit_batch(capsys: pytest.CaptureFixture[str]) -> None:
    """Prepare and submit a batch in one high-level call."""
    submit_batch_example.main()
    assert "(total=1, ok=1, failed=0)" in capsys.readouterr().out


@pytest.mark.integration
def test_example_batch_export_to_pdf(tmp_path: Path) -> None:
    """Batch-export all sample FA3 invoices to PDF and HTML.

    Covers: iterate sample XML invoices → XSLT render to HTML → render to PDF.
    """
    import scripts.examples.invoices.batch_export_to_pdf as batch_pdf_example

    batch_pdf_example.run(
        batch_pdf_example.ExampleConfig(
            source_dir=(Path(__file__).parents[2] / "schemas" / "FA3" / "samples"),
            output_dir=tmp_path,
        )
    )


# ── limits ────────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_example_limits_query() -> None:
    """Query all API limit types from an authenticated client.

    Covers: testdata setup → XAdES auth → get context limits →
    get subject limits → get API rate limits → cleanup.
    """
    limits_query_example.main()


@pytest.mark.integration
def test_example_limits_modify() -> None:
    """Modify and reset API limits (TEST environment only).

    Covers: testdata setup → XAdES auth → modify session/subject/rate limits →
    reset each to defaults → set production rate limits → cleanup.
    """
    limits_modify_example.main()


# ── permissions ───────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_example_grant_permissions() -> None:
    """Grant permissions to a person and an entity.

    Covers: testdata setup → XAdES auth → grant person permissions →
    grant entity permissions → cleanup.
    """
    grant_permissions_example.main()


@pytest.mark.integration
def test_example_query_permissions() -> None:
    """Query all permission types after granting them.

    Covers: testdata setup → XAdES auth → grant permissions → query persons /
    authorizations / personal / EU entities / subordinate entities /
    subunits → cleanup.
    """
    query_permissions_example.main()


# ── testdata ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_example_testdata_setup_automatic(real_client: Client) -> None:
    """Testdata setup with automatic cleanup via temporal() context manager."""
    setup_test_data_example.with_automatic_cleanup(real_client)


@pytest.mark.integration
def test_example_testdata_setup_manual(real_client: Client) -> None:
    """Testdata setup with manual create/revoke/delete lifecycle."""
    setup_test_data_example.manual_cleanup(real_client)


@pytest.mark.integration
def test_example_block_context() -> None:
    """Block and unblock an authentication context.

    Covers: create subject → block context → unblock context → cleanup.
    """
    block_context_example.main()


@pytest.mark.integration
def test_example_attachments() -> None:
    """Enable and revoke invoice attachment permissions.

    Covers: create subject → enable attachments → revoke immediately →
    re-enable → revoke with future end date → cleanup.
    """
    attachments_example.main()
