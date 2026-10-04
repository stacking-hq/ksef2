"""KSeF TEST returns Problem Details because the SDK asks for it.

The SDK sends ``X-Error-Format: problem-details`` on every KSeF API request. These
tests record the real ``Content-Type`` of KSeF's error responses and check that the
SDK reads ``ksef_code`` and ``trace_id`` from them.

Run with:
    uv run pytest tests/integration/test_error_format.py -v -m integration
"""

from collections.abc import Generator
from dataclasses import dataclass, field

import httpx
import pytest

from ksef2 import Client, Environment, FormSchema
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._core.exceptions import KSeFApiError, KSeFInvoiceRejectedError
from ksef2._core.exceptions import KSeFNotReadyError
from ksef2._infra.schema.api import spec
from ksef2.xades import generate_test_certificate
from scripts.examples._common import example_invoice_xml
from tests.integration.conftest import KSeFCredentials
from tests.integration.invoice_payload import invoice_seller_nip

PROBLEM_JSON = "application/problem+json"


@dataclass
class _Seen:
    """Error responses KSeF sent, as ``(status, media type)``."""

    errors: list[tuple[int, str]] = field(default_factory=list)

    def record(self, response: httpx.Response) -> None:
        if response.is_error:
            content_type = response.headers.get("content-type", "")
            self.errors.append(
                (response.status_code, content_type.split(";", 1)[0].strip().lower())
            )


@pytest.fixture
def recording_auth(
    ksef_credentials: KSeFCredentials,
) -> Generator[tuple[AuthenticatedClient, _Seen, str], None, None]:
    seen = _Seen()
    http_client = httpx.Client(
        base_url=Environment.TEST.base_url,
        event_hooks={"response": [seen.record]},
    )
    seller_nip = invoice_seller_nip(ksef_credentials.subject_nip)
    with Client(environment=Environment.TEST, http_client=http_client) as client:
        cert, private_key = generate_test_certificate(seller_nip)
        auth = client.authentication.with_xades(
            nip=seller_nip, cert=cert, private_key=private_key
        )
        seen.errors.clear()
        yield auth, seen, seller_nip
    http_client.close()


@pytest.mark.integration
def test_a_400_comes_back_as_problem_details(
    recording_auth: tuple[AuthenticatedClient, _Seen, str],
) -> None:
    """A validation error is ``application/problem+json`` with a code and a trace ID."""
    auth, seen, _ = recording_auth

    with pytest.raises(KSeFApiError) as exc_info:
        _ = auth.sessions.list(page_size=5000).first_page()  # KSeF allows 10 to 100

    error = exc_info.value
    assert seen.errors == [(400, PROBLEM_JSON)]
    assert isinstance(error.response, spec.BadRequestProblemDetails)
    assert error.response.errors
    assert error.ksef_code == error.response.errors[0].code == 21405
    assert error.trace_id == error.response.traceId
    assert error.trace_id
    assert f"Trace ID: {error.trace_id}" in str(error)


@pytest.mark.integration
def test_upo_not_issued_comes_back_as_problem_details_and_not_ready(
    recording_auth: tuple[AuthenticatedClient, _Seen, str],
) -> None:
    """A duplicate invoice is rejected with 440 and never gets a UPO: KSeF says 21178."""
    auth, seen, seller_nip = recording_auth
    invoice_xml = example_invoice_xml(seller_nip=seller_nip)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        _ = session.send_invoice(invoice_xml).wait(timeout=90.0)
        duplicate = session.send_invoice(invoice_xml)
        with pytest.raises(KSeFInvoiceRejectedError):
            _ = duplicate.wait(timeout=90.0)

        seen.errors.clear()
        with pytest.raises(KSeFNotReadyError) as exc_info:
            _ = duplicate.download_upo()

    error = exc_info.value
    assert seen.errors == [(400, PROBLEM_JSON)]
    assert isinstance(error.response, spec.BadRequestProblemDetails)
    assert error.ksef_code == 21178
    assert error.trace_id
    assert error.hint is not None
    assert "wait()" in error.hint
