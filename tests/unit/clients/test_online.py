from unittest.mock import patch

import pytest
from polyfactory import BaseFactory

from ksef2.clients.online import OnlineSessionClient
from ksef2.core.exceptions import (
    KSeFClientClosedError,
    KSeFInvoiceProcessingTimeoutError,
    KSeFSessionError,
)
from ksef2.core.routes import InvoiceRoutes, SessionRoutes
from ksef2.domain.models.session import OnlineSessionResumeState
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport


def _build_client(
    fake_transport: FakeTransport,
    domain_online_session_state: BaseFactory[OnlineSessionResumeState],
) -> OnlineSessionClient:
    return OnlineSessionClient(fake_transport, domain_online_session_state.build())


class TestOnlineSessionClient:
    def test_close_is_idempotent_and_blocks_further_calls(
        self,
        fake_transport: FakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        state = domain_online_session_state.build()
        client = OnlineSessionClient(fake_transport, state)
        fake_transport.enqueue({})

        client.close()
        client.close()

        assert len(fake_transport.calls) == 1
        assert fake_transport.calls[0].method == "POST"
        assert fake_transport.calls[0].path == SessionRoutes.TERMINATE_ONLINE.format(
            referenceNumber=state.reference_number
        )

        with pytest.raises(KSeFClientClosedError, match="Session client is closed"):
            _ = client.get_status()

    def test_wait_for_invoice_ready_returns_processed_status(
        self,
        fake_transport: FakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(fake_transport, domain_online_session_state)
        session_state = domain_online_session_state.build()
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        ksef_number = "1234567890-20260306-ABCDEF-123456-7A"

        fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=None,
                status=spec.InvoiceStatusInfo(code=100, description="Pending"),
            ).model_dump(mode="json")
        )
        fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=ksef_number,
                status=spec.InvoiceStatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        status = client.wait_for_invoice_ready(
            invoice_reference_number=invoice_reference_number,
            timeout=1.0,
            poll_interval=0.0,
        )

        assert status.ksef_number == ksef_number
        assert len(fake_transport.calls) == 2
        assert all(call.method == "GET" for call in fake_transport.calls)
        assert all(
            call.path
            == InvoiceRoutes.SESSION_INVOICE_STATUS.format(
                referenceNumber=session_state.reference_number,
                invoiceReferenceNumber=invoice_reference_number,
            )
            for call in fake_transport.calls
        )

    def test_wait_for_invoice_ready_raises_on_terminal_failure(
        self,
        fake_transport: FakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(fake_transport, domain_online_session_state)
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=None,
                status=spec.InvoiceStatusInfo(code=450, description="Rejected"),
            ).model_dump(mode="json")
        )

        with pytest.raises(KSeFSessionError, match="Rejected"):
            _ = client.wait_for_invoice_ready(
                invoice_reference_number=invoice_reference_number,
                timeout=1.0,
                poll_interval=0.0,
            )

        assert len(fake_transport.calls) == 1

    def test_wait_for_invoice_ready_raises_on_timeout(
        self,
        fake_transport: FakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(fake_transport, domain_online_session_state)
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"

        for _ in range(5):
            fake_transport.enqueue(
                inv_session_invoice_status_resp.build(
                    referenceNumber=invoice_reference_number,
                    ksefNumber=None,
                    status=spec.InvoiceStatusInfo(code=100, description="Pending"),
                ).model_dump(mode="json")
            )

        with pytest.raises(KSeFInvoiceProcessingTimeoutError, match="not ready"):
            _ = client.wait_for_invoice_ready(
                invoice_reference_number=invoice_reference_number,
                timeout=0.0,
                poll_interval=0.0,
            )

    def test_send_invoice_and_wait(
        self,
        fake_transport: FakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        client = _build_client(fake_transport, domain_online_session_state)
        session_state = domain_online_session_state.build()
        invoice_reference_number = "20250625-EE-319D7EE000-B67F415CDC-2C"
        ksef_number = "1234567890-20260306-ABCDEF-123456-7A"
        fake_transport.enqueue(
            inv_send_resp.build(referenceNumber=invoice_reference_number).model_dump(
                mode="json"
            )
        )
        fake_transport.enqueue(
            inv_session_invoice_status_resp.build(
                referenceNumber=invoice_reference_number,
                ksefNumber=ksef_number,
                status=spec.InvoiceStatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        with patch("ksef2.clients.online.encrypt_invoice", return_value=b"encrypted"):
            status = client.send_invoice_and_wait(
                invoice_xml=b"<Invoice />",
                timeout=1.0,
                poll_interval=0.0,
            )

        assert status.ksef_number == ksef_number
        assert fake_transport.calls[0].method == "POST"
        assert fake_transport.calls[0].path == InvoiceRoutes.SEND.format(
            referenceNumber=session_state.reference_number
        )
        assert fake_transport.calls[1].method == "GET"
