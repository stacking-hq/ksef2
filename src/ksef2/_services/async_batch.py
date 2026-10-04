"""Async high-level batch-session workflow service."""

import asyncio
from collections.abc import Awaitable, Callable, Coroutine, Iterable
from pathlib import Path
from typing import Protocol, final, runtime_checkable

from typing_extensions import deprecated

from ksef2._clients._async_session import _AwaitableSession
from ksef2._clients.async_batch import AsyncBatchSessionClient
from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.async_external_transfer import AsyncExternalTransferClient
from ksef2._core.polling import async_poll_until
from ksef2._domain.models.batch import (
    BatchFileInfo,
    BatchInvoice,
    BatchSessionResumeState,
    PreparedBatch,
)
from ksef2._domain.models.session import (
    FormSchema,
    SessionEncryptionMaterial,
    SessionInvoicesResponse,
    SessionStatusResponse,
)
from ksef2._endpoints.async_invoices import AsyncInvoicesEndpoints
from ksef2._endpoints.async_session import AsyncSessionEndpoints
from ksef2._infra.mappers.sessions import from_spec as session_from_spec
from ksef2._services.batch_preparation import (
    MAX_BATCH_PART_SIZE,
    load_batch_invoices,
    load_batch_items,
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
        """Create the service.

        Args:
            authed_transport: Middleware chain used for authenticated API requests.
            upload_transport: Middleware used to upload batch parts to external storage.
            get_encryption_key: Coroutine function returning fresh session encryption material.
            open_batch_session: Callable that opens a batch session from a prepared batch.
        """
        self._invoice_eps = AsyncInvoicesEndpoints(authed_transport)
        self._session_eps = AsyncSessionEndpoints(authed_transport)
        self._external_transfers = AsyncExternalTransferClient(upload_transport)
        self._get_encryption_key = get_encryption_key
        self._open_batch_session = open_batch_session

    async def prepare(
        self,
        invoices: Iterable[bytes | str | Path | BatchInvoice],
        *,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> PreparedBatch:
        """Build a ZIP package, split it, and encrypt each upload part.

        Args:
            invoices: Invoices to include. Each item is invoice XML as ``bytes`` or ``str`` (named ``invoice-<position>.xml``), a ``Path`` to an XML file (keeps its file name) or a ``BatchInvoice`` with an explicit file name.
            form_code: Invoice schema declared for the batch session.
            offline_mode: Whether to declare offline invoicing mode for the batch.
            max_part_size: Maximum size of each ZIP part before encryption.

        Returns:
            A prepared batch with encrypted part payloads and the metadata required
            to open a batch session.

        Raises:
            FileNotFoundError: If an invoice XML path does not exist.
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If key or part encryption fails.
            KSeFValidationError: If the invoice list or part size is invalid.

        Example:
            ```python
            batch = await auth.batch.prepare([xml_1, xml_2])
            session = await auth.batch.submit(batch)
            ```
        """
        loaded = await asyncio.to_thread(load_batch_items, invoices)
        return await self._prepare(
            invoices=loaded,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    async def _prepare(
        self,
        *,
        invoices: Iterable[BatchInvoice],
        form_code: FormSchema,
        offline_mode: bool,
        max_part_size: int,
    ) -> PreparedBatch:
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

    async def submit(
        self,
        batch: PreparedBatch | Iterable[bytes | str | Path | BatchInvoice],
        *,
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> AsyncBatchSessionClient:
        """Open a batch session, upload the parts and close the session.

        Args:
            batch: A prepared batch from ``prepare()``, or the invoices themselves, which are prepared first (same item types as ``prepare()``).
            form_code: Invoice schema declared for the batch session. Ignored for a prepared batch, which carries its own.
            offline_mode: Whether to declare offline invoicing mode for the batch. Ignored for a prepared batch.
            max_part_size: Maximum size of each ZIP part before encryption. Ignored for a prepared batch.

        Returns:
            The closed batch session client. Call its ``wait()`` for the terminal status, ``list_failed_invoices()`` for rejected invoices and ``download_upo()`` for the UPO pages.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If key or part encryption fails.
            KSeFValidationError: If preparation, session opening, or upload validation
                fails.
            KSeFBatchUploadError: If external storage rejects an upload or its
                outcome cannot be determined. Call ``recovery_state()`` on the error
                to deliberately recover the sensitive batch state.

        Example:
            ```python
            session = await auth.batch.submit([xml_1, xml_2])
            final = await session.wait()
            upos = await session.download_upo()
            ```
        """
        if isinstance(batch, PreparedBatch):
            prepared_batch = batch
        else:
            prepared_batch = await self.prepare(
                batch,
                form_code=form_code,
                offline_mode=offline_mode,
                max_part_size=max_part_size,
            )
        async with self._open_session(prepared_batch=prepared_batch) as session:
            await session.upload_parts()
        return session

    @deprecated(
        "`prepare_batch()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `prepare()` instead."
    )
    def prepare_batch(
        self,
        *,
        invoices: Iterable[BatchInvoice],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> Coroutine[None, None, PreparedBatch]:
        """Deprecated: build a ZIP package, split it, and encrypt each upload part.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``prepare()`` instead.

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
        return self._prepare(
            invoices=invoices,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    @deprecated(
        "`prepare_batch_from_paths()` is deprecated and will be removed in "
        "ksef2 1.10.0; use `prepare()` instead."
    )
    def prepare_batch_from_paths(
        self,
        *,
        invoice_paths: Iterable[Path | str],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> Coroutine[None, None, PreparedBatch]:
        """Deprecated: load invoice XML files from disk and prepare a batch package.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``prepare()`` with ``Path`` items instead.

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
        return self._prepare_batch_from_paths(
            invoice_paths=invoice_paths,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    async def _prepare_batch_from_paths(
        self,
        *,
        invoice_paths: Iterable[Path | str],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> PreparedBatch:
        invoices = await asyncio.to_thread(load_batch_invoices, invoice_paths)
        return await self._prepare(
            invoices=invoices,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    @deprecated(
        "`open_session()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `auth.batch_session()` instead."
    )
    def open_session(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> _AwaitableSession[AsyncBatchSessionClient]:
        """Deprecated: open a batch session for an already prepared package.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``auth.batch_session(prepared_batch=...)`` instead.

        Args:
            prepared_batch: Prepared batch payload returned by ``prepare()``.

        Returns:
            A session client exposing the upload instructions returned by KSeF.

        Raises:
            KSeFValidationError: If the prepared batch cannot be opened.
        """
        return self._open_session(prepared_batch=prepared_batch)

    def _open_session(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> _AwaitableSession[AsyncBatchSessionClient]:
        return _AwaitableSession(
            self._open_session_client(prepared_batch=prepared_batch)
        )

    async def _open_session_client(
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
            KSeFBatchUploadError: If external storage rejects an upload or its
                outcome cannot be determined. Call ``recovery_state()`` on the error
                to deliberately recover the sensitive batch state.
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
            try:
                await self._external_transfers.upload_part(
                    method=upload_request.method,
                    url=upload_request.url,
                    headers={
                        "Content-Type": "application/octet-stream",
                        **{
                            key: value
                            for key, value in upload_request.headers.items()
                            if value is not None
                        },
                    },
                    content=part.content,
                    reference_number=session.reference_number,
                    part_ordinal=ordinal_number,
                )
            except exceptions.KSeFExternalTransferError as exc:
                raise exceptions.KSeFBatchUploadError(
                    transfer_error=exc,
                    recovery_state=session.resume_state(),
                ) from exc

    @deprecated(
        "`submit_prepared_batch()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `submit()` instead."
    )
    def submit_prepared_batch(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> Coroutine[None, None, BatchSessionResumeState]:
        """Deprecated: open, upload, and close a batch session for a prepared package.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``submit()`` instead.

        Args:
            prepared_batch: Prepared batch payload returned by ``prepare()``.

        Returns:
            Serializable state of the submitted batch session.

        Raises:
            KSeFClientClosedError: If the session client closes before upload.
            KSeFValidationError: If the prepared batch cannot be opened or uploaded.
            KSeFBatchUploadError: If external storage rejects an upload or its
                outcome cannot be determined. Call ``recovery_state()`` on the error
                to deliberately recover the sensitive batch state.
        """
        return self._submit_prepared_batch(prepared_batch=prepared_batch)

    async def _submit_prepared_batch(
        self,
        *,
        prepared_batch: PreparedBatch,
    ) -> BatchSessionResumeState:
        return (await self.submit(prepared_batch)).resume_state()

    @deprecated(
        "`submit_batch()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `submit()` instead."
    )
    def submit_batch(
        self,
        *,
        invoices: Iterable[BatchInvoice],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> Coroutine[None, None, BatchSessionResumeState]:
        """Deprecated: prepare and submit a batch in one call.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``submit()`` instead.

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
            KSeFBatchUploadError: If external storage rejects an upload or its
                outcome cannot be determined. Call ``recovery_state()`` on the error
                to deliberately recover the sensitive batch state.
        """
        return self._submit_batch(
            invoices=invoices,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    async def _submit_batch(
        self,
        *,
        invoices: Iterable[BatchInvoice],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> BatchSessionResumeState:
        prepared_batch = await self._prepare(
            invoices=invoices,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )
        return (await self.submit(prepared_batch)).resume_state()

    @deprecated(
        "`get_status()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `BatchSessionClient.get_status()` instead."
    )
    def get_status(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
    ) -> Coroutine[None, None, SessionStatusResponse]:
        """Deprecated: fetch the current status of a batch session.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``BatchSessionClient.get_status()`` instead.

        Args:
            session: Session reference number, persisted state, or open session client.

        Returns:
            Current batch session status as reported by KSeF.
        """
        return self._get_status(session=session)

    async def _get_status(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
    ) -> SessionStatusResponse:
        return session_from_spec(
            await self._invoice_eps.get_session_status(
                reference_number=self._resolve_reference_number(session),
            )
        )

    @deprecated(
        "`list_invoices()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `BatchSessionClient.list_invoices()` instead."
    )
    def list_invoices(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> Coroutine[None, None, SessionInvoicesResponse]:
        """Deprecated: fetch one page of accepted invoices from a batch session.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``BatchSessionClient.list_invoices()`` instead.

        Args:
            session: Session reference number, persisted state, or open session client.
            page_size: Number of invoices per page (10–1000).
            continuation_token: Token from the previous page's response; ``None`` requests the first page.

        Returns:
            One page of invoices accepted in the session, with a continuation token when more exist.
        """
        return self._list_invoices(
            session=session, page_size=page_size, continuation_token=continuation_token
        )

    async def _list_invoices(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> SessionInvoicesResponse:
        return session_from_spec(
            await self._invoice_eps.list_session_invoices(
                reference_number=self._resolve_reference_number(session),
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    @deprecated(
        "`list_failed_invoices()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `BatchSessionClient.list_failed_invoices()` instead."
    )
    def list_failed_invoices(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> Coroutine[None, None, SessionInvoicesResponse]:
        """Deprecated: fetch one page of failed invoices from a batch session.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``BatchSessionClient.list_failed_invoices()`` instead.

        Args:
            session: Session reference number, persisted state, or open session client.
            page_size: Number of invoices per page (10–1000).
            continuation_token: Token from the previous page's response; ``None`` requests the first page.

        Returns:
            One page of invoices that failed processing, with a continuation token when more exist.
        """
        return self._list_failed_invoices(
            session=session, page_size=page_size, continuation_token=continuation_token
        )

    async def _list_failed_invoices(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> SessionInvoicesResponse:
        return session_from_spec(
            await self._invoice_eps.list_failed_session_invoices(
                reference_number=self._resolve_reference_number(session),
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    @deprecated(
        "`get_upo()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `BatchSessionClient.download_upo()` instead."
    )
    def get_upo(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        upo_reference_number: str,
    ) -> Coroutine[None, None, bytes]:
        """Deprecated: download the collective UPO for a batch session.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``BatchSessionClient.download_upo()`` instead.

        Args:
            session: Session reference number, persisted state, or open session client.
            upo_reference_number: UPO page reference returned in the session status.

        Returns:
            Raw XML bytes of the requested UPO page.
        """
        return self._session_eps.get_session_upo(
            reference_number=self._resolve_reference_number(session),
            upo_reference_number=upo_reference_number,
        )

    @deprecated(
        "`wait_for_completion()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `BatchSessionClient.wait()` instead."
    )
    def wait_for_completion(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> Coroutine[None, None, SessionStatusResponse]:
        """Deprecated: poll a batch session until KSeF reports a terminal status.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``BatchSessionClient.wait()`` instead.

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
        return self._wait_for_completion(
            session=session, timeout=timeout, poll_interval=poll_interval
        )

    async def _wait_for_completion(
        self,
        *,
        session: str | BatchSessionResumeState | AsyncBatchSessionClient,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> SessionStatusResponse:
        reference_number = self._resolve_reference_number(session)

        async def _poll() -> SessionStatusResponse:
            status = session_from_spec(
                await self._invoice_eps.get_session_status(
                    reference_number=reference_number,
                )
            )
            if status.status.code >= 400:
                raise exceptions.KSeFSessionError(
                    "Batch session processing failed: "
                    f"{reference_number} ({status.status.code}: {status.status.description})",
                    hint="See why invoices failed with `list_failed_invoices()`.",
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
