"""Async client bound to an open online invoice session."""

from types import TracebackType
from typing import final

import httpx
from typing_extensions import deprecated

from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.crypto import encrypt_invoice
from ksef2._core.polling import async_poll_until
from ksef2._domain.models import invoices
from ksef2._domain.models.invoices import SendInvoicePayload
from ksef2._domain.models.session import (
    OnlineSessionResumeState,
    SessionInvoiceStatusResponse,
    SessionInvoicesResponse,
    SessionStatusResponse,
)
from ksef2._endpoints.async_invoices import AsyncInvoicesEndpoints
from ksef2._endpoints.async_session import AsyncSessionEndpoints
from ksef2._infra.mappers.invoices import from_spec as invoice_from_spec
from ksef2._infra.mappers.invoices import to_spec as invoice_to_spec
from ksef2._infra.mappers.sessions import from_spec as session_from_spec
from ksef2._logging import get_logger

logger = get_logger(__name__)


@final
class AsyncOnlineSessionClient:
    """Async client bound to a single online invoice session.

    Catch ``KSeFException`` for SDK-classified failures raised by this session
    branch, and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        KSeFClientClosedError: If an operation is attempted after closing the session.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(self, transport: AsyncMiddleware, state: OnlineSessionResumeState):
        """Create the session client.

        Args:
            transport: Middleware chain used for authenticated requests.
            state: Resume state describing the open session and its encryption keys.
        """
        self._transport = transport
        self._state = state
        self._invoice_eps = AsyncInvoicesEndpoints(transport)
        self._session_eps = AsyncSessionEndpoints(transport)
        self._closed = False

    def _ensure_open(self) -> None:
        """Reject operations after the session client has been closed."""
        if self._closed:
            raise exceptions.KSeFClientClosedError("Session client is closed.")

    async def send_invoice(self, *, invoice_xml: bytes) -> invoices.SendInvoiceResponse:
        """Encrypt and submit one invoice into the open session.

        Args:
            invoice_xml: Invoice XML bytes, valid against the session's schema.

        Returns:
            The reference number KSeF assigned to the submission. Poll ``get_invoice_status()`` or use ``send_invoice_and_wait()`` for the processing result.

        Raises:
            KSeFEncryptionError: If invoice encryption fails.

        Example:
            ```python
            async with auth.online_session(form_code=FormSchema.FA3) as session:
                sent = await session.send_invoice(invoice_xml=xml_bytes)
                status = await session.wait_for_invoice_ready(
                    invoice_reference_number=sent.reference_number,
                )
            ```
        """
        self._ensure_open()
        encrypted = encrypt_invoice(
            xml_bytes=invoice_xml,
            key=self._state.get_aes_key_bytes(),
            iv=self._state.get_iv_bytes(),
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
        """Submit an invoice and poll until KSeF assigns a final processing result.

        Args:
            invoice_xml: Invoice XML bytes, valid against the session's schema.
            timeout: Maximum number of seconds to wait before giving up.
            poll_interval: Delay in seconds between invoice status checks.

        Returns:
            The final processing status, including the invoice's KSeF number once accepted.

        Raises:
            KSeFEncryptionError: If invoice encryption fails.
            KSeFInvoiceRejectedError: If invoice processing reaches a failed
                terminal status. It subclasses ``KSeFSessionError`` and keeps the
                status ``details`` and ``extensions``.
            KSeFInvoiceProcessingTimeoutError: If polling exceeds ``timeout``.

        Example:
            ```python
            async with auth.online_session(form_code=FormSchema.FA3) as session:
                status = await session.send_invoice_and_wait(invoice_xml=xml_bytes)
                print(status.ksef_number)
            ```
        """
        self._ensure_open()
        result = await self.send_invoice(invoice_xml=invoice_xml)
        return await self.wait_for_invoice_ready(
            invoice_reference_number=result.reference_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def get_status(self) -> SessionStatusResponse:
        """Fetch the current state of the online session.

        Returns:
            The session status, including invoice counters.
        """
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
        """Fetch one page of invoices submitted in this session.

        Args:
            page_size: Number of invoices per page (10–1000).
            continuation_token: Token from the previous page's response; ``None`` requests the first page.

        Returns:
            One page of invoices submitted in the session, with a continuation token when more exist.
        """
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
        """Fetch processing status for one invoice sent in this session.

        Args:
            invoice_reference_number: Reference number of the invoice within the session, as returned by ``send_invoice()``.

        Returns:
            The processing status of the invoice.
        """
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
        """Poll invoice status until it succeeds, fails, or times out.

        Args:
            invoice_reference_number: Reference number of the invoice within the session, as returned by ``send_invoice()``.
            timeout: Maximum number of seconds to wait before giving up.
            poll_interval: Delay in seconds between invoice status checks.

        Returns:
            The final processing status, including the invoice's KSeF number once accepted.

        Raises:
            KSeFInvoiceRejectedError: If invoice processing reaches a failed
                terminal status. It subclasses ``KSeFSessionError`` and keeps the
                status ``details`` and ``extensions``.
            KSeFInvoiceProcessingTimeoutError: If polling exceeds ``timeout``.
        """
        self._ensure_open()

        async def _poll() -> SessionInvoiceStatusResponse:
            status = await self.get_invoice_status(
                invoice_reference_number=invoice_reference_number
            )
            if status.status.code >= 400:
                raise exceptions.KSeFInvoiceRejectedError(
                    invoice_reference_number=invoice_reference_number,
                    status=status,
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
        """Fetch one page of invoices that failed within this session.

        Args:
            page_size: Number of invoices per page (10–1000).
            continuation_token: Token from the previous page's response; ``None`` requests the first page.

        Returns:
            One page of invoices that failed processing, with a continuation token when more exist.
        """
        self._ensure_open()
        return session_from_spec(
            await self._invoice_eps.list_failed_session_invoices(
                reference_number=self._state.reference_number,
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def get_invoice_upo_by_ksef_number(self, *, ksef_number: str) -> bytes:
        """Download the invoice UPO by KSeF number.

        Args:
            ksef_number: KSeF number of an invoice accepted in this session.

        Returns:
            The UPO as XML bytes.
        """
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
        """Download the invoice UPO by session invoice reference number.

        Args:
            invoice_reference_number: Reference number of the invoice within the session, as returned by ``send_invoice()``.

        Returns:
            The UPO as XML bytes.
        """
        self._ensure_open()
        return await self._invoice_eps.get_invoice_upo_by_reference(
            reference_number=self._state.reference_number,
            invoice_reference_number=invoice_reference_number,
        )

    async def aclose(self) -> None:
        """Terminate the online session if it is still open.

        Raises:
            KSeFApiError: If KSeF rejects the session termination request.
            httpx.HTTPError: If the HTTP transport fails before KSeF returns a
                response.
        """
        if self._closed:
            return

        await self._session_eps.terminate_online(
            reference_number=self._state.reference_number,
        )
        self._closed = True

    def resume_state(self) -> OnlineSessionResumeState:
        """Return the sensitive session state needed to resume later.

        Returns:
            The sensitive session state needed to resume later.
        """
        return self._state

    @deprecated(
        "`get_state()` is deprecated and will be removed in ksef2 2.0; "
        "use `resume_state()` instead."
    )
    def get_state(self) -> OnlineSessionResumeState:
        """Deprecated compatibility wrapper for ``resume_state()``.

        Deprecated:
            Will be removed in ksef2 2.0. Use ``resume_state()`` instead.

        Returns:
            The same state as ``resume_state()``.
        """
        return self.resume_state()

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
