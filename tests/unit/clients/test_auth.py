import datetime
from unittest.mock import MagicMock, patch

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID, ObjectIdentifier
from polyfactory import BaseFactory

from ksef2.clients.auth import AuthClient
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.clients.session_management import SessionManagementClient
from ksef2.config import Environment
from ksef2.core.xades import generate_test_certificate
from ksef2.core.exceptions import (
    KSeFAuthError,
    KSeFUnsupportedEnvironmentError,
    NoCertificateAvailableError,
)
from ksef2.core.routes import AuthRoutes
from ksef2.core.stores import CertificateStore
from ksef2.domain.models import auth as domain_auth
from ksef2.domain.models.encryption import PublicKeyCertificate
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport
from tests.unit.helpers import VALID_BASE64


def _generate_ec_test_certificate(
    nip: str,
) -> tuple[x509.Certificate, ec.EllipticCurvePrivateKey]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "KSeF SDK Test"),
            x509.NameAttribute(ObjectIdentifier("2.5.4.97"), f"VATPL-{nip}"),
            x509.NameAttribute(NameOID.COMMON_NAME, "KSeF SDK Test"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
        ]
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(hours=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )
    return cert, private_key


def _build_auth_client(
    fake_transport: FakeTransport,
    certificate_store: CertificateStore | None = None,
    environment: Environment = Environment.PRODUCTION,
) -> AuthClient:
    return AuthClient(
        fake_transport,
        certificate_store or CertificateStore(),
        environment=environment,
    )


def _token_store(certificate: PublicKeyCertificate) -> CertificateStore:
    store = CertificateStore()
    store.load([certificate])
    return store


class TestAuthClient:
    @patch("ksef2.clients.auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token(
        self,
        _mock_encrypt_token: MagicMock,
        fake_transport: FakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
        auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse],
    ) -> None:
        client = _build_auth_client(
            fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        challenge = auth_challenge_resp.build(timestampMs=1735689600000)
        init_response = auth_init_resp.build()
        status_response = auth_status_resp.build(
            status=spec.StatusInfo(code=200, description="Authenticated")
        )
        tokens_response = auth_tokens_resp.build()
        fake_transport.enqueue(challenge.model_dump(mode="json"))
        fake_transport.enqueue(init_response.model_dump(mode="json"))
        fake_transport.enqueue(status_response.model_dump(mode="json"))
        fake_transport.enqueue(tokens_response.model_dump(mode="json"))

        result = client.with_token(ksef_token="ksef-token", nip="1234567890")

        assert isinstance(result, AuthenticatedClient)
        assert len(fake_transport.calls) == 4
        challenge_call, token_call, status_call, redeem_call = fake_transport.calls
        assert challenge_call.method == "POST"
        assert challenge_call.path == AuthRoutes.CHALLENGE
        assert token_call.method == "POST"
        assert token_call.path == AuthRoutes.TOKEN_AUTH
        assert token_call.json is not None
        assert token_call.json["challenge"] == challenge.challenge
        assert token_call.json["contextIdentifier"]["type"] == "Nip"
        assert token_call.json["contextIdentifier"]["value"] == "1234567890"
        assert token_call.json["encryptedToken"] == VALID_BASE64
        assert status_call.method == "GET"
        assert status_call.path == AuthRoutes.AUTH_STATUS.format(
            referenceNumber=init_response.referenceNumber
        )
        assert status_call.headers == {
            "Authorization": f"Bearer {init_response.authenticationToken.token}"
        }
        assert redeem_call.method == "POST"
        assert redeem_call.path == AuthRoutes.REDEEM_TOKEN
        assert redeem_call.headers == {
            "Authorization": f"Bearer {init_response.authenticationToken.token}"
        }

    @patch("ksef2.clients.auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token_raises_without_ksef_token_encryption_certificate(
        self,
        _mock_encrypt_token: MagicMock,
        fake_transport: FakeTransport,
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
    ) -> None:
        client = _build_auth_client(fake_transport)
        fake_transport.enqueue(json_body=[])
        fake_transport.enqueue(auth_challenge_resp.build().model_dump(mode="json"))

        with pytest.raises(
            NoCertificateAvailableError,
            match="No valid certificate for KsefTokenEncryption found",
        ):
            _ = client.with_token(ksef_token="ksef-token", nip="1234567890")

    @patch("ksef2.clients.auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token_raises_when_authentication_fails(
        self,
        _mock_encrypt_token: MagicMock,
        fake_transport: FakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
    ) -> None:
        client = _build_auth_client(
            fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        init_response = auth_init_resp.build()
        failed_status = auth_status_resp.build(
            status=spec.StatusInfo(code=450, description="Authentication failed")
        )
        fake_transport.enqueue(auth_challenge_resp.build().model_dump(mode="json"))
        fake_transport.enqueue(init_response.model_dump(mode="json"))
        fake_transport.enqueue(failed_status.model_dump(mode="json"))

        with pytest.raises(KSeFAuthError, match="Authentication failed"):
            _ = client.with_token(ksef_token="ksef-token", nip="1234567890")

    @patch("ksef2.clients.auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token_raises_on_timeout(
        self,
        _mock_encrypt_token: MagicMock,
        fake_transport: FakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
    ) -> None:
        client = _build_auth_client(
            fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        init_response = auth_init_resp.build()
        pending_status = auth_status_resp.build(
            status=spec.StatusInfo(code=100, description="Pending")
        )
        fake_transport.enqueue(auth_challenge_resp.build().model_dump(mode="json"))
        fake_transport.enqueue(init_response.model_dump(mode="json"))
        fake_transport.enqueue(pending_status.model_dump(mode="json"))
        fake_transport.enqueue(pending_status.model_dump(mode="json"))

        with pytest.raises(KSeFAuthError, match="timed out"):
            _ = client.with_token(
                ksef_token="ksef-token",
                nip="1234567890",
                poll_interval=0.0,
                max_poll_attempts=2,
            )

    @patch(
        "ksef2.core.xades.sign_xades",
        return_value=b"<SignedXML />",
    )
    @patch(
        "ksef2.core.xades.build_auth_token_request_xml",
        return_value=b"<AuthTokenRequest />",
    )
    def test_with_xades(
        self,
        _mock_build_xml: MagicMock,
        _mock_sign_xades: MagicMock,
        fake_transport: FakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
        auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse],
    ) -> None:
        client = _build_auth_client(
            fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        challenge = auth_challenge_resp.build()
        init_response = auth_init_resp.build()
        status_response = auth_status_resp.build(
            status=spec.StatusInfo(code=200, description="Authenticated")
        )
        tokens_response = auth_tokens_resp.build()
        fake_transport.enqueue(challenge.model_dump(mode="json"))
        fake_transport.enqueue(init_response.model_dump(mode="json"))
        fake_transport.enqueue(status_response.model_dump(mode="json"))
        fake_transport.enqueue(tokens_response.model_dump(mode="json"))
        cert, private_key = generate_test_certificate("1234567890")

        result = client.with_xades(
            nip="1234567890",
            cert=cert,
            private_key=private_key,
            verify_chain=True,
        )

        assert isinstance(result, AuthenticatedClient)
        assert len(fake_transport.calls) == 4
        xades_call = fake_transport.calls[1]
        assert xades_call.method == "POST"
        assert xades_call.path == AuthRoutes.XADES_SIGNATURE
        assert xades_call.content == b"<SignedXML />"
        assert xades_call.params is not None
        assert xades_call.params["verifyCertificateChain"] == "true"

    @patch(
        "ksef2.core.xades.sign_xades",
        return_value=b"<SignedXML />",
    )
    @patch(
        "ksef2.core.xades.build_auth_token_request_xml",
        return_value=b"<AuthTokenRequest />",
    )
    def test_with_xades_accepts_ec_private_key(
        self,
        _mock_build_xml: MagicMock,
        _mock_sign_xades: MagicMock,
        fake_transport: FakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
        auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse],
    ) -> None:
        client = _build_auth_client(
            fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        challenge = auth_challenge_resp.build()
        init_response = auth_init_resp.build()
        status_response = auth_status_resp.build(
            status=spec.StatusInfo(code=200, description="Authenticated")
        )
        tokens_response = auth_tokens_resp.build()
        fake_transport.enqueue(challenge.model_dump(mode="json"))
        fake_transport.enqueue(init_response.model_dump(mode="json"))
        fake_transport.enqueue(status_response.model_dump(mode="json"))
        fake_transport.enqueue(tokens_response.model_dump(mode="json"))
        cert, private_key = _generate_ec_test_certificate("1234567890")

        result = client.with_xades(
            nip="1234567890",
            cert=cert,
            private_key=private_key,
            verify_chain=False,
        )

        assert isinstance(result, AuthenticatedClient)
        assert len(fake_transport.calls) == 4

    def test_refresh(
        self,
        auth_client: AuthClient,
        fake_transport: FakeTransport,
        auth_refresh_resp: BaseFactory[spec.AuthenticationTokenRefreshResponse],
    ) -> None:
        response = auth_refresh_resp.build()
        fake_transport.enqueue(response.model_dump(mode="json"))

        result = auth_client.refresh(refresh_token="refresh-token")

        assert isinstance(result, domain_auth.RefreshedToken)
        assert result.access_token.token == response.accessToken.token
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == AuthRoutes.REFRESH_TOKEN
        assert call.headers == {"Authorization": "Bearer refresh-token"}

    @patch.object(AuthClient, "with_xades")
    @patch("ksef2.clients.auth.generate_test_certificate")
    def test_with_test_certificate(
        self,
        mock_generate_test_certificate: MagicMock,
        mock_with_xades: MagicMock,
        fake_transport: FakeTransport,
    ) -> None:
        client = _build_auth_client(fake_transport, environment=Environment.TEST)
        mock_generate_test_certificate.return_value = ("cert", "private-key")
        expected = MagicMock(spec=AuthenticatedClient)
        mock_with_xades.return_value = expected

        result = client.with_test_certificate(
            nip="1234567890",
            verify_chain=True,
            poll_interval=0.5,
            max_poll_attempts=5,
        )

        assert result is expected
        mock_generate_test_certificate.assert_called_once_with("1234567890")
        mock_with_xades.assert_called_once_with(
            nip="1234567890",
            cert="cert",
            private_key="private-key",
            verify_chain=True,
            poll_interval=0.5,
            max_poll_attempts=5,
        )

    def test_with_test_certificate_raises_outside_test_environment(
        self,
        fake_transport: FakeTransport,
    ) -> None:
        client = _build_auth_client(fake_transport, environment=Environment.DEMO)

        with pytest.raises(
            KSeFUnsupportedEnvironmentError,
            match="with_test_certificate\\(\\) is only available for Environment.TEST",
        ):
            _ = client.with_test_certificate(nip="1234567890")


class TestSessionManagementClient:
    def test_query_authentication_page(
        self,
        fake_transport: FakeTransport,
        auth_list_resp: BaseFactory[spec.AuthenticationListResponse],
    ) -> None:
        client = SessionManagementClient(fake_transport)
        response = auth_list_resp.build(continuationToken="next-page")
        fake_transport.enqueue(response.model_dump(mode="json"))

        result = client.query(page_size=20)

        assert isinstance(result, domain_auth.AuthenticationSessionsResponse)
        assert result.continuation_token == "next-page"
        assert len(result.items) == len(response.items)
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == AuthRoutes.LIST_SESSIONS
        assert call.params is not None
        assert call.params["pageSize"] == "20"

    def test_all_authentication_iterates_over_pages(
        self,
        fake_transport: FakeTransport,
        auth_list_resp: BaseFactory[spec.AuthenticationListResponse],
    ) -> None:
        client = SessionManagementClient(fake_transport)
        first = auth_list_resp.build(continuationToken="ct-2")
        second = auth_list_resp.build(continuationToken=None)
        fake_transport.enqueue(first.model_dump(mode="json"))
        fake_transport.enqueue(second.model_dump(mode="json"))

        pages = list(client.all())

        assert len(pages) == 2
        assert fake_transport.calls[1].headers == {"x-continuation-token": "ct-2"}

    def test_terminate_current(self, fake_transport: FakeTransport) -> None:
        client = SessionManagementClient(fake_transport)
        fake_transport.enqueue()

        client.terminate_current()

        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert call.path == AuthRoutes.TERMINATE_CURRENT_SESSION

    def test_close(self, fake_transport: FakeTransport) -> None:
        client = SessionManagementClient(fake_transport)
        fake_transport.enqueue()

        client.close(reference_number="ref-123")

        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert call.path == AuthRoutes.TERMINATE_AUTH_SESSION.format(
            referenceNumber="ref-123"
        )
