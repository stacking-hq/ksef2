from __future__ import annotations

import pytest

from ksef2.domain.models.limits import ApiRateLimits, ContextLimits, SubjectLimits


@pytest.mark.integration
def test_get_context_limits(xades_authenticated_context):
    """Fetch effective context limits."""
    client, auth = xades_authenticated_context

    result = auth.limits.get_context_limits()

    assert isinstance(result, ContextLimits)
    assert result.online_session.max_invoices > 0
    assert result.batch_session.max_invoices > 0


@pytest.mark.integration
def test_get_subject_limits(xades_authenticated_context):
    """Fetch effective subject limits."""
    client, auth = xades_authenticated_context

    result = auth.limits.get_subject_limits()

    assert isinstance(result, SubjectLimits)


@pytest.mark.integration
def test_get_api_rate_limits(xades_authenticated_context):
    """Fetch effective API rate limits."""
    client, auth = xades_authenticated_context

    result = auth.limits.get_api_rate_limits()

    assert isinstance(result, ApiRateLimits)
    assert result.online_session.per_second > 0
    assert result.invoice_send.per_hour > 0


@pytest.mark.integration
def test_set_session_limits_roundtrip(xades_authenticated_context):
    """Fetch session limits, modify, post back, then reset."""
    client, auth = xades_authenticated_context

    limits = auth.limits.get_context_limits()
    original_max = limits.online_session.max_invoices

    limits.online_session.max_invoices = original_max + 1
    auth.limits.set_session_limits(limits=limits)

    updated = auth.limits.get_context_limits()
    assert updated.online_session.max_invoices == original_max + 1

    auth.limits.reset_session_limits()


@pytest.mark.integration
def test_set_api_rate_limits_accepts_override_payload(xades_authenticated_context):
    """Submit API rate limits without assuming the TEST environment persists them."""
    client, auth = xades_authenticated_context

    limits = auth.limits.get_api_rate_limits()
    original_per_second = limits.invoice_send.per_second

    limits.invoice_send.per_second = (
        original_per_second - 50
    )  # has to be between 1 and 100
    try:
        auth.limits.set_api_rate_limits(limits=limits)
    finally:
        auth.limits.reset_api_rate_limits()


@pytest.mark.integration
def test_reset_session_limits(xades_authenticated_context):
    """Reset session limits back to defaults."""
    client, auth = xades_authenticated_context

    auth.limits.reset_session_limits()


@pytest.mark.integration
def test_reset_api_rate_limits(xades_authenticated_context):
    """Reset API rate limits back to defaults."""
    client, auth = xades_authenticated_context

    auth.limits.reset_api_rate_limits()


@pytest.mark.integration
def test_set_subject_limits_roundtrip(xades_authenticated_context):
    """Fetch subject limits, modify, post back, then reset."""
    client, auth = xades_authenticated_context

    limits = auth.limits.get_subject_limits()

    if limits.certificate is None:
        pytest.skip("Subject certificate limits not available")

    original_max = limits.certificate.max_certificates
    limits.certificate.max_certificates = (original_max or 10) + 1
    auth.limits.set_subject_limits(limits=limits)

    updated = auth.limits.get_subject_limits()
    assert updated.certificate is not None
    assert updated.certificate.max_certificates == (original_max or 10) + 1

    auth.limits.reset_subject_limits()


@pytest.mark.integration
def test_reset_subject_limits(xades_authenticated_context):
    """Reset subject limits back to defaults."""
    client, auth = xades_authenticated_context

    auth.limits.reset_subject_limits()
