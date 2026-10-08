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

from ksef2 import Client, Environment, FormSchema, TransportConfig
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._core.exceptions import (
    ExceptionCode,
    KSeFApiError,
    KSeFAuthError,
    KSeFInvoiceRejectedError,
)
from ksef2._core.exceptions import KSeFNotReadyError
from ksef2._infra.schema.api import spec
from ksef2.xades import generate_test_certificate
from scripts.examples._common import example_invoice_xml
from tests.integration.conftest import KSeFCredentials
from tests.integration.invoice_payload import invoice_seller_nip

PROBLEM_JSON = "application/problem+json"
JSON = "application/json"
UNKNOWN_REFERENCE = "20260101-SE-0000000000-0000000000-00"


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


def _recording_auth(
    ksef_credentials: KSeFCredentials, config: TransportConfig
) -> Generator[tuple[AuthenticatedClient, _Seen, str], None, None]:
    seen = _Seen()
    http_client = httpx.Client(
        base_url=Environment.TEST.base_url,
        event_hooks={"response": [seen.record]},
    )
    seller_nip = invoice_seller_nip(ksef_credentials.subject_nip)
    with Client(
        environment=Environment.TEST, transport_config=config, http_client=http_client
    ) as client:
        cert, private_key = generate_test_certificate(seller_nip)
        auth = client.authentication.with_xades(
            nip=seller_nip, cert=cert, private_key=private_key
        )
        seen.errors.clear()
        yield auth, seen, seller_nip
    http_client.close()


@pytest.fixture
def recording_auth(
    ksef_credentials: KSeFCredentials,
) -> Generator[tuple[AuthenticatedClient, _Seen, str], None, None]:
    yield from _recording_auth(ksef_credentials, TransportConfig())


@pytest.fixture
def recording_legacy_auth(
    ksef_credentials: KSeFCredentials,
) -> Generator[tuple[AuthenticatedClient, _Seen, str], None, None]:
    yield from _recording_auth(ksef_credentials, TransportConfig(error_format="legacy"))


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


@pytest.mark.integration
def test_legacy_error_format_comes_back_as_the_older_payload(
    recording_legacy_auth: tuple[AuthenticatedClient, _Seen, str],
) -> None:
    """Without the header KSeF answers ``application/json``: same code, no trace ID."""
    auth, seen, _ = recording_legacy_auth

    with pytest.raises(KSeFApiError) as exc_info:
        _ = auth.sessions.list(page_size=5000).first_page()

    error = exc_info.value
    assert seen.errors == [(400, JSON)]
    assert isinstance(error.response, spec.ExceptionResponse)
    assert error.ksef_code == 21405
    assert error.trace_id is None


@pytest.mark.integration
@pytest.mark.parametrize(
    ("method", "path", "kwargs", "code"),
    [
        (
            "GET",
            "/sessions",
            {
                "params": {"sessionType": "Online", "pageSize": 10},
                "headers": {"x-continuation-token": "not-a-token"},
            },
            ExceptionCode.INVALID_CONTINUATION_TOKEN,
        ),
        ("GET", f"/sessions/{UNKNOWN_REFERENCE}", {}, ExceptionCode.SESSION_NOT_FOUND),
        (
            "GET",
            "/invoices/ksef/5265877635-20250101-0100A0000000-00",
            {},
            ExceptionCode.INVOICE_NOT_FOUND,
        ),
        (
            "POST",
            "/certificates/0000000000000000/revoke",
            {"json": {"revocationReason": "Unspecified"}},
            ExceptionCode.CERTIFICATE_NOT_FOUND,
        ),
    ],
    ids=lambda v: str(v) if isinstance(v, ExceptionCode) else None,
)
def test_documented_codes_map_to_exception_code(
    recording_auth: tuple[AuthenticatedClient, _Seen, str],
    method: str,
    path: str,
    kwargs: dict[str, object],
    code: ExceptionCode,
) -> None:
    """Codes KSeF TEST can be made to return arrive as their ``ExceptionCode``."""
    auth, seen, _ = recording_auth
    transport = auth._authed_transport  # pyright: ignore[reportPrivateUsage]

    with pytest.raises(KSeFApiError) as exc_info:
        _ = transport.request(method, path, **kwargs)  # pyright: ignore[reportArgumentType]

    error = exc_info.value
    assert seen.errors == [(400, PROBLEM_JSON)]
    assert error.ksef_code == code.value
    assert error.exception_code is code
    assert error.trace_id


@pytest.mark.integration
def test_a_missing_token_401_is_read_as_problem_details() -> None:
    """KSeF labels its 401 Problem Details ``application/json``; the SDK still reads it."""
    seen = _Seen()
    http_client = httpx.Client(
        base_url=Environment.TEST.base_url, event_hooks={"response": [seen.record]}
    )
    with Client(environment=Environment.TEST, http_client=http_client) as client:
        with pytest.raises(KSeFAuthError) as exc_info:
            _ = client._transport.get(  # pyright: ignore[reportPrivateUsage]
                "/sessions", params={"sessionType": "Online", "pageSize": 10}
            )
    http_client.close()

    error = exc_info.value
    assert seen.errors == [(401, JSON)]
    assert isinstance(error.response, spec.UnauthorizedProblemDetails)
    assert error.trace_id
    assert error.hint is not None
