"""Authenticated async client branch composition."""

from functools import cached_property
from typing import final

from ksef2.clients._async_session import _AwaitableSession
from ksef2.clients.async_batch import AsyncBatchSessionClient
from ksef2.clients.async_certificates import AsyncCertificatesClient
from ksef2.clients.async_encryption import AsyncEncryptionClient
from ksef2.clients.async_invoice_sessions import AsyncInvoiceSessionsClient
from ksef2.clients.async_invoices import AsyncInvoicesClient
from ksef2.clients.async_limits import AsyncLimitsClient
from ksef2.clients.async_online import AsyncOnlineSessionClient
from ksef2.clients.async_permissions import AsyncPermissionsClient
from ksef2.clients.async_session_management import AsyncSessionManagementClient
from ksef2.clients.async_tokens import AsyncTokensClient
from ksef2.config import Environment
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core import exceptions
from ksef2.core.crypto import encrypt_symmetric_key, generate_session_key
from ksef2.core.middlewares.async_auth import AsyncBearerTokenMiddleware
from ksef2.core.stores import CertificateStore
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models import (
    BatchFileInfo,
    BatchSessionState,
    OpenBatchSessionRequest,
    PreparedBatch,
)
from ksef2.domain.models.session import (
    FormSchema,
    OnlineSessionState,
    OpenOnlineSessionRequest,
)
from ksef2.endpoints.async_session import AsyncSessionEndpoints
from ksef2.infra.mappers.sessions import from_spec as session_from_spec
from ksef2.infra.mappers.sessions import to_spec as session_to_spec
from ksef2.raw.async_facade import AsyncRawAuthenticatedClient
from ksef2.services.async_batch import AsyncBatchService
from ksef2.services.async_invoices import AsyncInvoicesService


@final
class AsyncAuthenticatedClient:
    """Authenticated async entry point for KSeF operations.

    Catch ``KSeFException`` for SDK-classified failures raised by authenticated
    branches, and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(
        self,
        transport: AsyncMiddleware,
        auth_tokens: AuthTokens,
        certificate_store: CertificateStore,
        environment: Environment = Environment.PRODUCTION,
    ) -> None:
        self._transport = transport
        self._auth_tokens = auth_tokens
        self._certificate_store = certificate_store
        self._environment = environment
        self._authed_transport = AsyncBearerTokenMiddleware(
            transport, auth_tokens.access_token.token
        )
        self._encryption_client = AsyncEncryptionClient(transport)
        self._session_eps = AsyncSessionEndpoints(self._authed_transport)

    @property
    def auth_tokens(self) -> AuthTokens:
        """Return the authenticated token pair used by this client branch."""
        return self._auth_tokens

    @property
    def access_token(self) -> str:
        """Return the bearer access token string used for authenticated calls."""
        return self._auth_tokens.access_token.token

    @property
    def refresh_token(self) -> str:
        """Return the refresh token string paired with the access token."""
        return self._auth_tokens.refresh_token.token

    async def _ensure_encryption_certificates_loaded(self) -> None:
        """Load public encryption certificates on first use."""
        if self._certificate_store.all():
            return
        self._certificate_store.load(await self._encryption_client.get_certificates())

    async def _get_encryption_material(
        self,
    ) -> tuple[bytes, bytes, bytes, str | None]:
        """Generate encrypted session material and keep the selected key id."""
        await self._ensure_encryption_certificates_loaded()

        cert = self._certificate_store.get_valid("symmetric_key_encryption")
        aes_key, iv = generate_session_key()
        encrypted_key = encrypt_symmetric_key(key=aes_key, cert_b64=cert.certificate)
        return aes_key, iv, encrypted_key, cert.public_key_id

    async def get_encryption_key(self) -> tuple[bytes, bytes, bytes]:
        """Generate a session AES key, IV, and encrypted symmetric key payload.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If symmetric-key encryption fails.
        """
        (
            aes_key,
            iv,
            encrypted_key,
            _public_key_id,
        ) = await self._get_encryption_material()
        return aes_key, iv, encrypted_key

    def online_session(
        self,
        *,
        form_code: FormSchema,
    ) -> _AwaitableSession[AsyncOnlineSessionClient]:
        """Open a new online invoice session and return a bound session client.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If symmetric-key encryption fails.
        """
        return _AwaitableSession(self._open_online_session(form_code=form_code))

    async def _open_online_session(
        self,
        *,
        form_code: FormSchema,
    ) -> AsyncOnlineSessionClient:
        (
            aes_key,
            iv,
            encrypted_key,
            public_key_id,
        ) = await self._get_encryption_material()

        request = OpenOnlineSessionRequest(
            encrypted_key=encrypted_key,
            iv=iv,
            public_key_id=public_key_id,
            form_code=form_code,
        )
        session_data = session_from_spec(
            await self._session_eps.open_online(session_to_spec(request))
        )

        state = OnlineSessionState.from_encoded(
            reference_number=session_data.reference_number,
            aes_key=aes_key,
            iv=iv,
            access_token=self.access_token,
            valid_until=session_data.valid_until,
            form_code=form_code,
        )
        return AsyncOnlineSessionClient(transport=self._authed_transport, state=state)

    def resume_online_session(
        self,
        state: OnlineSessionState,
    ) -> AsyncOnlineSessionClient:
        """Rebind an existing serialized online session state to this client."""
        return AsyncOnlineSessionClient(transport=self._authed_transport, state=state)

    def batch_session(
        self,
        *,
        prepared_batch: PreparedBatch | None = None,
        batch_file: BatchFileInfo | None = None,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
    ) -> _AwaitableSession[AsyncBatchSessionClient]:
        """Open a batch session for upload work.

        Args:
            prepared_batch: Prepared batch payload created by ``auth.batch.prepare_batch()``.
            batch_file: Declared ZIP package metadata and encrypted part metadata.
            form_code: Invoice schema declared for the batch session when ``batch_file``
                is provided directly.
            offline_mode: Whether to declare offline invoicing mode for the batch when
                ``batch_file`` is provided directly.

        Returns:
            A bound batch session client exposing presigned upload instructions.

        Raises:
            NoCertificateAvailableError: If certificate-backed encryption material is
                needed but no valid certificate is available.
            KSeFEncryptionError: If symmetric-key encryption fails.
            KSeFValidationError: If neither or both batch inputs are provided.
        """
        return _AwaitableSession(
            self._open_batch_session_from_input(
                prepared_batch=prepared_batch,
                batch_file=batch_file,
                form_code=form_code,
                offline_mode=offline_mode,
            )
        )

    async def _open_batch_session_from_input(
        self,
        *,
        prepared_batch: PreparedBatch | None = None,
        batch_file: BatchFileInfo | None = None,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
    ) -> AsyncBatchSessionClient:
        if prepared_batch is not None and batch_file is not None:
            raise exceptions.KSeFValidationError(
                "Pass either prepared_batch or batch_file when opening a batch session."
            )

        if prepared_batch is not None:
            encryption = prepared_batch.encryption
            return await self._open_batch_session(
                batch_file=prepared_batch.batch_file,
                aes_key=encryption.get_aes_key_bytes(),
                iv=encryption.get_iv_bytes(),
                encrypted_key=encryption.get_encrypted_key_bytes(),
                public_key_id=encryption.public_key_id,
                form_code=prepared_batch.form_code,
                offline_mode=prepared_batch.offline_mode,
                prepared_batch=prepared_batch,
            )

        if batch_file is None:
            raise exceptions.KSeFValidationError(
                "prepared_batch or batch_file is required when opening a batch session."
            )

        (
            aes_key,
            iv,
            encrypted_key,
            public_key_id,
        ) = await self._get_encryption_material()
        return await self._open_batch_session(
            batch_file=batch_file,
            aes_key=aes_key,
            iv=iv,
            encrypted_key=encrypted_key,
            public_key_id=public_key_id,
            form_code=form_code,
            offline_mode=offline_mode,
        )

    def open_batch_session(
        self,
        *,
        batch_file: BatchFileInfo,
        aes_key: bytes,
        iv: bytes,
        encrypted_key: bytes,
        public_key_id: str | None = None,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        prepared_batch: PreparedBatch | None = None,
    ) -> _AwaitableSession[AsyncBatchSessionClient]:
        """Open a batch session using caller-prepared encryption metadata.

        Args:
            batch_file: Declared ZIP package metadata and encrypted part metadata.
            aes_key: Raw symmetric key used for part encryption.
            iv: Initialization vector paired with ``aes_key``.
            encrypted_key: RSA-encrypted symmetric key sent to KSeF.
            public_key_id: Identifier of the KSeF public key used for encryption.
            form_code: Invoice schema declared for the batch session.
            offline_mode: Whether to declare offline invoicing mode for the batch.
            prepared_batch: Optional prepared batch payload to attach to the returned
                session so ``session.upload_parts()`` can operate without extra args.

        Returns:
            A bound batch session client exposing presigned upload instructions.

        Raises:
            KSeFValidationError: If the batch session request is invalid.
        """
        return _AwaitableSession(
            self._open_batch_session(
                batch_file=batch_file,
                aes_key=aes_key,
                iv=iv,
                encrypted_key=encrypted_key,
                public_key_id=public_key_id,
                form_code=form_code,
                offline_mode=offline_mode,
                prepared_batch=prepared_batch,
            )
        )

    async def _open_batch_session(
        self,
        *,
        batch_file: BatchFileInfo,
        aes_key: bytes,
        iv: bytes,
        encrypted_key: bytes,
        public_key_id: str | None = None,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        prepared_batch: PreparedBatch | None = None,
    ) -> AsyncBatchSessionClient:
        request = OpenBatchSessionRequest(
            encrypted_key=encrypted_key,
            iv=iv,
            public_key_id=public_key_id,
            batch_file=batch_file,
            form_code=form_code,
            offline_mode=offline_mode,
        )
        session_response = session_from_spec(
            await self._session_eps.open_batch(body=session_to_spec(request))
        )

        state = BatchSessionState.from_encoded(
            reference_number=session_response.reference_number,
            aes_key=aes_key,
            iv=iv,
            access_token=self.access_token,
            form_code=form_code,
            part_upload_requests=session_response.part_upload_requests,
        )
        return AsyncBatchSessionClient(
            transport=self._authed_transport,
            state=state,
            upload_transport=self._transport,
            prepared_batch=prepared_batch,
        )

    def resume_batch_session(
        self,
        state: BatchSessionState,
    ) -> AsyncBatchSessionClient:
        """Rebind an existing serialized batch session state to this client."""
        return AsyncBatchSessionClient(
            transport=self._authed_transport,
            state=state,
            upload_transport=self._transport,
        )

    @cached_property
    def invoices(self) -> AsyncInvoicesService:
        """Return the invoices service with encryption support configured."""
        return AsyncInvoicesService(
            self._authed_transport,
            self._transport,
            self._certificate_store,
            client=AsyncInvoicesClient(self._authed_transport),
            ensure_encryption_certificates_loaded=(
                self._ensure_encryption_certificates_loaded
            ),
        )

    @cached_property
    def batch(self) -> AsyncBatchService:
        """Return the high-level batch upload workflow service.

        The service orchestrates package preparation, session opening,
        presigned part uploads, session closing, and status polling.
        """
        return AsyncBatchService(
            authed_transport=self._authed_transport,
            upload_transport=self._transport,
            get_encryption_key=self._get_encryption_material,
            open_batch_session=self.open_batch_session,
        )

    @cached_property
    def limits(self) -> AsyncLimitsClient:
        """Return the authenticated rate-limit branch."""
        return AsyncLimitsClient(self._authed_transport)

    @cached_property
    def tokens(self) -> AsyncTokensClient:
        """Return the authenticated token lifecycle branch."""
        return AsyncTokensClient(self._authed_transport)

    @cached_property
    def certificates(self) -> AsyncCertificatesClient:
        """Return the authenticated certificate enrollment branch."""
        return AsyncCertificatesClient(self._authed_transport)

    @cached_property
    def sessions(self) -> AsyncSessionManagementClient:
        """Return the authenticated session-management branch."""
        return AsyncSessionManagementClient(self._authed_transport)

    @cached_property
    def invoice_sessions(self) -> AsyncInvoiceSessionsClient:
        """Return the authenticated invoice-session history branch."""
        return AsyncInvoiceSessionsClient(self._authed_transport)

    @cached_property
    def permissions(self) -> AsyncPermissionsClient:
        """Return the authenticated permissions branch."""
        return AsyncPermissionsClient(self._authed_transport)

    @cached_property
    def raw(self) -> AsyncRawAuthenticatedClient:
        """Return raw authenticated endpoints for advanced async integrations."""
        return AsyncRawAuthenticatedClient(
            transport=self._transport,
            authed_transport=self._authed_transport,
            environment=self._environment,
        )
