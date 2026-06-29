"""Async high-level batch-session workflow service."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from typing import Protocol, final, runtime_checkable

from ksef2.clients._async_session import _AwaitableSession
from ksef2.clients.async_batch import AsyncBatchSessionClient
from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.polling import async_poll_until
from ksef2.domain.models.batch import (
    BatchFileInfo,
    BatchInvoice,
    BatchSessionResumeState,
    PreparedBatch,
)
from ksef2.domain.models.session import (
    FormSchema,
    SessionEncryptionMaterial,
    SessionInvoicesResponse,
    SessionStatusResponse,
)
from ksef2.endpoints.async_invoices import AsyncInvoicesEndpoints
from ksef2.endpoints.async_session import AsyncSessionEndpoints
from ksef2.infra.mappers.sessions import from_spec as session_from_spec
from ksef2.services.batch_preparation import (
    MAX_BATCH_PART_SIZE,
    load_batch_invoices,
    prepare_batch_package,
)


@runtime_checkable
class AsyncBatchSessionOpener(Protocol):
    def __call__(
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
    ) -> Awaitable[AsyncBatchSessionClient]: ...


@final
class AsyncBatchService:
    """Async high-level workflow for preparing and sending invoice batches.

    Catch ``KSeFException`` for SDK-classified failures raised by this service,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(
        self,
        *,
        authed_transport: AsyncMiddleware,
        upload_transport: AsyncMiddleware,
        get_encryption_key: Callable[[], Awaitable[SessionEncryptionMaterial]],
        open_batch_session: AsyncBatchSessionOpener,
    ) -> None:
        self._invoice_eps = AsyncInvoicesEndpoints(authed_transport)
        self._session_eps = AsyncSessionEndpoints(authed_transport)
        self._upload_transport = upload_transport
        self._get_encryption_key = get_encryption_key
        self._open_batch_session = open_batch_session

    async def prepare_batch(
        self,
        *,
        invoices: Iterable[BatchInvoice],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> PreparedBatch:
        """Build a ZIP package, split it, and encrypt each upload part.

        Args:
            invoices: Invoice XML payloads to include in the batch package.
            form_code: Invoice schema declared for the batch session.
            offline_mode: Whether to declare offline invoicing mode for the batch.
            max_part_size: Maximum size of each ZIP part before encryption.

        Returns:
            A prepared batch with encrypted part payloads and the metadata required
            to open a batch session.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If key or part encryption fails.
            KSeFValidationError: If the invoice list or part size is invalid.
        """
        material = await self._get_encryption_key()
        return await asyncio.to_thread(
            prepare_batch_package,
            invoices=invoices,
            aes_key=material.aes_key,
            iv=material.iv,
            encrypted_key=material.encrypted_key,
            public_key_id=material.public_key_id,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    async def prepare_batch_from_paths(
        self,
        *,
        invoice_paths: Iterable[Path | str],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> PreparedBatch:
        """Load invoice XML files from disk and prepare a batch package.

        Args:
            invoice_paths: Paths to XML files that should be added to the batch.
            form_code: Invoice schema declared for the batch session.
            offline_mode: Whether to declare offline invoicing mode for the batch.
            max_part_size: Maximum size of each ZIP part before encryption.

        Returns:
            A prepared batch with encrypted parts ready to be uploaded.

        Raises:
            FileNotFoundError: If an invoice XML path does not exist.
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If key or part encryption fails.
            KSeFValidationError: If the invoice list or part size is invalid.
        """
        invoices = await asyncio.to_thread(load_batch_invoices, invoice_paths)
        return await self.prepare_batch(
            invoices=invoices,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    def open_session(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> _AwaitableSession[AsyncBatchSessionClient]:
        """Open a batch session for an already prepared package.

        Args:
            prepared_batch: Prepared batch payload returned by ``prepare_batch()``.

        Returns:
            A session client exposing the upload instructions returned by KSeF.

        Raises:
            KSeFValidationError: If the prepared batch cannot be opened.
        """
        return _AwaitableSession(self._open_session(prepared_batch=prepared_batch))

    async def _open_session(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> AsyncBatchSessionClient:
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

    async def upload_parts(
        self,
        *,
        session: AsyncBatchSessionClient,
        prepared_batch: PreparedBatch,
    ) -> None:
        """Upload all prepared batch parts using the session's presigned URLs.

        Args:
            session: Open batch session that already contains upload instructions.
            prepared_batch: Prepared batch whose part ordinals match the session.

        Raises:
            KSeFClientClosedError: If the session client is closed.
            KSeFValidationError: If prepared part ordinals do not match session upload
                instructions.
            httpx.HTTPError: If uploading a part to its presigned URL fails.
        """
        upload_requests = {
            request.ordinal_number: request for request in session.part_upload_requests
        }
        parts = {part.ordinal_number: part for part in prepared_batch.parts}

        if set(upload_requests) != set(parts):
            raise exceptions.KSeFValidationError(
                "Prepared parts do not match the batch session upload instructions.",
                upload_ordinals=sorted(upload_requests),
                prepared_ordinals=sorted(parts),
            )

        for ordinal_number in sorted(upload_requests):
            upload_request = upload_requests[ordinal_number]
            part = parts[ordinal_number]
            _ = await self._upload_transport.request(
                upload_request.method,
                upload_request.url,
                headers={
                    "Content-Type": "application/octet-stream",
                    **{
                        key: value
                        for key, value in upload_request.headers.items()
                        if value is not None
                    },
                },
                content=part.content,
            )

    async def submit_prepared_batch(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> BatchSessionResumeState:
        """Open, upload, and close a batch session for a prepared package.

        Args:
            prepared_batch: Prepared batch payload returned by ``prepare_batch()``.

        Returns:
            Serializable state of the submitted batch session.

        Raises:
            KSeFClientClosedError: If the session client closes before upload.
            KSeFValidationError: If the prepared batch cannot be opened or uploaded.
            httpx.HTTPError: If uploading a part to its presigned URL fails.
        """
        async with self.open_session(prepared_batch=prepared_batch) as session:
            state = session.resume_state()
            await session.upload_parts()
        return state

    async def submit_batch(
        self,
        *,
        invoices: Iterable[BatchInvoice],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> BatchSessionResumeState:
        """Prepare and submit a batch in one call.

        Args:
            invoices: Invoice XML payloads to include in the batch package.
            form_code: Invoice schema declared for the batch session.
            offline_mode: Whether to declare offline invoicing mode for the batch.
            max_part_size: Maximum size of each ZIP part before encryption.

        Returns:
            Serializable state of the submitted batch session.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If key or part encryption fails.
            KSeFValidationError: If preparation, session opening, or upload validation
                fails.
            httpx.HTTPError: If uploading a part to its presigned URL fails.
        """
        prepared_batch = await self.prepare_batch(
            invoices=invoices,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )
        return await self.submit_prepared_batch(prepared_batch=prepared_batch)

    async def get_status(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
    ) -> SessionStatusResponse:
        """Fetch the current status of a batch session.

        Args:
            session: Session reference number, persisted state, or open session client.

        Returns:
            Current batch session status as reported by KSeF.
        """
        return session_from_spec(
            await self._invoice_eps.get_session_status(
                reference_number=self._resolve_reference_number(session),
            )
        )

    async def list_invoices(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> SessionInvoicesResponse:
        """Fetch one page of accepted invoices from a batch session."""
        return session_from_spec(
            await self._invoice_eps.list_session_invoices(
                reference_number=self._resolve_reference_number(session),
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def list_failed_invoices(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> SessionInvoicesResponse:
        """Fetch one page of failed invoices from a batch session."""
        return session_from_spec(
            await self._invoice_eps.list_failed_session_invoices(
                reference_number=self._resolve_reference_number(session),
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def get_upo(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        upo_reference_number: str,
    ) -> bytes:
        """Download the collective UPO for a batch session.

        Args:
            session: Session reference number, persisted state, or open session client.
            upo_reference_number: UPO page reference returned in the session status.

        Returns:
            Raw XML bytes of the requested UPO page.
        """
        return await self._session_eps.get_session_upo(
            reference_number=self._resolve_reference_number(session),
            upo_reference_number=upo_reference_number,
        )

    async def wait_for_completion(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> SessionStatusResponse:
        """Poll a batch session until KSeF reports a terminal status.

        Args:
            session: Session reference number, persisted state, or open session client.
            timeout: Maximum number of seconds to wait for completion.
            poll_interval: Delay between status checks.

        Returns:
            Final successful batch session status.

        Raises:
            KSeFSessionError: If batch processing reaches a failed terminal status.
            KSeFBatchSessionTimeoutError: If polling exceeds ``timeout``.
        """
        reference_number = self._resolve_reference_number(session)

        async def _poll() -> SessionStatusResponse:
            status = await self.get_status(session=reference_number)
            if status.status.code >= 400:
                raise exceptions.KSeFSessionError(
                    "Batch session processing failed: "
                    f"{reference_number} ({status.status.code}: {status.status.description})"
                )
            return status

        return await async_poll_until(
            operation=_poll,
            retry_predicate=lambda status: status.status.code < 200,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFBatchSessionTimeoutError(
                reference_number=reference_number,
                timeout=timeout,
            ),
        )

    @staticmethod
    def _resolve_reference_number(
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
    ) -> str:
        if isinstance(session, str):
            return session
        if isinstance(session, AsyncBatchSessionClient):
            return session.resume_state().reference_number
        return session.reference_number
