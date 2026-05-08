import asyncio
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from typing import final

from ksef2.clients.async_batch import AsyncBatchSessionClient
from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.polling import async_poll_until
from ksef2.domain.models.batch import BatchInvoice, BatchSessionState, PreparedBatch
from ksef2.domain.models.session import (
    FormSchema,
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


@final
class AsyncBatchService:
    """Async high-level workflow for preparing and sending invoice batches."""

    def __init__(
        self,
        *,
        authed_transport: AsyncMiddleware,
        upload_transport: AsyncMiddleware,
        get_encryption_key: Callable[
            [], Awaitable[tuple[bytes, bytes, bytes, str | None]]
        ],
        open_batch_session: Callable[..., Awaitable[AsyncBatchSessionClient]],
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
        aes_key, iv, encrypted_key, public_key_id = await self._get_encryption_key()
        return await asyncio.to_thread(
            prepare_batch_package,
            invoices=invoices,
            aes_key=aes_key,
            iv=iv,
            encrypted_key=encrypted_key,
            public_key_id=public_key_id,
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
        invoices = await asyncio.to_thread(load_batch_invoices, invoice_paths)
        return await self.prepare_batch(
            invoices=invoices,
            form_code=form_code,
            offline_mode=offline_mode,
            max_part_size=max_part_size,
        )

    async def open_session(
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
    ) -> BatchSessionState:
        async with await self.open_session(prepared_batch=prepared_batch) as session:
            state = session.get_state()
            await session.upload_parts()
        return state

    async def submit_batch(
        self,
        *,
        invoices: Iterable[BatchInvoice],
        form_code: FormSchema = FormSchema.FA3,
        offline_mode: bool = False,
        max_part_size: int = MAX_BATCH_PART_SIZE,
    ) -> BatchSessionState:
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
        session: str | BatchSessionState | AsyncBatchSessionClient,
    ) -> SessionStatusResponse:
        return session_from_spec(
            await self._invoice_eps.get_session_status(
                reference_number=self._resolve_reference_number(session),
            )
        )

    async def list_invoices(
        self,
        *,
        session: str | BatchSessionState | AsyncBatchSessionClient,
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

    async def list_failed_invoices(
        self,
        *,
        session: str | BatchSessionState | AsyncBatchSessionClient,
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

    async def get_upo(
        self,
        *,
        session: str | BatchSessionState | AsyncBatchSessionClient,
        upo_reference_number: str,
    ) -> bytes:
        return await self._session_eps.get_session_upo(
            reference_number=self._resolve_reference_number(session),
            upo_reference_number=upo_reference_number,
        )

    async def wait_for_completion(
        self,
        *,
        session: str | BatchSessionState | AsyncBatchSessionClient,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> SessionStatusResponse:
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
        session: str | BatchSessionState | AsyncBatchSessionClient,
    ) -> str:
        if isinstance(session, str):
            return session
        if isinstance(session, AsyncBatchSessionClient):
            return session.get_state().reference_number
        return session.reference_number
