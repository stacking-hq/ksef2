"""Authenticated async client branch composition."""

from functools import cached_property
from typing import final, overload

from typing_extensions import deprecated

from ksef2._clients._async_session import _AwaitableSession
from ksef2._clients.async_batch import AsyncBatchSessionClient
from ksef2._clients.async_certificates import AsyncCertificatesClient
from ksef2._clients.async_collective_identifiers import (
    AsyncCollectiveIdentifiersClient,
)
from ksef2._clients.async_encryption import AsyncEncryptionClient
from ksef2._clients.async_invoice_sessions import AsyncInvoiceSessionsClient
from ksef2._clients.async_invoices import AsyncInvoicesClient
from ksef2._clients.async_limits import AsyncLimitsClient
from ksef2._clients.async_online import AsyncOnlineSessionClient
from ksef2._clients.async_permissions import AsyncPermissionsClient
from ksef2._clients.async_session_management import AsyncSessionManagementClient
from ksef2._clients.async_testdata import AsyncTestDataClient
from ksef2._clients.async_tokens import AsyncTokensClient
from ksef2._config import Environment
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core import exceptions
from ksef2._core.crypto import encrypt_symmetric_key, generate_session_key
from ksef2._core.middlewares.async_auth import AsyncBearerTokenMiddleware
from ksef2._core.stores import CertificateStoreProtocol
from ksef2._domain.models.auth import AuthenticationResumeState, AuthTokens
from ksef2._domain.models import (
    BatchFileInfo,
    BatchSessionResumeState,
    OpenBatchSessionRequest,
    PreparedBatch,
)
from ksef2._domain.models.session import (
    FormSchema,
    OnlineSessionResumeState,
    OpenOnlineSessionRequest,
    SessionEncryptionMaterial,
)
from ksef2._endpoints.async_session import AsyncSessionEndpoints
from ksef2._infra.mappers.sessions import from_spec as session_from_spec
from ksef2._infra.mappers.sessions import to_spec as session_to_spec
from ksef2.raw._async_facade import AsyncRawAuthenticatedClient
from ksef2._services.async_batch import AsyncBatchService
from ksef2._services.async_invoices import AsyncInvoicesService


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
        certificate_store: CertificateStoreProtocol,
        environment: Environment = Environment.PRODUCTION,
        transfer_transport: AsyncMiddleware | None = None,
    ) -> None:
        """Create the client.

        Args:
            transport: Middleware chain used for requests.
            auth_tokens: Access and refresh tokens obtained from authentication.
            certificate_store: Store holding the KSeF public-key certificates used to encrypt session keys.
            environment: KSeF environment the client talks to.
            transfer_transport: Middleware used for transfers outside the KSeF API such as batch part uploads; defaults to ``transport``.
        """
        self._transport = transport
        self._transfer_transport = transfer_transport or transport
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
        """Return the authenticated token pair used by this client branch.

        Returns:
            The authenticated token pair used by this client branch.
        """
        return self._auth_tokens

    @property
    def access_token(self) -> str:
        """Return the bearer access token string used for authenticated calls.

        Returns:
            The bearer access token string used for authenticated calls.
        """
        return self._auth_tokens.access_token.token

    @property
    def refresh_token(self) -> str:
        """Return the refresh token string paired with the access token.

        Returns:
            The refresh token string paired with the access token.
        """
        return self._auth_tokens.refresh_token.token

    def resume_state(self) -> AuthenticationResumeState:
        """Return the authentication state needed to rehydrate this branch later.

        Returns:
            The authentication state needed to rehydrate this branch later.
        """
        return AuthenticationResumeState.from_tokens(self._auth_tokens)

    async def _ensure_encryption_certificates_loaded(self) -> None:
        """Load public encryption certificates when the cache needs refresh."""
        if self._certificate_store.needs_refresh("symmetric_key_encryption"):
            self._certificate_store.load(
                await self._encryption_client.get_certificates()
            )

    async def _get_encryption_material(
        self,
    ) -> SessionEncryptionMaterial:
        """Generate encrypted session material and keep the selected key id."""
        await self._ensure_encryption_certificates_loaded()

        cert = self._certificate_store.get_valid("symmetric_key_encryption")
        aes_key, iv = generate_session_key()
        encrypted_key = encrypt_symmetric_key(key=aes_key, cert_b64=cert.certificate)
        return SessionEncryptionMaterial(
            aes_key=aes_key,
            iv=iv,
            encrypted_key=encrypted_key,
            public_key_id=cert.public_key_id,
        )

    async def get_encryption_key(self) -> tuple[bytes, bytes, bytes]:
        """Generate a session AES key, IV, and encrypted symmetric key payload.

        Returns:
            A tuple of the raw AES key, the initialization vector and the AES key encrypted with the KSeF public key.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If symmetric-key encryption fails.
        """
        material = await self._get_encryption_material()
        return material.aes_key, material.iv, material.encrypted_key

    async def _open_online_session(
        self,
        *,
        form_code: FormSchema,
    ) -> AsyncOnlineSessionClient:
        material = await self._get_encryption_material()

        request = OpenOnlineSessionRequest(
            encrypted_key=material.encrypted_key,
            iv=material.iv,
            public_key_id=material.public_key_id,
            form_code=form_code,
        )
        session_data = session_from_spec(
            await self._session_eps.open_online(session_to_spec(request))
        )

        state = OnlineSessionResumeState.from_encoded(
            reference_number=session_data.reference_number,
            aes_key=material.aes_key,
            iv=material.iv,
            valid_until=session_data.valid_until,
            form_code=form_code,
        )
        return AsyncOnlineSessionClient(transport=self._authed_transport, state=state)

    @overload
    def online_session(
        self,
        *,
        form_code: FormSchema,
    ) -> _AwaitableSession[AsyncOnlineSessionClient]: ...

    @overload
    def online_session(
        self,
        *,
        state: OnlineSessionResumeState | str,
    ) -> _AwaitableSession[AsyncOnlineSessionClient]: ...

    def online_session(
        self,
        *,
        form_code: FormSchema | None = None,
        state: OnlineSessionResumeState | str | None = None,
    ) -> _AwaitableSession[AsyncOnlineSessionClient]:
        """Open a new online invoice session, or resume one from saved state.

        Pass exactly one of ``form_code`` (open a new session) or ``state``
        (resume). When resuming, the form code, keys and expiry all come from the
        state. Leaving the ``with`` block closes the session in both cases;
        closing an already-closed session is a no-op.

        Args:
            form_code: Invoice schema the new session accepts, for example ``FormSchema.FA3``.
            state: State from ``session.resume_state()``, or its JSON string, to resume an open session.

        Returns:
            A session client that can be used as a context manager and closes the session on exit.

        Raises:
            KSeFArgumentError: If neither or both of ``form_code`` and ``state`` are given.
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If symmetric-key encryption fails.
            KSeFValidationError: If ``state`` is not valid online session state.

        Example:
            ```python
            from ksef2.models import FormSchema

            async with auth.online_session(form_code=FormSchema.FA3) as session:
                submission = await session.send_invoice(xml_bytes)
                saved = session.resume_state().to_json()

            async with auth.online_session(state=saved) as session:
                result = await session.submission(reference_number).wait()
            ```
        """
        if (form_code is None) == (state is None):
            raise exceptions.KSeFArgumentError(
                "online_session() takes either form_code (to open a new session) "
                "or state (to resume one), not both and not neither."
            )
        if state is not None:
            return _AwaitableSession(self._resume_online_session_async(state))
        assert form_code is not None
        return _AwaitableSession(self._open_online_session(form_code=form_code))

    async def _resume_online_session_async(
        self, state: OnlineSessionResumeState | str
    ) -> AsyncOnlineSessionClient:
        return self._rebind_online_session(state)

    def _rebind_online_session(
        self, state: OnlineSessionResumeState | str
    ) -> AsyncOnlineSessionClient:
        resume = (
            OnlineSessionResumeState.from_json(state)
            if isinstance(state, str)
            else state
        )
        return AsyncOnlineSessionClient(
            transport=self._authed_transport, state=resume, resumed=True
        )

    @deprecated(
        "`resume_online_session()` is deprecated and will be removed in "
        "ksef2 1.10.0; use `online_session(state=...)` instead."
    )
    def resume_online_session(
        self,
        state: OnlineSessionResumeState,
    ) -> AsyncOnlineSessionClient:
        """Deprecated: rebind an existing serialized online session state to this client.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``online_session(state=...)`` instead.

        Args:
            state: State previously exported from an online session client.

        Returns:
            An online session client bound to the saved state.
        """
        return self._rebind_online_session(state)

    @overload
    def batch_session(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> _AwaitableSession[AsyncBatchSessionClient]: ...

    @overload
    def batch_session(
        self,
        *,
        batch_file: BatchFileInfo,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
    ) -> _AwaitableSession[AsyncBatchSessionClient]: ...

    @overload
    def batch_session(
        self,
        *,
        state: BatchSessionResumeState | str,
    ) -> _AwaitableSession[AsyncBatchSessionClient]: ...

    def batch_session(
        self,
        *,
        prepared_batch: PreparedBatch | None = None,
        batch_file: BatchFileInfo | None = None,
        form_code: FormSchema | None = None,
        offline_mode: bool | None = None,
        state: BatchSessionResumeState | str | None = None,
    ) -> _AwaitableSession[AsyncBatchSessionClient]:
        """Open a batch session for upload work, or resume one from saved state.

        Pass exactly one of ``prepared_batch``, ``batch_file`` (open a new
        session) or ``state`` (resume). When resuming, everything comes from the
        state, including the form code, keys and part upload requests. Leaving the
        ``with`` block closes the session in every case; closing an already-closed
        session is a no-op.

        Args:
            prepared_batch: Prepared batch payload created by ``auth.batch.prepare()``.
            batch_file: Declared ZIP package metadata and encrypted part metadata.
            form_code: Invoice schema declared for the batch session when ``batch_file`` is provided directly; defaults to ``FormSchema.FA3``.
            offline_mode: Whether to declare offline invoicing mode for the batch when ``batch_file`` is provided directly; defaults to ``False``.
            state: State from ``session.resume_state()``, or its JSON string, to resume a batch session.

        Returns:
            A bound batch session client exposing presigned upload instructions.

        Raises:
            KSeFArgumentError: If not exactly one of ``prepared_batch``, ``batch_file`` and ``state`` is given, or ``form_code`` or ``offline_mode`` is combined with ``prepared_batch`` or ``state``.
            NoCertificateAvailableError: If certificate-backed encryption material is
                needed but no valid certificate is available.
            KSeFEncryptionError: If symmetric-key encryption fails.
            KSeFValidationError: If ``state`` is not valid batch session state.

        Example:
            ```python
            from ksef2.models import BatchInvoice

            prepared = await auth.batch.prepare(
                [BatchInvoice(file_name="invoice-1.xml", content=xml_bytes)],
            )
            async with auth.batch_session(prepared_batch=prepared) as session:
                await session.upload_parts()
                saved = session.resume_state().to_json()

            async with auth.batch_session(state=saved) as session:
                final = await session.wait()
            ```
        """
        given = [
            name
            for name, value in (
                ("prepared_batch", prepared_batch),
                ("batch_file", batch_file),
                ("state", state),
            )
            if value is not None
        ]
        if len(given) != 1:
            raise exceptions.KSeFArgumentError(
                "batch_session() takes exactly one of prepared_batch, batch_file "
                f"or state; got {', '.join(given) if given else 'none'}."
            )
        if batch_file is None and (form_code is not None or offline_mode is not None):
            raise exceptions.KSeFArgumentError(
                "form_code and offline_mode apply only with batch_file; a "
                "prepared batch or saved state already carries them."
            )
        if state is not None:
            return _AwaitableSession(self._resume_batch_session_async(state))
        return _AwaitableSession(
            self._open_batch_session_from_input(
                prepared_batch=prepared_batch,
                batch_file=batch_file,
                form_code=form_code or FormSchema.FA3,
                offline_mode=bool(offline_mode),
            )
        )

    async def _resume_batch_session_async(
        self, state: BatchSessionResumeState | str
    ) -> AsyncBatchSessionClient:
        return self._rebind_batch_session(state)

    def _rebind_batch_session(
        self, state: BatchSessionResumeState | str
    ) -> AsyncBatchSessionClient:
        resume = (
            BatchSessionResumeState.from_json(state)
            if isinstance(state, str)
            else state
        )
        return AsyncBatchSessionClient(
            transport=self._authed_transport,
            state=resume,
            upload_transport=self._transfer_transport,
            access_token=self.access_token,
            resumed=True,
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
                encryption_material=SessionEncryptionMaterial(
                    aes_key=encryption.get_aes_key_bytes(),
                    iv=encryption.get_iv_bytes(),
                    encrypted_key=encryption.get_encrypted_key_bytes(),
                    public_key_id=encryption.public_key_id,
                ),
                form_code=prepared_batch.form_code,
                offline_mode=prepared_batch.offline_mode,
                prepared_batch=prepared_batch,
            )

        if batch_file is None:
            raise exceptions.KSeFValidationError(
                "prepared_batch or batch_file is required when opening a batch session."
            )

        material = await self._get_encryption_material()
        return await self._open_batch_session(
            batch_file=batch_file,
            encryption_material=material,
            form_code=form_code,
            offline_mode=offline_mode,
        )

    async def _open_batch_session(
        self,
        *,
        batch_file: BatchFileInfo,
        encryption_material: SessionEncryptionMaterial,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        prepared_batch: PreparedBatch | None = None,
    ) -> AsyncBatchSessionClient:
        request = OpenBatchSessionRequest(
            encrypted_key=encryption_material.encrypted_key,
            iv=encryption_material.iv,
            public_key_id=encryption_material.public_key_id,
            batch_file=batch_file,
            form_code=form_code,
            offline_mode=offline_mode,
        )
        session_response = session_from_spec(
            await self._session_eps.open_batch(body=session_to_spec(request))
        )

        state = BatchSessionResumeState.from_encoded(
            reference_number=session_response.reference_number,
            aes_key=encryption_material.aes_key,
            iv=encryption_material.iv,
            form_code=form_code,
            part_upload_requests=session_response.part_upload_requests,
        )
        return AsyncBatchSessionClient(
            transport=self._authed_transport,
            state=state,
            upload_transport=self._transfer_transport,
            prepared_batch=prepared_batch,
            access_token=self.access_token,
        )

    def _open_batch_session_with_material(
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
        return _AwaitableSession(
            self._open_batch_session(
                batch_file=batch_file,
                encryption_material=SessionEncryptionMaterial(
                    aes_key=aes_key,
                    iv=iv,
                    encrypted_key=encrypted_key,
                    public_key_id=public_key_id,
                ),
                form_code=form_code,
                offline_mode=offline_mode,
                prepared_batch=prepared_batch,
            )
        )

    @deprecated(
        "`open_batch_session()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `raw` instead."
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
        """Deprecated: open a batch session using caller-prepared encryption metadata.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``auth.batch_session()`` for the standard flow, or ``raw`` for caller-supplied encryption material.

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
        return self._open_batch_session_with_material(
            batch_file=batch_file,
            aes_key=aes_key,
            iv=iv,
            encrypted_key=encrypted_key,
            public_key_id=public_key_id,
            form_code=form_code,
            offline_mode=offline_mode,
            prepared_batch=prepared_batch,
        )

    @deprecated(
        "`resume_batch_session()` is deprecated and will be removed in "
        "ksef2 1.10.0; use `batch_session(state=...)` instead."
    )
    def resume_batch_session(
        self,
        state: BatchSessionResumeState,
    ) -> AsyncBatchSessionClient:
        """Deprecated: rebind an existing serialized batch session state to this client.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``batch_session(state=...)`` instead.

        Args:
            state: State previously exported from a batch session client.

        Returns:
            A batch session client bound to the saved state.
        """
        return self._rebind_batch_session(state)

    @cached_property
    def invoices(self) -> AsyncInvoicesService:
        """Return the invoices service with encryption support configured.

        Returns:
            The invoices service with encryption support configured.
        """
        return AsyncInvoicesService(
            self._authed_transport,
            self._transfer_transport,
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

        Returns:
            The batch upload service.
        """
        return AsyncBatchService(
            authed_transport=self._authed_transport,
            upload_transport=self._transfer_transport,
            get_encryption_key=self._get_encryption_material,
            open_batch_session=self._open_batch_session_with_material,
        )

    @cached_property
    def limits(self) -> AsyncLimitsClient:
        """Return the authenticated rate-limit branch.

        Returns:
            The authenticated rate-limit branch.
        """
        return AsyncLimitsClient(self._authed_transport)

    @cached_property
    def collective_identifiers(self) -> AsyncCollectiveIdentifiersClient:
        """Return the collective invoice identifier branch.

        Returns:
            The collective invoice identifier branch.
        """
        return AsyncCollectiveIdentifiersClient(self._authed_transport)

    @cached_property
    def tokens(self) -> AsyncTokensClient:
        """Return the authenticated token lifecycle branch.

        Returns:
            The authenticated token lifecycle branch.
        """
        return AsyncTokensClient(self._authed_transport)

    @cached_property
    def certificates(self) -> AsyncCertificatesClient:
        """Return the authenticated certificate enrollment branch.

        Returns:
            The authenticated certificate enrollment branch.
        """
        return AsyncCertificatesClient(self._authed_transport)

    @cached_property
    def sessions(self) -> AsyncSessionManagementClient:
        """Return the authenticated session-management branch.

        Returns:
            The authenticated session-management branch.
        """
        return AsyncSessionManagementClient(self._authed_transport)

    @cached_property
    def invoice_sessions(self) -> AsyncInvoiceSessionsClient:
        """Return the authenticated invoice-session history branch.

        Returns:
            The authenticated invoice-session history branch.
        """
        return AsyncInvoiceSessionsClient(self._authed_transport)

    @cached_property
    def permissions(self) -> AsyncPermissionsClient:
        """Return the authenticated permissions branch.

        Returns:
            The authenticated permissions branch.
        """
        return AsyncPermissionsClient(self._authed_transport)

    @cached_property
    def testdata(self) -> AsyncTestDataClient:
        """Return authenticated TEST-only data mutation helpers.

        Returns:
            Authenticated TEST-only data mutation helpers.
        """
        if self._environment is not Environment.TEST:
            raise exceptions.KSeFUnsupportedEnvironmentError(
                "testdata is only available for Environment.TEST"
            )
        return AsyncTestDataClient(self._authed_transport)

    @cached_property
    def raw(self) -> AsyncRawAuthenticatedClient:
        """Return raw authenticated endpoints for advanced async integrations.

        Returns:
            Raw authenticated endpoints for advanced async integrations.
        """
        return AsyncRawAuthenticatedClient(
            transport=self._transport,
            authed_transport=self._authed_transport,
            environment=self._environment,
        )
