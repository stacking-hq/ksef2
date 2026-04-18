import base64
from types import TracebackType
from typing import final

import httpx

from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.crypto import encrypt_invoice
from ksef2.core.polling import async_poll_until
from ksef2.domain.models import invoices
from ksef2.domain.models.invoices import SendInvoicePayload
from ksef2.domain.models.session import (
    OnlineSessionState,
    SessionInvoiceStatusResponse,
    SessionInvoicesResponse,
    SessionStatusResponse,
)
from ksef2.endpoints.async_invoices import AsyncInvoicesEndpoints
from ksef2.endpoints.async_session import AsyncSessionEndpoints
from ksef2.infra.mappers.invoices import from_spec as invoice_from_spec
from ksef2.infra.mappers.invoices import to_spec as invoice_to_spec
from ksef2.infra.mappers.sessions import from_spec as session_from_spec
from ksef2.logging import get_logger

logger = get_logger(__name__)


@final
class AsyncOnlineSessionClient:
    """Async client bound to a single online invoice session."""

    def __init__(self, transport: AsyncMiddleware, state: OnlineSessionState):
        self._transport = transport
        self._state = state
        self._invoice_eps = AsyncInvoicesEndpoints(transport)
        self._session_eps = AsyncSessionEndpoints(transport)
        self._closed = False

    def _ensure_open(self) -> None:
        if self._closed:
            raise exceptions.KSeFClientClosedError("Session client is closed.")

    async def send_invoice(self, *, invoice_xml: bytes) -> invoices.SendInvoiceResponse:
        self._ensure_open()
        encrypted = encrypt_invoice(
            xml_bytes=invoice_xml,
            key=base64.b64decode(self._state.aes_key),
            iv=base64.b64decode(self._state.iv),
        )
        request_body = invoice_to_spec(
            SendInvoicePayload(
                xml_bytes=invoice_xml,
                encrypted_bytes=encrypted,
            )
        )

        response_dto = await self._invoice_eps.send(
            reference_number=self._state.reference_number,
            body=request_body,
        )
        return invoice_from_spec(response_dto)

    async def send_invoice_and_wait(
        self,
        *,
        invoice_xml: bytes,
        timeout: float = 60.0,
        poll_interval: float = 2.0,
    ) -> SessionInvoiceStatusResponse:
        self._ensure_open()
        result = await self.send_invoice(invoice_xml=invoice_xml)
        return await self.wait_for_invoice_ready(
            invoice_reference_number=result.reference_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def get_status(self) -> SessionStatusResponse:
        self._ensure_open()
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
        self._ensure_open()
        return session_from_spec(
            await self._invoice_eps.list_session_invoices(
                reference_number=self._state.reference_number,
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def get_invoice_status(
        self, *, invoice_reference_number: str
    ) -> SessionInvoiceStatusResponse:
        self._ensure_open()
        return session_from_spec(
            await self._invoice_eps.get_session_invoice_status(
                reference_number=self._state.reference_number,
                invoice_reference_number=invoice_reference_number,
            )
        )

    async def wait_for_invoice_ready(
        self,
        *,
        invoice_reference_number: str,
        timeout: float = 60.0,
        poll_interval: float = 2.0,
    ) -> SessionInvoiceStatusResponse:
        self._ensure_open()

        async def _poll() -> SessionInvoiceStatusResponse:
            status = await self.get_invoice_status(
                invoice_reference_number=invoice_reference_number
            )
            if status.status.code >= 400:
                raise exceptions.KSeFSessionError(
                    "Invoice processing failed: "
                    f"{invoice_reference_number} ({status.status.code}: {status.status.description})"
                )
            return status

        return await async_poll_until(
            operation=_poll,
            retry_predicate=lambda status: not status.ksef_number,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFInvoiceProcessingTimeoutError(
                invoice_reference_number=invoice_reference_number,
                timeout=timeout,
            ),
        )

    async def list_failed_invoices(
        self,
        *,
        page_size: int = 10,
        continuation_token: str | None = None,
    ) -> SessionInvoicesResponse:
        self._ensure_open()
        return session_from_spec(
            await self._invoice_eps.list_failed_session_invoices(
                reference_number=self._state.reference_number,
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def get_invoice_upo_by_ksef_number(self, *, ksef_number: str) -> bytes:
        self._ensure_open()
        return await self._invoice_eps.get_invoice_upo_by_ksef(
            reference_number=self._state.reference_number,
            ksef_number=ksef_number,
        )

    async def get_invoice_upo_by_reference(
        self,
        *,
        invoice_reference_number: str,
    ) -> bytes:
        self._ensure_open()
        return await self._invoice_eps.get_invoice_upo_by_reference(
            reference_number=self._state.reference_number,
            invoice_reference_number=invoice_reference_number,
        )

    async def aclose(self) -> None:
        if self._closed:
            return

        await self._session_eps.terminate_online(
            reference_number=self._state.reference_number,
        )
        self._closed = True

    def get_state(self) -> OnlineSessionState:
        return self._state

    async def __aenter__(self) -> "AsyncOnlineSessionClient":
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
                "Failed to terminate KSeF session",
                reference_number=self._state.reference_number,
            )
        except httpx.HTTPError:
            if exc_type is None:
                raise
            logger.warning(
                "Transport error during session termination",
                reference_number=self._state.reference_number,
                exc_info=True,
            )
