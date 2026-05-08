from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from polyfactory import BaseFactory

from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.clients.batch import BatchSessionClient
from ksef2.clients.certificates import CertificatesClient
from ksef2.clients.invoice_sessions import InvoiceSessionsClient
from ksef2.clients.limits import LimitsClient
from ksef2.clients.online import OnlineSessionClient
from ksef2.clients.permissions import PermissionsClient
from ksef2.clients.session_management import SessionManagementClient
from ksef2.clients.tokens import TokensClient
from ksef2.core.routes import EncryptionRoutes, SessionRoutes, TokenRoutes
from ksef2.core.stores import CertificateStore
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchPreparedPart,
    BatchSessionState,
    PreparedBatch,
)
from ksef2.domain.models.encryption import PublicKeyCertificate
from ksef2.domain.models.session import FormSchema, OnlineSessionState
from ksef2.infra.schema.api import spec
from ksef2.services.batch import BatchService
from ksef2.services.invoices import InvoicesService
from tests.unit.conftest import _TOKEN
from tests.unit.fakes.transport import FakeTransport
from tests.unit.helpers import VALID_PUBLIC_KEY_ID
from ksef2.core.crypto import sha256_b64


def _build_client(  # [TODO] maybe we could just have client as a fixture, im not sure if rebuilding is necessary for every test
    fake_transport: FakeTransport,
    auth_tokens: AuthTokens,
    certificate_store: CertificateStore | None = None,
) -> AuthenticatedClient:
    return AuthenticatedClient(
        transport=fake_transport,
        auth_tokens=auth_tokens,
        certificate_store=certificate_store or CertificateStore(),
    )


class TestAuthenticatedClientFacade:
    def test_properties_expose_tokens(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
    ) -> None:
        client = _build_client(fake_transport, domain_auth_tokens.build())

        assert client.auth_tokens.access_token.token == _TOKEN
        assert client.access_token == _TOKEN
        assert client.refresh_token == "fake-refresh-token"

    def test_leaf_accessors_return_expected_types(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
    ) -> None:
        client = _build_client(fake_transport, domain_auth_tokens.build())

        assert isinstance(client.tokens, TokensClient)
        assert isinstance(client.certificates, CertificatesClient)
        assert isinstance(client.permissions, PermissionsClient)
        assert isinstance(client.sessions, SessionManagementClient)
        assert isinstance(client.invoice_sessions, InvoiceSessionsClient)
        assert isinstance(client.limits, LimitsClient)
        assert isinstance(client.invoices, InvoicesService)
        assert isinstance(client.batch, BatchService)

    def test_leaf_accessors_are_cached(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
    ) -> None:
        client = _build_client(fake_transport, domain_auth_tokens.build())

        assert client.tokens is client.tokens
        assert client.sessions is client.sessions
        assert client.invoice_sessions is client.invoice_sessions
        assert client.certificates is client.certificates
        assert client.permissions is client.permissions
        assert client.limits is client.limits
        assert client.invoices is client.invoices
        assert client.batch is client.batch

    def test_tokens_accessor_uses_bearer_transport(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        token_list_resp: BaseFactory[spec.QueryTokensResponse],
    ) -> None:
        fake_transport.enqueue(token_list_resp.build().model_dump(mode="json"))
        client = _build_client(fake_transport, domain_auth_tokens.build())

        _ = client.tokens.list_page()

        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == TokenRoutes.LIST_TOKENS
        assert call.headers == {"Authorization": f"Bearer {_TOKEN}"}

    def test_sessions_accessor_uses_bearer_transport(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        auth_list_resp: BaseFactory[spec.AuthenticationListResponse],
    ) -> None:
        fake_transport.enqueue(auth_list_resp.build().model_dump(mode="json"))
        client = _build_client(fake_transport, domain_auth_tokens.build())

        _ = client.sessions.query()

        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == "/auth/sessions"
        assert call.headers == {"Authorization": f"Bearer {_TOKEN}"}


class TestEncryptionAndSessions:
    @patch("ksef2.clients.authenticated.encrypt_symmetric_key", return_value=b"enc-key")
    @patch(
        "ksef2.clients.authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_get_encryption_key_fetches_certificates_when_store_empty(
        self,
        _mock_generate_session_key: MagicMock,
        _mock_encrypt_symmetric_key: MagicMock,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        public_key_cert: BaseFactory[spec.PublicKeyCertificate],
    ) -> None:
        fake_transport.enqueue(
            json_body=[
                public_key_cert.build(
                    usage=[spec.PublicKeyCertificateUsage.SymmetricKeyEncryption],
                    validTo=datetime.now(timezone.utc) + timedelta(days=30),
                ).model_dump(mode="json")
            ]
        )
        client = _build_client(
            fake_transport,
            domain_auth_tokens.build(),
            certificate_store=CertificateStore(),
        )

        aes_key, iv, encrypted_key = client.get_encryption_key()

        assert aes_key == b"k" * 32
        assert iv == b"v" * 16
        assert encrypted_key == b"enc-key"
        assert fake_transport.calls[0].method == "GET"
        assert fake_transport.calls[0].path == EncryptionRoutes.PUBLIC_KEY_CERTIFICATES

    @patch("ksef2.clients.authenticated.encrypt_symmetric_key", return_value=b"enc-key")
    @patch(
        "ksef2.clients.authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_online_session_uses_bearer_transport_and_returns_client(
        self,
        _mock_generate_session_key: MagicMock,
        _mock_encrypt_symmetric_key: MagicMock,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        session_open_online_resp: BaseFactory[spec.OpenOnlineSessionResponse],
    ) -> None:
        fake_transport.enqueue(session_open_online_resp.build().model_dump(mode="json"))
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["symmetric_key_encryption"],
                )
            ]
        )
        client = _build_client(
            fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        session_client = client.online_session(form_code=FormSchema.FA3)

        assert isinstance(session_client, OnlineSessionClient)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == SessionRoutes.OPEN_ONLINE
        assert call.headers == {"Authorization": f"Bearer {_TOKEN}"}
        assert call.json is not None
        assert call.json["encryption"]["publicKeyId"] == store.all()[0].public_key_id
        assert session_client.get_state().access_token == _TOKEN

    @patch("ksef2.clients.authenticated.encrypt_symmetric_key", return_value=b"enc-key")
    @patch(
        "ksef2.clients.authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_batch_session_uses_bearer_transport_and_returns_client(
        self,
        _mock_generate_session_key: MagicMock,
        _mock_encrypt_symmetric_key: MagicMock,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        domain_batch_file_info: BaseFactory[BatchFileInfo],
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
    ) -> None:
        fake_transport.enqueue(session_open_batch_resp.build().model_dump(mode="json"))
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["symmetric_key_encryption"],
                )
            ]
        )
        client = _build_client(
            fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        batch_file = domain_batch_file_info.build()
        batch_client = client.batch_session(batch_file=batch_file)

        assert isinstance(batch_client, BatchSessionClient)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == SessionRoutes.OPEN_BATCH
        assert call.headers == {"Authorization": f"Bearer {_TOKEN}"}
        assert call.json is not None
        assert call.json["encryption"]["publicKeyId"] == store.all()[0].public_key_id
        assert batch_client.access_token == _TOKEN

    def test_open_batch_session_uses_supplied_encryption_material(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_file_info: BaseFactory[BatchFileInfo],
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
    ) -> None:
        fake_transport.enqueue(session_open_batch_resp.build().model_dump(mode="json"))
        client = _build_client(fake_transport, domain_auth_tokens.build())

        batch_client = client.open_batch_session(
            batch_file=domain_batch_file_info.build(),
            aes_key=b"a" * 32,
            iv=b"b" * 16,
            encrypted_key=b"enc-key",
            public_key_id=VALID_PUBLIC_KEY_ID,
        )

        assert isinstance(batch_client, BatchSessionClient)
        assert batch_client.aes_key == b"a" * 32
        assert batch_client.iv == b"b" * 16
        call = fake_transport.calls[0]
        assert call.path == SessionRoutes.OPEN_BATCH
        assert call.json is not None
        assert call.json["encryption"]["publicKeyId"] == VALID_PUBLIC_KEY_ID

    def test_batch_session_accepts_prepared_batch(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
    ) -> None:
        fake_transport.enqueue(session_open_batch_resp.build().model_dump(mode="json"))
        client = _build_client(fake_transport, domain_auth_tokens.build())
        prepared_batch = PreparedBatch(
            form_code=FormSchema.FA3,
            offline_mode=False,
            batch_file=BatchFileInfo(
                file_size=10,
                file_hash=sha256_b64(b"plaintext"),
                parts=[
                    BatchFilePart(
                        ordinal_number=1,
                        file_size=12,
                        file_hash=sha256_b64(b"encrypted"),
                    )
                ],
            ),
            parts=[
                BatchPreparedPart(
                    ordinal_number=1,
                    content=b"encrypted",
                    file_size=len(b"encrypted"),
                    file_hash=sha256_b64(b"encrypted"),
                )
            ],
            encryption=BatchEncryptionData.from_bytes(
                aes_key=b"a" * 32,
                iv=b"b" * 16,
                encrypted_key=b"enc-key",
                public_key_id=VALID_PUBLIC_KEY_ID,
            ),
            invoices=[],
        )

        batch_client = client.batch_session(prepared_batch=prepared_batch)

        assert isinstance(batch_client, BatchSessionClient)
        assert batch_client.aes_key == b"a" * 32
        assert batch_client.iv == b"b" * 16
        call = fake_transport.calls[0]
        assert call.path == SessionRoutes.OPEN_BATCH
        assert call.json is not None
        assert call.json["encryption"]["publicKeyId"] == VALID_PUBLIC_KEY_ID

    def test_resume_online_session_reuses_authenticated_transport(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_online_session_state: BaseFactory[OnlineSessionState],
    ) -> None:
        client = _build_client(fake_transport, domain_auth_tokens.build())
        state = domain_online_session_state.build()

        resumed = client.resume_online_session(state)

        assert isinstance(resumed, OnlineSessionClient)
        assert resumed.get_state() == state

    def test_resume_batch_session_reuses_authenticated_transport(
        self,
        fake_transport: FakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_session_state: BaseFactory[BatchSessionState],
    ) -> None:
        client = _build_client(fake_transport, domain_auth_tokens.build())
        state = domain_batch_session_state.build()

        resumed = client.resume_batch_session(state)

        assert isinstance(resumed, BatchSessionClient)
        assert resumed.get_state() == state
