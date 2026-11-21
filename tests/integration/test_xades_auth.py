import pytest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat

from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._core.tools import generate_nip
from ksef2._domain.models.tokens import GenerateTokenResponse
from ksef2.xades import XAdESCredentials, generate_test_certificate


@pytest.mark.integration
def test_xades_auth_with_data_credentials(real_client, ksef_credentials, test_context):
    """Authenticate on TEST with credentials supplied as PEM data (TEST env only).

    This is the data-based form of the same self-signed XAdES login the fixture
    above performs with loaded objects, so it proves ``credentials=`` works against
    the real environment. Generated key material never leaves this process, and no
    token value is printed.
    """
    cert, private_key = generate_test_certificate(ksef_credentials.subject_nip)
    credentials = XAdESCredentials.from_pem(
        cert.public_bytes(Encoding.PEM),
        private_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, serialization.NoEncryption()
        ),
    )

    auth = real_client.authentication.with_xades(
        nip=ksef_credentials.subject_nip,
        credentials=credentials,
    )

    assert isinstance(auth, AuthenticatedClient)
    assert auth.access_token is not None
    assert auth.refresh_token is not None
    assert auth.access_token != auth.refresh_token


@pytest.mark.integration
def test_xades_auth_with_self_signed_cert(xades_authenticated_context):
    """Authenticate using XAdES with self-signed certificate (TEST env only).

    This test verifies that:
    - Self-signed certificates work for authentication on TEST environment
    - Access and refresh tokens are returned
    - Tokens have valid expiration times
    """
    client, auth = xades_authenticated_context

    assert isinstance(auth, AuthenticatedClient)
    assert auth.access_token is not None
    assert auth.refresh_token is not None
    assert auth.access_token != auth.refresh_token
    assert auth.auth_tokens.access_token.valid_until is not None
    assert auth.auth_tokens.refresh_token.valid_until is not None

    print("\n\n=== KSEF TOKEN (add to .env.test as KSEF_TEST_KSEF_TOKEN) ===")
    print(auth.access_token[:50] + "...")  # Just show a hint
    print("=========================================================\n")


@pytest.mark.integration
def test_generate_ksef_token(real_client):
    """Generate a KSeF token after XAdES login in a fresh TEST context."""
    nip = generate_nip()
    with real_client.testdata.temporal() as temp:
        temp.create_subject(
            nip=nip,
            subject_type="enforcement_authority",
            description="XAdES token generation test",
        )
        cert, private_key = generate_test_certificate(nip)
        auth = real_client.authentication.with_xades(
            nip=nip,
            cert=cert,
            private_key=private_key,
        )
        generated = auth.tokens.generate(
            permissions=["invoice_write", "invoice_read"],
            description="Integration test KSeF token",
        )
        try:
            _ = generated.wait()
            assert isinstance(generated.response, GenerateTokenResponse)
            assert generated.token
            assert generated.reference_number
        finally:
            auth.tokens.revoke(reference_number=generated.reference_number)
