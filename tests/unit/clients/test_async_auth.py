import asyncio
from unittest.mock import MagicMock, patch

import pytest
from cryptography.x509 import Certificate
from polyfactory import BaseFactory

from ksef2.clients.async_auth import AsyncAuthClient
from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.config import Environment
from ksef2.core.exceptions import (
    KSeFAuthError,
    KSeFUnsupportedEnvironmentError,
    NoCertificateAvailableError,
)
from ksef2.core.routes import AuthRoutes
from ksef2.core.stores import CertificateStore
from ksef2.core.xades import generate_test_certificate
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models.encryption import PublicKeyCertificate
from ksef2.infra.schema.api.supp.auth import InitTokenAuthenticationRequest
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport
from tests.unit.helpers import VALID_BASE64


def _build_auth_client(
    async_fake_transport: AsyncFakeTransport,
    certificate_store: CertificateStore | None = None,
    environment: Environment = Environment.PRODUCTION,
) -> AsyncAuthClient:
    return AsyncAuthClient(
        async_fake_transport,
        certificate_store or CertificateStore(),
        environment=environment,
    )


def _token_store(certificate: PublicKeyCertificate) -> CertificateStore:
    store = CertificateStore()
    store.load([certificate])
    return store


class TestAsyncAuthClient:
    @patch("ksef2.clients.async_auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token(
        self,
        _mock_encrypt_token: MagicMock,
        async_fake_transport: AsyncFakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
        auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse],
    ) -> None:
        client = _build_auth_client(
            async_fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        challenge = auth_challenge_resp.build(timestampMs=1735689600000)
        init_response = auth_init_resp.build()
        status_response = auth_status_resp.build(
            status=spec.StatusInfo(code=200, description="Authenticated")
        )
        tokens_response = auth_tokens_resp.build()
        async_fake_transport.enqueue(challenge.model_dump(mode="json"))
        async_fake_transport.enqueue(init_response.model_dump(mode="json"))
        async_fake_transport.enqueue(status_response.model_dump(mode="json"))
        async_fake_transport.enqueue(tokens_response.model_dump(mode="json"))

        result = asyncio.run(
            client.with_token(ksef_token="ksef-token", nip="1234567890")
        )

        assert isinstance(result, AsyncAuthenticatedClient)
        assert len(async_fake_transport.calls) == 4
        challenge_call, token_call, status_call, redeem_call = (
            async_fake_transport.calls
        )
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

    @patch("ksef2.clients.async_auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token_raises_without_ksef_token_encryption_certificate(
        self,
        _mock_encrypt_token: MagicMock,
        async_fake_transport: AsyncFakeTransport,
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
    ) -> None:
        client = _build_auth_client(async_fake_transport)
        async_fake_transport.enqueue(json_body=[])
        async_fake_transport.enqueue(
            auth_challenge_resp.build().model_dump(mode="json")
        )

        with pytest.raises(
            NoCertificateAvailableError,
            match="No valid certificate for KsefTokenEncryption found",
        ):
            asyncio.run(client.with_token(ksef_token="ksef-token", nip="1234567890"))

    @patch("ksef2.clients.async_auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token_raises_when_authentication_fails(
        self,
        _mock_encrypt_token: MagicMock,
        async_fake_transport: AsyncFakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
    ) -> None:
        client = _build_auth_client(
            async_fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        init_response = auth_init_resp.build()
        failed_status = auth_status_resp.build(
            status=spec.StatusInfo(code=450, description="Authentication failed")
        )
        async_fake_transport.enqueue(
            auth_challenge_resp.build().model_dump(mode="json")
        )
        async_fake_transport.enqueue(init_response.model_dump(mode="json"))
        async_fake_transport.enqueue(failed_status.model_dump(mode="json"))

        with pytest.raises(KSeFAuthError, match="Authentication failed"):
            asyncio.run(client.with_token(ksef_token="ksef-token", nip="1234567890"))

    @patch("ksef2.clients.async_auth.encrypt_token", return_value=VALID_BASE64)
    def test_with_token_raises_on_timeout(
        self,
        _mock_encrypt_token: MagicMock,
        async_fake_transport: AsyncFakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
    ) -> None:
        client = _build_auth_client(
            async_fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        init_response = auth_init_resp.build()
        pending_status = auth_status_resp.build(
            status=spec.StatusInfo(code=100, description="Pending")
        )
        async_fake_transport.enqueue(
            auth_challenge_resp.build().model_dump(mode="json")
        )
        async_fake_transport.enqueue(init_response.model_dump(mode="json"))
        async_fake_transport.enqueue(pending_status.model_dump(mode="json"))
        async_fake_transport.enqueue(pending_status.model_dump(mode="json"))

        with pytest.raises(KSeFAuthError, match="timed out"):
            asyncio.run(
                client.with_token(
                    ksef_token="ksef-token",
                    nip="1234567890",
                    poll_interval=0.0,
                    max_poll_attempts=2,
                )
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
        async_fake_transport: AsyncFakeTransport,
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        auth_challenge_resp: BaseFactory[spec.AuthenticationChallengeResponse],
        auth_init_resp: BaseFactory[spec.AuthenticationInitResponse],
        auth_status_resp: BaseFactory[spec.AuthenticationOperationStatusResponse],
        auth_tokens_resp: BaseFactory[spec.AuthenticationTokensResponse],
    ) -> None:
        client = _build_auth_client(
            async_fake_transport,
            _token_store(domain_public_key_cert.build(usage=["ksef_token_encryption"])),
        )
        challenge = auth_challenge_resp.build()
        init_response = auth_init_resp.build()
        status_response = auth_status_resp.build(
            status=spec.StatusInfo(code=200, description="Authenticated")
        )
        tokens_response = auth_tokens_resp.build()
        async_fake_transport.enqueue(challenge.model_dump(mode="json"))
        async_fake_transport.enqueue(init_response.model_dump(mode="json"))
        async_fake_transport.enqueue(status_response.model_dump(mode="json"))
        async_fake_transport.enqueue(tokens_response.model_dump(mode="json"))
        cert, private_key = generate_test_certificate("1234567890")

        result = asyncio.run(
            client.with_xades(
                nip="1234567890",
                cert=cert,
                private_key=private_key,
                verify_chain=True,
            )
        )

        assert isinstance(result, AsyncAuthenticatedClient)
        assert async_fake_transport.calls[1].path == AuthRoutes.XADES_SIGNATURE

    def test_with_test_certificate_rejects_non_test_environment(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        client = _build_auth_client(
            async_fake_transport,
            environment=Environment.PRODUCTION,
        )

        with pytest.raises(KSeFUnsupportedEnvironmentError):
            asyncio.run(client.with_test_certificate(nip="1234567890"))

    @patch.object(
        AsyncAuthClient,
        "with_xades",
        autospec=True,
    )
    def test_with_test_certificate_uses_generated_certificate(
        self,
        mock_with_xades: MagicMock,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
    ) -> None:
        client = _build_auth_client(async_fake_transport, environment=Environment.TEST)
        mock_with_xades.return_value = AsyncAuthenticatedClient(
            transport=async_fake_transport,
            auth_tokens=domain_auth_tokens.build(),
            certificate_store=CertificateStore(),
        )

        result = asyncio.run(
            client.with_test_certificate(
                nip="1234567890",
                verify_chain=True,
                poll_interval=2.0,
                max_poll_attempts=5,
            )
        )

        assert result is mock_with_xades.return_value
        _, kwargs = mock_with_xades.call_args
        assert kwargs["nip"] == "1234567890"
        assert isinstance(kwargs["cert"], Certificate)
        assert kwargs["private_key"] is not None
        assert kwargs["verify_chain"] is True
        assert kwargs["poll_interval"] == 2.0
        assert kwargs["max_poll_attempts"] == 5
