"""End-to-end tests that execute the example scripts against Environment.TEST.

Each test imports and calls the main() function of a self-contained example.
Batch examples build their own FA(3) invoices and only need the TEST seller NIP;
the single-invoice examples still take a caller-provided FA(3) XML fixture.

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
from ksef2._core.exceptions import KSeFExportTimeoutError
from tests.integration.conftest import KSeFCredentials

EXPORT_TIMEOUT_SKIP_MARKER = "KSEF2_EXPORT_TIMEOUT"


@pytest.fixture
def example_seller(
    monkeypatch: pytest.MonkeyPatch,
    ksef_credentials: KSeFCredentials,
) -> None:
    """Point the invoice examples at the TEST subject.

    Every invoice example builds its own FA(3) invoice through
    ``example_invoice_xml``, so the seller NIP is all the environment they need.
    """
    monkeypatch.setenv(
        "KSEF2_EXAMPLE_SELLER_NIP",
        os.environ.get("KSEF2_EXAMPLE_SELLER_NIP", ksef_credentials.subject_nip),
    )


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
def test_example_quickstart(ksef_credentials: KSeFCredentials) -> None:
    """Quickstart: authenticate and send an invoice (context manager + manual).

    Covers: XAdES auth → open session via context manager → send invoice →
    open session manually → send invoice → terminate.

    The example hardcodes a TEST seller NIP so it runs with no setup; the test
    passes the credentials subject instead, which is what ``ExampleConfig`` is
    for.
    """
    quickstart_example.run(
        quickstart_example.ExampleConfig(seller_nip=ksef_credentials.subject_nip)
    )


@pytest.mark.integration
def test_example_send_invoice(example_seller: None) -> None:
    """Send a single invoice and immediately download it by KSeF number.

    Covers: testdata setup → XAdES auth → open session → send invoice →
    download invoice XML → cleanup.
    """
    send_invoice_example.main()


@pytest.mark.integration
def test_example_send_query_export_download(
    example_seller: None, capsys: pytest.CaptureFixture[str]
) -> None:
    """Full invoice lifecycle: send, query status, schedule export, download.

    Covers: testdata setup → XAdES auth → open session → send invoice →
    wait for status → export → wait for the package → save → cleanup.

    KSeF TEST builds export packages on its own schedule, so a scheduled export
    can legitimately stay unready. This is the one skip the release gate
    tolerates, and it tolerates it by marker, not by test name: the reason
    carries EXPORT_TIMEOUT_SKIP_MARKER and
    scripts/verify_integration_results.py accepts only that. Any other skip
    reason, and any skip in the other six required workflows, still fails the
    gate.
    """
    try:
        send_example.main()
    except KSeFExportTimeoutError as exc:
        captured = capsys.readouterr()
        assert "Export scheduled:" in captured.out
        pytest.skip(
            f"{EXPORT_TIMEOUT_SKIP_MARKER} KSeF TEST export package "
            f"{exc.reference_number} was not ready after {exc.timeout}s"
        )


@pytest.mark.integration
def test_example_send_batch(
    example_seller: None, capsys: pytest.CaptureFixture[str]
) -> None:
    """Prepare, upload, and process a two-invoice batch session end to end.

    Covers: prepare batch → open session → upload parts → close → wait →
    list invoices → download collective UPO.

    Each invoice carries its own number; reusing one number makes KSeF
    reject the later part with 440 Duplikat faktury while the session itself
    still reports success.
    """
    send_batch_example.main()

    captured = capsys.readouterr()
    assert "total=2, ok=2, failed=0" in captured.out
    assert captured.out.count("status=200") == 2


@pytest.mark.integration
def test_example_submit_batch(
    example_seller: None, capsys: pytest.CaptureFixture[str]
) -> None:
    """Submit a two-invoice batch in one high-level call.

    Covers: submit → wait → list invoices → download collective UPO.

    Covers the same duplicate-number rule as the manual batch example: two invoices
    with one number come back as ok=1, failed=1.
    """
    submit_batch_example.main()

    captured = capsys.readouterr()
    assert "total=2, ok=2, failed=0" in captured.out
    assert captured.out.count("status=200") == 2


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
