import pytest

from ksef2 import Client
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.core.exceptions import KSeFAuthError


@pytest.mark.integration
def test_full_auth_flow(authenticated_context):
    """Full token authentication flow against real KSeF TEST API.

    Flow: Challenge → Encrypt Token → Init Auth → Poll Status → Redeem Tokens

    Verifies:
        - Access token is returned
        - Refresh token is returned
        - Tokens are different (not the same JWT)
    """
    client, auth = authenticated_context

    assert isinstance(auth, AuthenticatedClient)
    assert auth.access_token is not None
    assert auth.refresh_token is not None
    assert auth.access_token != auth.refresh_token
    assert auth.auth_tokens.access_token.valid_until is not None
    assert auth.auth_tokens.refresh_token.valid_until is not None


@pytest.mark.integration
def test_invalid_ksef_token_fails(real_client: Client, ksef_credentials):
    """Verify proper error when using invalid KSeF token."""
    with pytest.raises(KSeFAuthError):
        real_client.authentication.with_token(
            ksef_token="invalid-token-that-does-not-exist",
            nip=ksef_credentials.subject_nip,
        )
