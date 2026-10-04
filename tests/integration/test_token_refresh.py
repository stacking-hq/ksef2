from datetime import datetime, timedelta, timezone
import pytest

from ksef2._domain.models.auth import AuthenticationResumeState, RefreshedToken


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


@pytest.mark.integration
def test_resumed_client_with_expired_access_token_still_works(authenticated_context):
    """A client resumed from a state whose access token expired refreshes itself."""
    client, auth = authenticated_context
    expired_state = AuthenticationResumeState.model_validate_json(
        auth.resume_state().to_json()
    ).model_copy(
        update={
            "access_token_valid_until": datetime.now(timezone.utc)
            - timedelta(minutes=1)
        }
    )

    resumed = client.authentication.resume(expired_state)
    limits = resumed.limits.get_context_limits()

    assert limits is not None
    assert resumed.access_token != auth.access_token
    assert resumed.auth_tokens.access_token.valid_until > datetime.now(timezone.utc)
    assert resumed.resume_state().access_token_valid_until > datetime.now(timezone.utc)
