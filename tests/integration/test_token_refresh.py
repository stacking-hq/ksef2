from datetime import datetime, timezone
import pytest

from ksef2.domain.models.auth import RefreshedToken


@pytest.mark.integration
def test_refresh_token(authenticated_context):
    """Exchange refresh token for new access token."""
    client, auth = authenticated_context

    refreshed = client.authentication.refresh(refresh_token=auth.refresh_token)

    assert isinstance(refreshed, RefreshedToken)
    assert refreshed.access_token is not None
    assert refreshed.access_token.valid_until is not None

    now = datetime.now(timezone.utc)
    assert refreshed.access_token.valid_until > now


@pytest.mark.integration
def test_refreshed_token_works(authenticated_context):
    """Verify the refreshed token can be used for API calls."""
    client, auth = authenticated_context

    refreshed = client.authentication.refresh(refresh_token=auth.refresh_token)

    assert refreshed.access_token.token is not None
