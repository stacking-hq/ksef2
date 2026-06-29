import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from polyfactory import BaseFactory

from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_online import AsyncOnlineSessionClient
from ksef2.core.exceptions import (
    KSeFClientClosedError,
    KSeFInvoiceProcessingTimeoutError,
    KSeFSessionError,
    NoCertificateAvailableError,
)
from ksef2.core.routes import EncryptionRoutes, InvoiceRoutes, SessionRoutes
from ksef2.core.stores import CertificateStore
from ksef2.domain.models.auth import AuthenticationResumeState, AuthTokens
from ksef2.domain.models.encryption import PublicKeyCertificate
from ksef2.domain.models.session import FormSchema, OnlineSessionResumeState
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport


def _build_client(
    async_fake_transport: AsyncFakeTransport,
    domain_online_session_state: BaseFactory[OnlineSessionResumeState],
) -> AsyncOnlineSessionClient:
    return AsyncOnlineSessionClient(
        async_fake_transport, domain_online_session_state.build()
    )


def _build_authenticated_client(
    async_fake_transport: AsyncFakeTransport,
    auth_tokens: AuthTokens,
    certificate_store: CertificateStore | None = None,
) -> AsyncAuthenticatedClient:
    return AsyncAuthenticatedClient(
        transport=async_fake_transport,
        auth_tokens=auth_tokens,
        certificate_store=certificate_store or CertificateStore(),
    )


class TestAsyncOnlineSessionClient:
    def test_authenticated_client_resume_state_exports_authentication_state(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
    ) -> None:
        auth_tokens = domain_auth_tokens.build()
        client = _build_authenticated_client(async_fake_transport, auth_tokens)

        state = client.resume_state()

        assert isinstance(state, AuthenticationResumeState)
        assert state.to_tokens() == auth_tokens

    def test_context_manager_reraises_close_failure_on_clean_exit(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        client = _build_client(async_fake_transport, domain_online_session_state)
        client.aclose = AsyncMock(side_effect=KSeFSessionError("close failed"))  # type: ignore[method-assign]

        async def _run() -> None:
            async with client:
                pass

        with pytest.raises(KSeFSessionError, match="close failed"):
            asyncio.run(_run())

    def test_aclose_is_idempotent_and_blocks_further_calls(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        state = domain_online_session_state.build()
        client = AsyncOnlineSessionClient(async_fake_transport, state)
        async_fake_transport.enqueue({})

        asyncio.run(client.aclose())
        asyncio.run(client.aclose())

        assert len(async_fake_transport.calls) == 1
        assert async_fake_transport.calls[0].method == "POST"
        assert async_fake_transport.calls[
            0
        ].path == SessionRoutes.TERMINATE_ONLINE.format(
            referenceNumber=state.reference_number
        )

        with pytest.raises(KSeFClientClosedError, match="Session client is closed"):
            asyncio.run(client.get_status())

    def test_wait_for_invoice_ready_returns_processed_status(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(async_fake_transport, domain_online_session_state)
        session_state = domain_online_session_state.build()
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        ksef_number = "1234567890-20260306-ABCDEF-123456-7A"

        async_fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=None,
                status=spec.InvoiceStatusInfo(code=100, description="Pending"),
            ).model_dump(mode="json")
        )
        async_fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=ksef_number,
                status=spec.InvoiceStatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        status = asyncio.run(
            client.wait_for_invoice_ready(
                invoice_reference_number=invoice_reference_number,
                timeout=1.0,
                poll_interval=0.0,
            )
        )

        assert status.ksef_number == ksef_number
        assert len(async_fake_transport.calls) == 2
        assert all(call.method == "GET" for call in async_fake_transport.calls)
        assert all(
            call.path
            == InvoiceRoutes.SESSION_INVOICE_STATUS.format(
                referenceNumber=session_state.reference_number,
                invoiceReferenceNumber=invoice_reference_number,
            )
            for call in async_fake_transport.calls
        )

    def test_wait_for_invoice_ready_raises_on_terminal_failure(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(async_fake_transport, domain_online_session_state)
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        async_fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=None,
                status=spec.InvoiceStatusInfo(code=450, description="Rejected"),
            ).model_dump(mode="json")
        )

        with pytest.raises(KSeFSessionError, match="Rejected"):
            asyncio.run(
                client.wait_for_invoice_ready(
                    invoice_reference_number=invoice_reference_number,
                    timeout=1.0,
                    poll_interval=0.0,
                )
            )

        assert len(async_fake_transport.calls) == 1

    def test_wait_for_invoice_ready_raises_on_timeout(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(async_fake_transport, domain_online_session_state)
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"

        async_fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=None,
                status=spec.InvoiceStatusInfo(code=100, description="Pending"),
            ).model_dump(mode="json")
        )

        with pytest.raises(KSeFInvoiceProcessingTimeoutError, match="not ready"):
            asyncio.run(
                client.wait_for_invoice_ready(
                    invoice_reference_number=invoice_reference_number,
                    timeout=0.0,
                    poll_interval=0.0,
                )
            )

    def test_send_invoice_and_wait(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(async_fake_transport, domain_online_session_state)
        session_state = domain_online_session_state.build()
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        ksef_number = "1234567890-20260306-ABCDEF-123456-7A"
        async_fake_transport.enqueue(
            inv_send_resp.build(referenceNumber=invoice_reference_number).model_dump(
                mode="json"
            )
        )
        async_fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=ksef_number,
                status=spec.InvoiceStatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        with patch(
            "ksef2.clients.async_online.encrypt_invoice", return_value=b"encrypted"
        ):
            status = asyncio.run(
                client.send_invoice_and_wait(
                    invoice_xml=b"<Invoice />",
                    timeout=1.0,
                    poll_interval=0.0,
                )
            )

        assert status.ksef_number == ksef_number
        assert async_fake_transport.calls[0].method == "POST"
        assert async_fake_transport.calls[0].path == InvoiceRoutes.SEND.format(
            referenceNumber=session_state.reference_number
        )
        assert async_fake_transport.calls[1].method == "GET"


class TestAsyncAuthenticatedOnlineSession:
    @patch(
        "ksef2.clients.async_authenticated.encrypt_symmetric_key",
        return_value=b"enc-key",
    )
    @patch(
        "ksef2.clients.async_authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_get_encryption_key_uses_fresh_symmetric_key_certificate_without_refresh(
        self,
        _mock_generate_session_key,
        _mock_encrypt_symmetric_key,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
    ) -> None:
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["symmetric_key_encryption"],
                )
            ]
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        async def _run() -> tuple[bytes, bytes, bytes]:
            return await client.get_encryption_key()

        aes_key, iv, encrypted_key = asyncio.run(_run())

        assert aes_key == b"k" * 32
        assert iv == b"v" * 16
        assert encrypted_key == b"enc-key"
        assert async_fake_transport.calls == []

    @patch(
        "ksef2.clients.async_authenticated.encrypt_symmetric_key",
        return_value=b"enc-key",
    )
    @patch(
        "ksef2.clients.async_authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_get_encryption_key_refreshes_stale_symmetric_key_certificate(
        self,
        _mock_generate_session_key,
        _mock_encrypt_symmetric_key,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        public_key_cert: BaseFactory[spec.PublicKeyCertificate],
    ) -> None:
        store = CertificateStore(refresh_after=timedelta(0))
        store.load(
            [
                domain_public_key_cert.build(
                    public_key_id="old-public-key-id",
                    usage=["symmetric_key_encryption"],
                )
            ]
        )
        refreshed_certificate = public_key_cert.build(
            validTo=datetime.now(timezone.utc) + timedelta(days=30),
            usage=[spec.PublicKeyCertificateUsage.SymmetricKeyEncryption],
        )
        async_fake_transport.enqueue(
            json_body=[refreshed_certificate.model_dump(mode="json")]
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        async def _run() -> tuple[bytes, bytes, bytes]:
            return await client.get_encryption_key()

        aes_key, iv, encrypted_key = asyncio.run(_run())

        assert aes_key == b"k" * 32
        assert iv == b"v" * 16
        assert encrypted_key == b"enc-key"
        assert async_fake_transport.calls[0].method == "GET"
        assert async_fake_transport.calls[0].path == (
            EncryptionRoutes.PUBLIC_KEY_CERTIFICATES
        )
        assert (
            store.get_valid("symmetric_key_encryption").public_key_id
            == refreshed_certificate.publicKeyId
        )

    @patch(
        "ksef2.clients.async_authenticated.encrypt_symmetric_key",
        return_value=b"enc-key",
    )
    @patch(
        "ksef2.clients.async_authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_get_encryption_key_fetches_certificates_when_store_lacks_symmetric_key_usage(
        self,
        _mock_generate_session_key,
        _mock_encrypt_symmetric_key,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        public_key_cert: BaseFactory[spec.PublicKeyCertificate],
    ) -> None:
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["ksef_token_encryption"],
                )
            ]
        )
        refreshed_certificate = public_key_cert.build(
            usage=[spec.PublicKeyCertificateUsage.SymmetricKeyEncryption]
        )
        async_fake_transport.enqueue(
            json_body=[refreshed_certificate.model_dump(mode="json")]
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        async def _run() -> tuple[bytes, bytes, bytes]:
            return await client.get_encryption_key()

        aes_key, iv, encrypted_key = asyncio.run(_run())

        assert aes_key == b"k" * 32
        assert iv == b"v" * 16
        assert encrypted_key == b"enc-key"
        assert async_fake_transport.calls[0].method == "GET"
        assert async_fake_transport.calls[0].path == (
            EncryptionRoutes.PUBLIC_KEY_CERTIFICATES
        )
        assert (
            store.get_valid("symmetric_key_encryption").public_key_id
            == refreshed_certificate.publicKeyId
        )

    def test_get_encryption_key_preserves_missing_symmetric_key_error_after_refresh(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        public_key_cert: BaseFactory[spec.PublicKeyCertificate],
    ) -> None:
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["ksef_token_encryption"],
                )
            ]
        )
        async_fake_transport.enqueue(
            json_body=[
                public_key_cert.build(
                    usage=[spec.PublicKeyCertificateUsage.KsefTokenEncryption]
                ).model_dump(mode="json")
            ]
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        async def _run() -> tuple[bytes, bytes, bytes]:
            return await client.get_encryption_key()

        with pytest.raises(
            NoCertificateAvailableError,
            match="No valid certificate for usage: symmetric_key_encryption",
        ):
            asyncio.run(_run())

        assert async_fake_transport.calls[0].method == "GET"
        assert async_fake_transport.calls[0].path == (
            EncryptionRoutes.PUBLIC_KEY_CERTIFICATES
        )

    @patch(
        "ksef2.clients.async_authenticated.encrypt_symmetric_key",
        return_value=b"enc-key",
    )
    @patch(
        "ksef2.clients.async_authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_online_session_uses_bearer_transport_and_returns_client(
        self,
        _mock_generate_session_key,
        _mock_encrypt_symmetric_key,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        session_open_online_resp: BaseFactory[spec.OpenOnlineSessionResponse],
    ) -> None:
        async_fake_transport.enqueue(
            session_open_online_resp.build().model_dump(mode="json")
        )
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["symmetric_key_encryption"],
                )
            ]
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        async def _run() -> AsyncOnlineSessionClient:
            return await client.online_session(form_code=FormSchema.FA3)

        session_client = asyncio.run(_run())

        assert isinstance(session_client, AsyncOnlineSessionClient)
        call = async_fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == SessionRoutes.OPEN_ONLINE
        assert call.headers == {"Authorization": "Bearer fake-access-token"}
        assert call.json is not None
        assert call.json["encryption"]["publicKeyId"] == store.all()[0].public_key_id
        assert "access_token" not in session_client.resume_state().to_dict()

    @patch(
        "ksef2.clients.async_authenticated.encrypt_symmetric_key",
        return_value=b"enc-key",
    )
    @patch(
        "ksef2.clients.async_authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_online_session_context_manager_opens_and_closes_session(
        self,
        _mock_generate_session_key,
        _mock_encrypt_symmetric_key,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        session_open_online_resp: BaseFactory[spec.OpenOnlineSessionResponse],
    ) -> None:
        reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        open_response = session_open_online_resp.build(referenceNumber=reference_number)
        async_fake_transport.enqueue(open_response.model_dump(mode="json"))
        async_fake_transport.enqueue({})
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["symmetric_key_encryption"],
                )
            ]
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        async def _run() -> None:
            async with client.online_session(form_code=FormSchema.FA3) as session:
                assert session.resume_state().reference_number == reference_number

        asyncio.run(_run())

        assert [call.method for call in async_fake_transport.calls] == ["POST", "POST"]
        assert async_fake_transport.calls[0].path == SessionRoutes.OPEN_ONLINE
        assert async_fake_transport.calls[1].path == (
            SessionRoutes.TERMINATE_ONLINE.format(referenceNumber=reference_number)
        )

    @patch(
        "ksef2.clients.async_authenticated.encrypt_symmetric_key",
        return_value=b"enc-key",
    )
    @patch(
        "ksef2.clients.async_authenticated.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_online_session_context_manager_closes_after_exception(
        self,
        _mock_generate_session_key,
        _mock_encrypt_symmetric_key,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_public_key_cert: BaseFactory[PublicKeyCertificate],
        session_open_online_resp: BaseFactory[spec.OpenOnlineSessionResponse],
    ) -> None:
        reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        async_fake_transport.enqueue(
            session_open_online_resp.build(referenceNumber=reference_number).model_dump(
                mode="json"
            )
        )
        async_fake_transport.enqueue({})
        store = CertificateStore()
        store.load(
            [
                domain_public_key_cert.build(
                    usage=["symmetric_key_encryption"],
                )
            ]
        )
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
            certificate_store=store,
        )

        async def _run() -> None:
            async with client.online_session(form_code=FormSchema.FA3):
                raise ValueError("block failed")

        with pytest.raises(ValueError, match="block failed"):
            asyncio.run(_run())

        assert async_fake_transport.calls[1].path == (
            SessionRoutes.TERMINATE_ONLINE.format(referenceNumber=reference_number)
        )

    def test_resume_online_session_context_manager_closes_session(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        client = _build_authenticated_client(
            async_fake_transport,
            domain_auth_tokens.build(),
        )
        state = domain_online_session_state.build()
        async_fake_transport.enqueue({})

        async def _run() -> None:
            async with client.resume_online_session(state=state) as session:
                assert session.resume_state() == state

        asyncio.run(_run())

        assert async_fake_transport.calls[0].path == (
            SessionRoutes.TERMINATE_ONLINE.format(
                referenceNumber=state.reference_number
            )
        )
