"""Async batch session client for managing batch upload sessions."""

from types import TracebackType
from typing import final

from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models import BatchSessionState
from ksef2.domain.models.batch import PartUploadRequest, PreparedBatch
from ksef2.domain.models.session import (
    SessionInvoicesResponse,
    SessionStatusResponse,
)
from ksef2.endpoints.async_invoices import AsyncInvoicesEndpoints
from ksef2.endpoints.async_session import AsyncSessionEndpoints
from ksef2.infra.mappers.sessions import from_spec as session_from_spec
from ksef2.logging import get_logger

logger = get_logger(__name__)


@final
class AsyncBatchSessionClient:
    """Async client for managing an active batch session."""

    def __init__(
        self,
        transport: AsyncMiddleware,
        state: BatchSessionState,
        *,
        upload_transport: AsyncMiddleware | None = None,
        prepared_batch: PreparedBatch | None = None,
    ) -> None:
        self._transport = transport
        self._upload_transport = upload_transport or transport
        self._state = state
        self._prepared_batch = prepared_batch
        self._invoice_eps = AsyncInvoicesEndpoints(transport)
        self._session_eps = AsyncSessionEndpoints(transport)
        self._closed = False

    def _ensure_open(self) -> None:
        if self._closed:
            raise exceptions.KSeFClientClosedError("Session client is closed.")

    @property
    def reference_number(self) -> str:
        return self._state.reference_number

    @property
    def access_token(self) -> str:
        self._ensure_open()
        return self._state.access_token

    @property
    def aes_key(self) -> bytes:
        self._ensure_open()
        return self._state.get_aes_key_bytes()

    @property
    def iv(self) -> bytes:
        self._ensure_open()
        return self._state.get_iv_bytes()

    @property
    def part_upload_requests(self) -> list[PartUploadRequest]:
        self._ensure_open()
        return self._state.part_upload_requests

    def get_state(self) -> BatchSessionState:
        return self._state

    async def get_status(self) -> SessionStatusResponse:
        return session_from_spec(
            await self._invoice_eps.get_session_status(
                reference_number=self._state.reference_number,
            )
        )

    async def list_invoices(
        self,
        *,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> SessionInvoicesResponse:
        return session_from_spec(
            await self._invoice_eps.list_session_invoices(
                reference_number=self._state.reference_number,
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def list_failed_invoices(
        self,
        *,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> SessionInvoicesResponse:
        return session_from_spec(
            await self._invoice_eps.list_failed_session_invoices(
                reference_number=self._state.reference_number,
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def get_upo(self, *, upo_reference_number: str) -> bytes:
        return await self._session_eps.get_session_upo(
            reference_number=self._state.reference_number,
            upo_reference_number=upo_reference_number,
        )

    async def upload_parts(self) -> None:
        self._ensure_open()

        if self._prepared_batch is None:
            raise exceptions.KSeFValidationError(
                "Batch session has no prepared batch attached. "
                "Open it through auth.batch_session(prepared_batch=...) "
                "or auth.batch.open_session(prepared_batch=...)."
            )

        upload_requests = {
            request.ordinal_number: request
            for request in self._state.part_upload_requests
        }
        parts = {part.ordinal_number: part for part in self._prepared_batch.parts}

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

    async def aclose(self) -> None:
        if self._closed:
            return

        await self._session_eps.close_batch(
            reference_number=self._state.reference_number,
        )
        self._closed = True

    async def __aenter__(self) -> "AsyncBatchSessionClient":
        self._ensure_open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            await self.aclose()
        except exceptions.KSeFException:
            if exc_type is None:
                raise
            logger.warning(
                "Failed to close batch session",
                reference_number=self._state.reference_number,
                exc_info=True,
            )
