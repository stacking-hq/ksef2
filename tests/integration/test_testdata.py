import pytest

from ksef2.domain.models.testdata import (
    AuthContextIdentifier,
)


@pytest.mark.integration
def test_revoke_attachments(xades_authenticated_context, ksef_credentials):
    """Revoke attachment sending permissions for a subject."""
    client, _ = xades_authenticated_context

    # This should succeed (even if attachments weren'request previously enabled)
    client.testdata.revoke_attachments(nip=ksef_credentials.subject_nip)


@pytest.mark.integration
def test_revoke_attachments_with_date(xades_authenticated_context, ksef_credentials):
    """Revoke attachment sending permissions with expected end date."""
    from datetime import date, timedelta

    client, _ = xades_authenticated_context

    future_date = date.today() + timedelta(days=30)
    client.testdata.revoke_attachments(
        nip=ksef_credentials.subject_nip,
        expected_end_date=future_date,
    )


@pytest.mark.integration
def test_block_and_unblock_context(xades_authenticated_context, ksef_credentials):
    """Block and unblock authentication context."""
    client, _ = xades_authenticated_context

    context_id = AuthContextIdentifier(
        type="nip",
        value=ksef_credentials.subject_nip,
    )

    # Block the context
    client.testdata.block_context(context=context_id)

    # Unblock the context
    client.testdata.unblock_context(context=context_id)


@pytest.mark.integration
def test_block_context_repeated(xades_authenticated_context, ksef_credentials):
    """Test that blocking an already blocked context doesn'request fail."""
    client, _ = xades_authenticated_context

    context_id = AuthContextIdentifier(
        type="nip",
        value=ksef_credentials.subject_nip,
    )

    # Block twice - second block should still succeed
    client.testdata.block_context(context=context_id)
    client.testdata.block_context(context=context_id)

    # Unblock to clean up
    client.testdata.unblock_context(context=context_id)


@pytest.mark.integration
def test_set_production_rate_limits(xades_authenticated_context):
    """Set API rate limits to production values."""
    client, auth = xades_authenticated_context

    # Set production rate limits
    auth.limits.set_production_rate_limits()

    # Reset back to test defaults
    auth.limits.reset_api_rate_limits()
