"""Transport failures reach public callers as SDK errors, after the retries ran out."""

import asyncio
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2 import KSeFException, KSeFTransportError
from ksef2._clients.async_authenticated import AsyncAuthenticatedClient
from ksef2._clients.async_online import AsyncOnlineSessionClient
from ksef2._clients.async_base import AsyncClient
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._clients.base import Client
from ksef2._clients.online import OnlineSessionClient
from ksef2._config import Environment, RetryConfig, TransportConfig
from ksef2._core import exceptions
from ksef2._core.exceptions import (
    KSeFApiError,
    KSeFAuthError,
    KSeFRateLimitError,
    KSeFValidationError,
)
from ksef2._core.middlewares.async_exceptions import AsyncKSeFExceptionMiddleware
from ksef2._core.middlewares.exceptions import KSeFExceptionMiddleware
from ksef2._core.routes import LimitRoutes, PeppolRoutes, SessionRoutes
from ksef2._domain.models.auth import AuthenticationResumeState, AuthTokens
from ksef2._domain.models.session import OnlineSessionResumeState
from ksef2._infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport, FakeTransport
from tests.unit.flavors import Flavor

_PublicClient = Client | AsyncClient | AuthenticatedClient | AsyncAuthenticatedClient
_Operation = Callable[[_PublicClient], object]
_Handler = Callable[[httpx.Request], httpx.Response]

# Three attempts, so the retry middleware is really exercised, and no waiting.
_RETRY = RetryConfig(max_attempts=3, initial_delay=0.0)
# httpx's own default, kept explicit so the redirect test can lower it.
_HTTPX_MAX_REDIRECTS = 20

_REVOKED_SERIAL_NUMBER = "ABCDEF0123456789"


@dataclass
class _Outcome:
    """Result of one public call driven through a scripted HTTP transport."""

    requests: list[httpx.Request]
    result: object | None
    error: Exception | None


def _rate_limits(client: _PublicClient) -> object:
    """Call a public GET the retry middleware treats as retryable."""
    assert isinstance(client, AuthenticatedClient | AsyncAuthenticatedClient)
    return client.limits.get_api_rate_limits()


def _first_peppol_page(client: _PublicClient) -> object:
    """Call a public GET through the pager boundary and return its first page."""
    assert isinstance(client, Client | AsyncClient)
    return client.peppol.list().first_page()


def _revoke_certificate(client: _PublicClient) -> object:
    """Call a public mutation whose POST the SDK never retries."""
    assert isinstance(client, AuthenticatedClient | AsyncAuthenticatedClient)
    return client.certificates.revoke(certificate_serial_number=_REVOKED_SERIAL_NUMBER)


def _drive(
    flavor: Flavor,
    tokens: AuthTokens,
    operation: _Operation,
    handler: _Handler,
    *,
    retry: RetryConfig = _RETRY,
    authenticated: bool = True,
    follow_redirects: bool = False,
    max_redirects: int = _HTTPX_MAX_REDIRECTS,
) -> _Outcome:
    """Run ``operation`` on the flavour's public client over a scripted HTTP transport.

    Only the real middleware chain sits between the operation and the transport, so
    the outcome shows exactly what a caller sees: retries first, then the error the
    SDK raises.
    """
    requests: list[httpx.Request] = []

    def _record(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    http_client: httpx.Client | httpx.AsyncClient
    if flavor.is_async:
        http_client = httpx.AsyncClient(
            base_url=Environment.TEST.base_url,
            transport=httpx.MockTransport(_record),
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
        )
    else:
        http_client = httpx.Client(
            base_url=Environment.TEST.base_url,
            transport=httpx.MockTransport(_record),
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
        )

    client = flavor.root_client(
        environment=Environment.TEST,
        http_client=http_client,
        transport_config=TransportConfig(retry=retry, auto_refresh_tokens=False),
    )
    outcome = _Outcome(requests=requests, result=None, error=None)
    try:
        target: _PublicClient = client
        if authenticated:
            target = client.authentication.resume(
                AuthenticationResumeState.from_tokens(tokens)
            )
        outcome.result = flavor.run(operation(target))
    except Exception as exc:
        outcome.error = exc
    finally:
        flavor.close(client)
        if isinstance(http_client, httpx.AsyncClient):
            _ = asyncio.run(http_client.aclose())
        else:
            http_client.close()
    return outcome


_TRANSPORT_FAILURES: list[type[httpx.TransportError]] = [
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteError,
    httpx.RemoteProtocolError,
]


@pytest.mark.parametrize("failure", _TRANSPORT_FAILURES, ids=lambda cls: cls.__name__)
def test_transport_failure_surfaces_as_sdk_error(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
    failure: type[httpx.TransportError],
) -> None:
    """Every transport failure class becomes the exported SDK error, never an httpx one."""

    def _fail(request: httpx.Request) -> httpx.Response:
        raise failure(f"{failure.__name__} while reaching KSeF", request=request)

    outcome = _drive(flavor, domain_auth_tokens.build(), _rate_limits, _fail)

    error = outcome.error
    assert isinstance(error, KSeFTransportError)
    assert type(error) is KSeFTransportError
    assert isinstance(error, KSeFException)
    assert not isinstance(error, httpx.HTTPError)
    assert error.code == "TRANSPORT_ERROR"
    assert error.context["code"] == "TRANSPORT_ERROR"
    assert isinstance(error.__cause__, failure)
    assert error.method == "GET"
    assert error.path == LimitRoutes.GET_API_RATE_LIMITS.path
    assert error.outcome_ambiguous is False
    assert len(outcome.requests) == _RETRY.max_attempts
    assert failure.__name__ in str(error)


def test_malformed_encoded_response_surfaces_as_sdk_error(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    """A response the HTTP client cannot decode is an SDK error and is not retried."""

    def _bad_gzip(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Encoding": "gzip"},
            content=b"not-gzip",
            request=request,
        )

    outcome = _drive(
        flavor,
        domain_auth_tokens.build(),
        _first_peppol_page,
        _bad_gzip,
        authenticated=False,
    )

    error = outcome.error
    assert isinstance(error, KSeFTransportError)
    assert type(error) is KSeFTransportError
    assert error.code == "TRANSPORT_ERROR"
    assert isinstance(error.__cause__, httpx.DecodingError)
    assert not isinstance(error, httpx.HTTPError)
    assert error.method == "GET"
    assert error.path == PeppolRoutes.QUERY_PROVIDERS.path
    assert error.outcome_ambiguous is False
    assert len(outcome.requests) == 1


def test_redirect_chain_exhaustion_surfaces_as_sdk_error(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    """A redirect chain the HTTP client gives up on is an SDK error, without retries."""

    def _redirect(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"Location": PeppolRoutes.QUERY_PROVIDERS.path},
            request=request,
        )

    outcome = _drive(
        flavor,
        domain_auth_tokens.build(),
        _first_peppol_page,
        _redirect,
        authenticated=False,
        follow_redirects=True,
        max_redirects=1,
    )

    error = outcome.error
    assert isinstance(error, KSeFTransportError)
    assert error.code == "TRANSPORT_ERROR"
    assert isinstance(error.__cause__, httpx.TooManyRedirects)
    assert error.method == "GET"
    assert error.path == PeppolRoutes.QUERY_PROVIDERS.path
    assert error.outcome_ambiguous is False
    assert not isinstance(error, httpx.HTTPError)
    assert len(outcome.requests) == 2


def test_retry_exhaustion_wraps_after_last_attempt(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    """The wrapper waits for the retries and reports the failure that ended them."""
    failures: list[httpx.TransportError] = [
        httpx.ConnectError("first attempt"),
        httpx.ConnectError("second attempt"),
        httpx.ReadTimeout("last attempt"),
    ]
    attempts = 0

    def _fail(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise failures[min(attempts - 1, len(failures) - 1)]

    outcome = _drive(flavor, domain_auth_tokens.build(), _rate_limits, _fail)

    assert len(outcome.requests) == 3
    error = outcome.error
    assert isinstance(error, KSeFTransportError)
    assert error.__cause__ is failures[2]


def test_retry_then_success_returns_result(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
    peppol_providers_resp: BaseFactory[spec.QueryPeppolProvidersResponse],
) -> None:
    """A transport failure the retries recover from is never reported to the caller."""
    payload = peppol_providers_resp.build().model_dump(mode="json")
    attempts = 0

    def _fail_then_succeed(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("first attempt", request=request)
        assert request.url.path.endswith(PeppolRoutes.QUERY_PROVIDERS.path)
        return httpx.Response(200, json=payload, request=request)

    outcome = _drive(
        flavor,
        domain_auth_tokens.build(),
        _first_peppol_page,
        _fail_then_succeed,
        authenticated=False,
    )

    assert outcome.error is None
    assert len(outcome.requests) == 2
    providers = outcome.result
    assert isinstance(providers, list)
    assert [provider.id for provider in providers] == ["PPL123456"]


def test_nonretryable_post_is_not_retried(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    """A mutation the SDK does not retry is sent once and marked ambiguous."""

    def _fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadError("request may have reached KSeF", request=request)

    outcome = _drive(flavor, domain_auth_tokens.build(), _revoke_certificate, _fail)

    assert len(outcome.requests) == 1
    assert outcome.requests[0].method == "POST"
    error = outcome.error
    assert isinstance(error, KSeFTransportError)
    assert error.method == "POST"
    assert error.path == f"/certificates/{_REVOKED_SERIAL_NUMBER}/revoke"
    assert error.outcome_ambiguous is True


@pytest.mark.parametrize(
    ("method", "ambiguous"),
    [
        ("GET", False),
        ("HEAD", False),
        ("OPTIONS", False),
        ("POST", True),
        ("PUT", True),
        ("DELETE", True),
    ],
)
def test_transport_context_is_sanitized(
    flavor: Flavor,
    method: str,
    ambiguous: bool,
) -> None:
    """Method and pathname survive; credentials, tokens and cause text do not."""
    if flavor.is_async:
        async_transport = AsyncFakeTransport()
        async_transport.enqueue_error(
            httpx.ConnectError("part?signature=raw-cause-secret")
        )
        middleware: AsyncKSeFExceptionMiddleware | KSeFExceptionMiddleware = (
            AsyncKSeFExceptionMiddleware(async_transport)
        )
    else:
        sync_transport = FakeTransport()
        sync_transport.enqueue_error(
            httpx.ConnectError("part?signature=raw-cause-secret")
        )
        middleware = KSeFExceptionMiddleware(sync_transport)

    with pytest.raises(KSeFTransportError) as exc_info:
        _ = flavor.run(
            middleware.request(
                method,
                "https://api-user:bearer-in-url@ksef.example.pl/invoices/query"
                "?continuationToken=query-secret#fragment",
                headers={"Authorization": "Bearer header-secret"},
                content=b"body-secret",
            )
        )

    error = exc_info.value
    assert error.method == method
    assert error.path == "/invoices/query"
    assert error.outcome_ambiguous is ambiguous
    assert isinstance(error.__cause__, httpx.ConnectError)
    assert "ConnectError" in str(error)
    assert "part" in str(error)
    secrets = (
        "query-secret",
        "bearer-in-url",
        "api-user",
        "header-secret",
        "body-secret",
        "raw-cause-secret",
        "fragment",
        "ksef.example.pl",
    )
    for payload in (str(error), repr(error), json.dumps(error.context, default=str)):
        assert not [secret for secret in secrets if secret in payload], payload


@pytest.mark.parametrize(
    ("status_code", "expected", "expected_attempts"),
    [
        (401, KSeFAuthError, 1),
        (429, KSeFRateLimitError, 3),
        (500, KSeFApiError, 1),
        (503, KSeFApiError, 3),
    ],
)
def test_api_status_error_is_not_transport_error(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
    status_code: int,
    expected: type[KSeFApiError],
    expected_attempts: int,
) -> None:
    """Answers that came back from KSeF keep their API class and their retries."""

    def _answer(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=b"", request=request)

    outcome = _drive(flavor, domain_auth_tokens.build(), _rate_limits, _answer)

    error = outcome.error
    assert isinstance(error, expected)
    assert not isinstance(error, KSeFTransportError)
    assert len(outcome.requests) == expected_attempts


def test_sdk_error_is_not_rewrapped(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    """A response the SDK cannot parse stays the SDK error it already was."""

    def _wrong_shape(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "payload"}, request=request)

    outcome = _drive(flavor, domain_auth_tokens.build(), _rate_limits, _wrong_shape)

    error = outcome.error
    assert isinstance(error, KSeFValidationError)
    assert not isinstance(error, KSeFTransportError)
    assert len(outcome.requests) == 1


def _close_failing_session(
    flavor: Flavor, state: OnlineSessionResumeState
) -> OnlineSessionClient | AsyncOnlineSessionClient:
    """Build an online session whose requests run through the SDK exception chain."""
    if flavor.is_async:
        assert isinstance(flavor.transport, AsyncFakeTransport)
        return AsyncOnlineSessionClient(
            AsyncKSeFExceptionMiddleware(flavor.transport), state
        )
    assert isinstance(flavor.transport, FakeTransport)
    return OnlineSessionClient(KSeFExceptionMiddleware(flavor.transport), state)


def _exit_session(
    flavor: Flavor,
    session: OnlineSessionClient | AsyncOnlineSessionClient,
    *,
    body_failed: bool,
) -> None:
    """Leave a ``with`` block holding an online session, optionally with a body error."""
    if flavor.is_async:
        assert isinstance(session, AsyncOnlineSessionClient)

        async def _run_async() -> None:
            async with session:
                if body_failed:
                    raise RuntimeError("invoice submission failed")

        _ = flavor.run(_run_async())
        return

    assert isinstance(session, OnlineSessionClient)
    with session:
        if body_failed:
            raise RuntimeError("invoice submission failed")


def test_session_close_transport_failure_preserves_body_exception(
    flavor: Flavor,
    domain_online_session_state: BaseFactory[OnlineSessionResumeState],
) -> None:
    """A close that fails at the transport never hides what the body was doing."""
    state = domain_online_session_state.build()
    flavor.transport.enqueue_error(httpx.ReadError("close response lost"))

    with pytest.raises(RuntimeError, match="invoice submission failed"):
        _exit_session(flavor, _close_failing_session(flavor, state), body_failed=True)

    assert len(flavor.transport.calls) == 1
    assert flavor.transport.calls[0].path == SessionRoutes.TERMINATE_ONLINE.format(
        referenceNumber=state.reference_number
    )


def test_session_close_transport_failure_propagates_without_body_exception(
    flavor: Flavor,
    domain_online_session_state: BaseFactory[OnlineSessionResumeState],
) -> None:
    """A close that fails at the transport is reported as the SDK transport error."""
    state = domain_online_session_state.build()
    flavor.transport.enqueue_error(httpx.ReadError("close response lost"))

    with pytest.raises(KSeFTransportError) as exc_info:
        _exit_session(flavor, _close_failing_session(flavor, state), body_failed=False)

    assert isinstance(exc_info.value.__cause__, httpx.ReadError)
    assert exc_info.value.outcome_ambiguous is True


def test_public_canonical_and_legacy_exceptions_are_the_same_class() -> None:
    """The new error is exported once and the legacy import resolves to that class."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
import warnings
import ksef2
assert 'ksef2.core' not in sys.modules, 'modern import activated the legacy package'
with warnings.catch_warnings():
    warnings.simplefilter('ignore', DeprecationWarning)
    from ksef2.core.exceptions import KSeFTransportError as LegacyError
from ksef2._core.exceptions import KSeFTransportError as CanonicalError
assert LegacyError is CanonicalError is ksef2.KSeFTransportError
error = ksef2.KSeFTransportError('boom', method='GET', path='/x?q=1')
assert error.code == 'TRANSPORT_ERROR'
""",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_transport_context_preserves_code_and_hint() -> None:
    """Extra context cannot rewrite the class code, and an explicit hint is honoured."""
    error = KSeFTransportError(
        "The request failed",
        code="OVERRIDDEN",
        hint="Try later",
        reference_number="ref-1",
    )

    assert error.code == "TRANSPORT_ERROR"
    assert error.context["code"] == "TRANSPORT_ERROR"
    assert error.hint == "Try later"
    assert error.context["hint"] == "Try later"
    assert error.context["reference_number"] == "ref-1"
    assert str(error) == "The request failed\nHint: Try later"

    subclass = exceptions.KSeFExternalTransferError(
        operation="download",
        host="storage.example",
        reference_number="ref-1",
        part_ordinal=1,
    )

    assert subclass.code == "EXTERNAL_TRANSFER_ERROR"
    assert subclass.context["code"] == "EXTERNAL_TRANSFER_ERROR"
    assert subclass.hint is None
    assert "hint" not in subclass.context


def test_transport_error_codes_are_stable_and_distinct() -> None:
    """Each transport failure keeps its own code while sharing one base class."""
    transport_classes = [
        KSeFTransportError,
        exceptions.KSeFExternalTransferError,
        exceptions.KSeFBatchUploadError,
        exceptions.KSeFAuthTokenRedemptionError,
    ]

    codes = [cls.code for cls in transport_classes]

    assert codes == [
        "TRANSPORT_ERROR",
        "EXTERNAL_TRANSFER_ERROR",
        "BATCH_UPLOAD_ERROR",
        "AUTH_TOKEN_REDEMPTION_ERROR",
    ]
    assert len(set(codes)) == len(codes)
    for cls in transport_classes:
        assert issubclass(cls, KSeFTransportError)
        assert issubclass(cls, KSeFException)
