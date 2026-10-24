import datetime
import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from cryptography.x509 import Certificate
from cryptography.x509.oid import NameOID, ObjectIdentifier
from polyfactory import BaseFactory

from ksef2._clients.async_authenticated import AsyncAuthenticatedClient
from ksef2._clients.auth import AuthClient
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._clients.session_management import SessionManagementClient
from ksef2._config import Environment
from ksef2.xades import generate_test_certificate
from ksef2._core.exceptions import (
    KSeFAuthError,
    KSeFAuthPollingTimeoutError,
    KSeFAuthTokenRedemptionError,
    KSeFArgumentError,
    KSeFTransportError,
    KSeFUnsupportedEnvironmentError,
    KSeFProfileConfigError,
    NoCertificateAvailableError,
)
from ksef2._core.routes import AuthRoutes
from ksef2._core.stores import CertificateStore
from ksef2._domain.models import auth as domain_auth
from ksef2._domain.models.encryption import PublicKeyCertificate
from ksef2._infra.schema.api.supp.auth import InitTokenAuthenticationRequest
from ksef2._infra.schema.api import spec
from ksef2.xades import XAdESCredentials, XAdESPrivateKey
from tests.unit.fakes.transport import FakeTransport
from tests.unit.flavors import Flavor
from tests.unit.helpers import VALID_BASE64
from tests.unit.helpers import legacy_api
from tests.unit.xades_material import (
    CredentialFormat,
    build_credentials,
    public_key_der,
)


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
    def test_legacy_auth_constructor_without_environment_still_works(
        self,
        fake_transport: FakeTransport,
    ) -> None:
        with pytest.warns(DeprecationWarning, match="authentication"):
            _ = AuthClient(fake_transport, CertificateStore())

    def test_resume_rehydrates_authenticated_client(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[domain_auth.AuthTokens],
    ) -> None:
        client = _build_auth_client(fake_transport)
        auth_tokens = domain_auth_tokens.build()
        state = domain_auth.AuthenticationResumeState.from_tokens(auth_tokens)

        result = client.resume(state)

        assert isinstance(result, AuthenticatedClient)
        assert result.auth_tokens == auth_tokens

    @patch("ksef2._clients.auth.encrypt_token", return_value=VALID_BASE64)
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
        certificate = domain_public_key_cert.build(usage=["ksef_token_encryption"])
        client = _build_auth_client(fake_transport, _token_store(certificate))
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
        token_request = InitTokenAuthenticationRequest.model_validate(token_call.json)
        assert token_request.challenge == challenge.challenge
        assert token_request.contextIdentifier.type == "Nip"
        assert token_request.contextIdentifier.value == "1234567890"
        assert token_request.encryptedToken == VALID_BASE64
        assert token_request.publicKeyId == certificate.public_key_id
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

    @pytest.mark.parametrize(
        ("failure", "message"),
        [
            (httpx.ReadError, "redemption response lost"),
            (httpx.DecodingError, "redemption body undecodable"),
        ],
        ids=["read", "decoding"],
    )
    @patch("ksef2._clients.auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token_reports_ambiguous_lost_redemption_response(
        self,
        _mock_encrypt_token: MagicMock,
        failure: type[httpx.RequestError],
        message: str,
        fake_transport: FakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
    ) -> None:
        certificate = domain_public_key_cert.build(usage=["ksef_token_encryption"])
        client = _build_auth_client(fake_transport, _token_store(certificate))
        init_response = auth_init_resp.build()
        status_response = auth_status_resp.build(
            status=spec.StatusInfo(code=200, description="Authenticated")
        )
        transport_error = failure(message)
        fake_transport.enqueue(
            auth_challenge_resp.build(timestampMs=1735689600000).model_dump(mode="json")
        )
        fake_transport.enqueue(init_response.model_dump(mode="json"))
        fake_transport.enqueue(status_response.model_dump(mode="json"))
        fake_transport.enqueue_error(transport_error)

        with pytest.raises(
            KSeFAuthTokenRedemptionError,
            match="may have succeeded",
        ) as exc_info:
            _ = client.with_token(ksef_token="ksef-token", nip="1234567890")

        assert exc_info.value.outcome_ambiguous is True
        assert exc_info.value.context["outcome_ambiguous"] is True
        assert exc_info.value.__cause__ is transport_error
        assert len(fake_transport.calls) == 4
        assert fake_transport.calls[-1].path == AuthRoutes.REDEEM_TOKEN

    @patch("ksef2._clients.auth.encrypt_token", return_value=VALID_BASE64)
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

    @patch("ksef2._clients.auth.encrypt_token", return_value=VALID_BASE64)
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

    @patch("ksef2._clients.auth.encrypt_token", return_value=VALID_BASE64)
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

        with pytest.raises(KSeFAuthPollingTimeoutError, match="not ready") as exc_info:
            _ = client.with_token(
                ksef_token="ksef-token",
                nip="1234567890",
                timeout=0.0,
                poll_interval=0.0,
            )

        assert exc_info.value.reference_number == init_response.referenceNumber
        assert exc_info.value.timeout == 0.0
        assert not hasattr(exc_info.value, "attempts")
        assert not hasattr(exc_info.value, "status_code")

    @patch(
        "ksef2.xades.sign_xades",
        return_value=b"<SignedXML />",
    )
    @patch(
        "ksef2.xades.build_auth_token_request_xml",
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
        "ksef2.xades.sign_xades",
        return_value=b"<SignedXML />",
    )
    @patch(
        "ksef2.xades.build_auth_token_request_xml",
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

    @pytest.mark.parametrize("credential_format", ["pem", "der", "pkcs12"])
    @pytest.mark.parametrize("encrypted", [False, True], ids=["plain", "password"])
    @patch("ksef2.xades.sign_xades")
    @patch(
        "ksef2.xades.build_auth_token_request_xml",
        return_value=b"<AuthTokenRequest />",
    )
    def test_with_xades_accepts_data_credentials(
        self,
        _mock_build_xml: MagicMock,
        mock_sign_xades: MagicMock,
        credential_format: CredentialFormat,
        encrypted: bool,
        flavor: Flavor,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
        auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse],
    ) -> None:
        client = flavor.auth_client(
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        challenge = auth_challenge_resp.build()
        init_response = auth_init_resp.build()
        status_response = auth_status_resp.build(
            status=spec.StatusInfo(code=200, description="Authenticated")
        )
        tokens_response = auth_tokens_resp.build()
        for response in (challenge, init_response, status_response, tokens_response):
            flavor.transport.enqueue(response.model_dump(mode="json"))
        cert, private_key = generate_test_certificate("1234567890")
        password = b"data-credentials-password" if encrypted else None
        credentials = build_credentials(
            cert, private_key, credential_format, password=password
        )
        signed_with: list[tuple[Certificate, XAdESPrivateKey]] = []

        def record_and_sign(
            xml_bytes: bytes, signing_cert: Certificate, signing_key: XAdESPrivateKey
        ) -> bytes:
            signed_with.append((signing_cert, signing_key))
            return b"<SignedXML />"

        mock_sign_xades.side_effect = record_and_sign

        with patch(
            "ksef2._domain.models.xades._usable_pair",
            side_effect=AssertionError("credentials were validated again"),
        ):
            result = flavor.run(
                client.with_xades(
                    nip="1234567890",
                    credentials=credentials,
                    verify_chain=True,
                )
            )

        assert isinstance(
            result, AsyncAuthenticatedClient if flavor.is_async else AuthenticatedClient
        )
        assert len(flavor.transport.calls) == 4
        assert len(signed_with) == 1
        used_cert, used_key = signed_with[0]
        assert used_cert is credentials.certificate
        assert used_key is credentials.private_key
        assert used_cert.public_bytes(Encoding.DER) == cert.public_bytes(Encoding.DER)
        assert public_key_der(used_key) == public_key_der(private_key)
        xades_call = flavor.transport.calls[1]
        assert xades_call.path == AuthRoutes.XADES_SIGNATURE
        assert xades_call.content == b"<SignedXML />"
        assert xades_call.params is not None
        assert xades_call.params["verifyCertificateChain"] == "true"

    def test_with_xades_rejects_mixed_or_incomplete_credentials(
        self,
        flavor: Flavor,
    ) -> None:
        client = flavor.auth_client()
        cert, private_key = generate_test_certificate("1234567890")
        credentials = XAdESCredentials.from_pem(
            cert.public_bytes(Encoding.PEM),
            private_key.private_bytes(
                Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
            ),
        )

        # Both forms, one form with a leftover half of the other, and neither form.
        with pytest.raises(KSeFArgumentError):
            _ = flavor.run(
                client.with_xades(
                    nip="1234567890",
                    credentials=credentials,
                    cert=cert,
                    private_key=private_key,
                )
            )
        with pytest.raises(KSeFArgumentError):
            _ = flavor.run(
                client.with_xades(nip="1234567890", credentials=credentials, cert=cert)
            )
        with pytest.raises(KSeFArgumentError):
            _ = flavor.run(
                client.with_xades(
                    nip="1234567890", credentials=credentials, private_key=private_key
                )
            )
        with pytest.raises(KSeFArgumentError):
            _ = flavor.run(client.with_xades(nip="1234567890"))
        with pytest.raises(KSeFArgumentError):
            _ = flavor.run(client.with_xades(nip="1234567890", cert=cert))
        with pytest.raises(KSeFArgumentError):
            _ = flavor.run(client.with_xades(nip="1234567890", private_key=private_key))

        assert flavor.transport.calls == []

    @pytest.mark.parametrize("invalid", ["unreadable", "mismatched"])
    def test_with_xades_rejects_invalid_credentials_before_challenge(
        self, invalid: str, flavor: Flavor
    ) -> None:
        client = flavor.auth_client()
        cert, _ = generate_test_certificate("1234567890")
        _, other_key = generate_test_certificate("1234567890")
        cert_pem = (
            b"junk" if invalid == "unreadable" else cert.public_bytes(Encoding.PEM)
        )
        key_pem = other_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        )
        with pytest.raises(KSeFArgumentError):
            flavor.run(
                client.with_xades(
                    nip="1234567890",
                    credentials=XAdESCredentials.from_pem(cert_pem, key_pem),
                )
            )
        assert flavor.transport.calls == []

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
    @patch("ksef2._clients.auth.generate_test_certificate")
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
            timeout=5.0,
            poll_interval=0.5,
        )

        assert result is expected
        mock_generate_test_certificate.assert_called_once_with("1234567890")
        mock_with_xades.assert_called_once_with(
            nip="1234567890",
            cert="cert",
            private_key="private-key",
            verify_chain=True,
            timeout=5.0,
            poll_interval=0.5,
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

    @patch.object(AuthClient, "with_token")
    def test_with_profile_uses_active_token_profile(
        self,
        mock_with_token: MagicMock,
        fake_transport: FakeTransport,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
            active_profile = "prod-token"

            [profiles.prod-token]
            environment = "production"
            nip = "5261040828"
            poll_interval = 1.5
            max_poll_attempts = 12

            [profiles.prod-token.auth]
            type = "token"
            token_env = "KSEF2_TOKEN"
            context_type = "nip"
            """,
            encoding="utf-8",
        )
        monkeypatch.setenv("KSEF2_TOKEN", "secret-token")
        client = _build_auth_client(fake_transport, environment=Environment.PRODUCTION)
        expected = MagicMock(spec=AuthenticatedClient)
        mock_with_token.return_value = expected

        result = client.with_profile(config_path=config_path)

        assert result is expected
        mock_with_token.assert_called_once_with(
            ksef_token="secret-token",
            nip="5261040828",
            context_type="nip",
            timeout=18.0,
            poll_interval=1.5,
        )

    @patch.object(AuthClient, "with_test_certificate")
    def test_with_profile_uses_named_test_certificate_profile(
        self,
        mock_with_test_certificate: MagicMock,
        fake_transport: FakeTransport,
        tmp_path,
    ) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
            [profiles.test-company]
            environment = "test"
            nip = "5261040828"

            [profiles.test-company.auth]
            type = "test_certificate"
            """,
            encoding="utf-8",
        )
        client = _build_auth_client(fake_transport, environment=Environment.TEST)
        expected = MagicMock(spec=AuthenticatedClient)
        mock_with_test_certificate.return_value = expected

        result = client.with_profile(
            "test-company",
            config_path=config_path,
            timeout=5.0,
            poll_interval=0.5,
            verify_chain=True,
        )

        assert result is expected
        mock_with_test_certificate.assert_called_once_with(
            nip="5261040828",
            verify_chain=True,
            timeout=5.0,
            poll_interval=0.5,
        )

    @patch.object(AuthClient, "with_xades")
    @patch("ksef2._clients.auth.load_profile_pem_credentials")
    def test_with_profile_uses_pem_xades_profile(
        self,
        mock_load_pem_credentials: MagicMock,
        mock_with_xades: MagicMock,
        fake_transport: FakeTransport,
        tmp_path,
    ) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
            [profiles.demo-pem]
            environment = "demo"
            nip = "5261040828"

            [profiles.demo-pem.auth]
            type = "xades_pem"
            cert = "company.pem"
            key = "company.key"
            """,
            encoding="utf-8",
        )
        client = _build_auth_client(fake_transport, environment=Environment.DEMO)
        expected = MagicMock(spec=AuthenticatedClient)
        mock_load_pem_credentials.return_value = ("cert", "private-key")
        mock_with_xades.return_value = expected

        result = client.with_profile(
            "demo-pem",
            config_path=config_path,
            verify_chain=True,
        )

        assert result is expected
        mock_load_pem_credentials.assert_called_once()
        _, loader_kwargs = mock_load_pem_credentials.call_args
        assert loader_kwargs["profile_name"] == "demo-pem"
        mock_with_xades.assert_called_once_with(
            nip="5261040828",
            cert="cert",
            private_key="private-key",
            verify_chain=True,
            timeout=60.0,
            poll_interval=1.0,
        )

    def test_with_profile_rejects_environment_mismatch(
        self,
        fake_transport: FakeTransport,
        tmp_path,
    ) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
            [profiles.prod-token]
            environment = "production"
            nip = "5261040828"

            [profiles.prod-token.auth]
            type = "token"
            token_env = "KSEF2_TOKEN"
            """,
            encoding="utf-8",
        )
        client = _build_auth_client(fake_transport, environment=Environment.TEST)

        with pytest.raises(KSeFProfileConfigError, match="profile 'prod-token' uses"):
            _ = client.with_profile("prod-token", config_path=config_path)

    def test_with_profile_requires_token_environment_variable(
        self,
        fake_transport: FakeTransport,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
            [profiles.prod-token]
            environment = "production"
            nip = "5261040828"

            [profiles.prod-token.auth]
            type = "token"
            token_env = "KSEF2_TOKEN"
            """,
            encoding="utf-8",
        )
        monkeypatch.delenv("KSEF2_TOKEN", raising=False)
        client = _build_auth_client(fake_transport, environment=Environment.PRODUCTION)

        with pytest.raises(KSeFProfileConfigError, match="KSEF2_TOKEN is not set"):
            _ = client.with_profile("prod-token", config_path=config_path)


class TestSessionManagementClient:
    @legacy_api
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

    @legacy_api
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

    def test_terminate(self, fake_transport: FakeTransport) -> None:
        client = SessionManagementClient(fake_transport)
        fake_transport.enqueue()

        client.terminate("ref-123")

        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert call.path == AuthRoutes.TERMINATE_AUTH_SESSION.format(
            referenceNumber="ref-123"
        )

    @legacy_api
    def test_close(self, fake_transport: FakeTransport) -> None:
        client = SessionManagementClient(fake_transport)
        fake_transport.enqueue()

        client.close(reference_number="ref-123")

        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert call.path == AuthRoutes.TERMINATE_AUTH_SESSION.format(
            referenceNumber="ref-123"
        )


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (httpx.ReadError, "redemption response lost"),
        (httpx.DecodingError, "redemption body undecodable"),
    ],
    ids=["read", "decoding"],
)
def test_redemption_transport_error_keeps_the_redemption_contract(
    flavor: Flavor,
    failure: type[httpx.RequestError],
    message: str,
    domain_public_key_cert: BaseFactory[PublicKeyCertificate],
    auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
    auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
    auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
) -> None:
    """The wrapped request failure still ends as the one-shot redemption error."""
    requests: list[httpx.Request] = []
    challenge = auth_challenge_resp.build(timestampMs=1735689600000).model_dump(
        mode="json"
    )
    init = auth_init_resp.build().model_dump(mode="json")
    status = auth_status_resp.build(
        status=spec.StatusInfo(code=200, description="Authenticated")
    ).model_dump(mode="json")

    def _handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith(AuthRoutes.REDEEM_TOKEN.path):
            raise failure(message, request=request)
        if path.endswith(AuthRoutes.CHALLENGE.path):
            return httpx.Response(200, json=challenge, request=request)
        if path.endswith(AuthRoutes.TOKEN_AUTH.path):
            return httpx.Response(200, json=init, request=request)
        if request.method == "GET":
            return httpx.Response(200, json=status, request=request)
        raise AssertionError(f"unexpected request {request.method} {path}")

    store = CertificateStore()
    _ = store.load([domain_public_key_cert.build(usage=["ksef_token_encryption"])])

    http_client = (httpx.AsyncClient if flavor.is_async else httpx.Client)(
        base_url=Environment.PRODUCTION.base_url,
        transport=httpx.MockTransport(_handle),
    )
    client = flavor.root_client(
        environment=Environment.PRODUCTION,
        http_client=http_client,
        certificate_store=store,
    )
    auth_module = "async_auth" if flavor.is_async else "auth"
    try:
        with patch(
            f"ksef2._clients.{auth_module}.encrypt_token", return_value=VALID_BASE64
        ):
            with pytest.raises(KSeFAuthTokenRedemptionError) as exc_info:
                _ = flavor.run(
                    client.authentication.with_token(
                        ksef_token="ksef-token", nip="1234567890"
                    )
                )
    finally:
        flavor.close(client)
        flavor.close(http_client)

    error = exc_info.value
    assert isinstance(error, KSeFTransportError)
    assert isinstance(error.__cause__, failure)
    assert error.outcome_ambiguous is True
    assert error.method == "POST"
    assert error.path == AuthRoutes.REDEEM_TOKEN.path
    redemption_requests = [
        request
        for request in requests
        if request.url.path.endswith(AuthRoutes.REDEEM_TOKEN.path)
    ]
    assert len(redemption_requests) == 1
    assert "ksef-token" not in str(error)
    assert "ksef-token" not in json.dumps(error.context, default=str)
