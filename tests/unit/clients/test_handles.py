"""Handles and session ``wait()`` / ``download_upo()``: success, KSeF failure, timeout."""

from typing import Any

import pytest
from polyfactory import BaseFactory

from ksef2._clients._async_handles import AsyncOperationHandle
from ksef2._clients._handles import OperationHandle
from ksef2._clients.online import InvoiceSubmission
from ksef2._core.exceptions import (
    KSeFBatchSessionTimeoutError,
    KSeFClientClosedError,
    KSeFInvoiceProcessingTimeoutError,
    KSeFInvoiceRejectedError,
    KSeFOnlineSessionTimeoutError,
    KSeFSessionError,
    KSeFValidationError,
)
from ksef2._core.routes import InvoiceRoutes, SessionRoutes
from ksef2._domain.models.batch import BatchSessionResumeState
from ksef2._domain.models.invoices import SendInvoiceResponse
from ksef2._domain.models.session import OnlineSessionResumeState
from ksef2._infra.schema.api import spec
from tests.unit.flavors import Flavor
from tests.unit.payloads import (
    INVOICE_REF,
    KSEF_NUMBER,
    UPO_REFS,
    invoice_status,
    session_status,
    upo,
)

XML = "<Faktura>zażółć</Faktura>"


class TestInvoiceSubmission:
    def _send(
        self,
        flavor: Flavor,
        state: OnlineSessionResumeState,
        send_resp: BaseFactory[spec.SendInvoiceResponse],
    ) -> tuple[Any, Any]:
        session = flavor.online_session(state)
        flavor.transport.enqueue(
            send_resp.build(referenceNumber=INVOICE_REF).model_dump(mode="json")
        )
        return session, flavor.run(session.send_invoice(XML))

    def test_exposes_every_send_invoice_response_field(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
    ) -> None:
        _, submission = self._send(
            flavor, domain_online_session_state.build(), inv_send_resp
        )

        base = AsyncOperationHandle if flavor.is_async else OperationHandle
        assert base in type(submission).__mro__
        assert submission.reference_number == INVOICE_REF
        for field in SendInvoiceResponse.model_fields:
            assert getattr(submission, field) == getattr(submission.response, field)
        with pytest.raises(AttributeError):
            _ = submission.no_such_field

    def test_send_accepts_positional_and_keyword_str_or_bytes(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        for _ in range(3):
            flavor.transport.enqueue(
                inv_send_resp.build(referenceNumber=INVOICE_REF).model_dump(mode="json")
            )

        flavor.run(session.send_invoice(XML))
        flavor.run(session.send_invoice(XML.encode()))
        flavor.run(session.send_invoice(invoice_xml=XML))

        hashes = {
            call.json["invoiceHash"] for call in flavor.transport.calls if call.json
        }
        assert len(flavor.transport.calls) == 3
        assert len(hashes) == 1

    def test_wait_returns_final_status(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        _, submission = self._send(
            flavor, domain_online_session_state.build(), inv_send_resp
        )
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 100, None)
        )
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 200, KSEF_NUMBER)
        )

        status = flavor.run(submission.wait(timeout=1.0, poll_interval=0.0))

        assert status.ksef_number == KSEF_NUMBER
        assert len(flavor.transport.calls) == 3

    def test_wait_raises_when_ksef_rejects_the_invoice(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        _, submission = self._send(
            flavor, domain_online_session_state.build(), inv_send_resp
        )
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 450, None)
        )

        with pytest.raises(KSeFInvoiceRejectedError) as exc_info:
            flavor.run(submission.wait(timeout=1.0, poll_interval=0.0))

        assert exc_info.value.invoice_status_code == 450
        assert exc_info.value.invoice_reference_number == INVOICE_REF

    def test_wait_times_out(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        _, submission = self._send(
            flavor, domain_online_session_state.build(), inv_send_resp
        )
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 100, None)
        )

        with pytest.raises(KSeFInvoiceProcessingTimeoutError):
            flavor.run(submission.wait(timeout=0.0, poll_interval=0.0))

    def test_handle_works_after_the_session_is_closed(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        session, submission = self._send(
            flavor, domain_online_session_state.build(), inv_send_resp
        )
        flavor.transport.enqueue(content=b"", status_code=204)
        flavor.close(session)
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 200, KSEF_NUMBER)
        )
        flavor.transport.enqueue(content=b"<upo />")

        with pytest.raises(KSeFClientClosedError):
            flavor.run(session.get_status())
        status = flavor.run(submission.wait(timeout=1.0, poll_interval=0.0))
        upo = flavor.run(submission.download_upo())

        assert status.ksef_number == KSEF_NUMBER
        assert upo == b"<upo />"
        assert flavor.transport.calls[-1].path == (
            InvoiceRoutes.INVOICE_UPO_BY_REFERENCE.format(
                referenceNumber=session.reference_number,
                invoiceReferenceNumber=INVOICE_REF,
            )
        )


class TestOnlineSessionWait:
    def test_wait_refuses_while_the_session_is_open(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())

        with pytest.raises(KSeFSessionError, match="still open"):
            flavor.run(session.wait())

        assert flavor.transport.calls == []

    def test_wait_returns_terminal_status_after_close(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(content=b"", status_code=204)
        flavor.close(session)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 170))
        flavor.transport.enqueue(session_status(inv_session_status_resp, 200))

        status = flavor.run(session.wait(timeout=1.0, poll_interval=0.0))

        assert status.status.code == 200

    def test_wait_raises_when_ksef_fails_the_session(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(content=b"", status_code=204)
        flavor.close(session)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 445))

        with pytest.raises(KSeFSessionError, match="445"):
            flavor.run(session.wait(timeout=1.0, poll_interval=0.0))

    def test_wait_times_out(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(content=b"", status_code=204)
        flavor.close(session)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 170))

        with pytest.raises(KSeFOnlineSessionTimeoutError):
            flavor.run(session.wait(timeout=0.0, poll_interval=0.0))

    def test_resumed_session_can_wait_without_local_close(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.online_session(
            domain_online_session_state.build(), resumed=True
        )
        flavor.transport.enqueue(session_status(inv_session_status_resp, 200))

        assert (
            flavor.run(session.wait(timeout=1.0, poll_interval=0.0)).status.code == 200
        )

    def test_download_upo_resolves_every_page_reference(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        state = domain_online_session_state.build()
        session = flavor.online_session(state)
        flavor.transport.enqueue(
            session_status(inv_session_status_resp, 200, upo(*UPO_REFS))
        )
        flavor.transport.enqueue(content=b"<upo-1 />")
        flavor.transport.enqueue(content=b"<upo-2 />")

        pages = flavor.run(session.download_upo())

        assert pages == [b"<upo-1 />", b"<upo-2 />"]
        assert [call.path for call in flavor.transport.calls[1:]] == [
            SessionRoutes.GET_SESSION_UPO.format(
                referenceNumber=state.reference_number, upoReferenceNumber=ref
            )
            for ref in UPO_REFS
        ]

    def test_download_upo_is_empty_when_ksef_issued_none(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(session_status(inv_session_status_resp, 445))

        assert flavor.run(session.download_upo()) == []

    def test_download_upo_requires_a_processed_session(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(session_status(inv_session_status_resp, 170))

        with pytest.raises(KSeFSessionError, match="wait"):
            flavor.run(session.download_upo())

    def test_download_invoice_upo_needs_exactly_one_identifier(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())

        with pytest.raises(KSeFValidationError):
            flavor.run(session.download_invoice_upo())
        with pytest.raises(KSeFValidationError):
            flavor.run(
                session.download_invoice_upo(ksef_number="k", reference_number="r")
            )

    def test_download_invoice_upo_by_ksef_number_and_by_reference(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        state = domain_online_session_state.build()
        session = flavor.online_session(state)
        flavor.transport.enqueue(content=b"<by-ksef />")
        flavor.transport.enqueue(content=b"<by-ref />")

        by_ksef = flavor.run(session.download_invoice_upo(ksef_number=KSEF_NUMBER))
        by_ref = flavor.run(session.download_invoice_upo(reference_number=INVOICE_REF))

        assert (by_ksef, by_ref) == (b"<by-ksef />", b"<by-ref />")
        assert flavor.transport.calls[0].path == (
            InvoiceRoutes.INVOICE_UPO_BY_KSEF.format(
                referenceNumber=state.reference_number, ksefNumber=KSEF_NUMBER
            )
        )


class TestBatchSessionWait:
    def test_wait_refuses_while_the_session_is_open(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        session = flavor.batch_session(domain_batch_session_state.build())

        with pytest.raises(KSeFSessionError, match="still open"):
            flavor.run(session.wait())

    def test_wait_returns_terminal_status_after_close(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.batch_session(domain_batch_session_state.build())
        flavor.transport.enqueue(content=b"", status_code=204)
        flavor.close(session)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 150))
        flavor.transport.enqueue(session_status(inv_session_status_resp, 200))

        status = flavor.run(session.wait(timeout=1.0, poll_interval=0.0))

        assert status.status.code == 200

    def test_wait_raises_when_ksef_fails_the_batch(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.batch_session(domain_batch_session_state.build())
        flavor.transport.enqueue(content=b"", status_code=204)
        flavor.close(session)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 445))

        with pytest.raises(KSeFSessionError, match="445"):
            flavor.run(session.wait(timeout=1.0, poll_interval=0.0))

    def test_wait_times_out(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.batch_session(domain_batch_session_state.build())
        flavor.transport.enqueue(content=b"", status_code=204)
        flavor.close(session)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 150))

        with pytest.raises(KSeFBatchSessionTimeoutError):
            flavor.run(session.wait(timeout=0.0, poll_interval=0.0))

    def test_resumed_session_can_wait_without_local_close(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.batch_session(domain_batch_session_state.build(), resumed=True)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 200))

        assert (
            flavor.run(session.wait(timeout=1.0, poll_interval=0.0)).status.code == 200
        )

    def test_download_upo_resolves_every_page_reference(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        state = domain_batch_session_state.build()
        session = flavor.batch_session(state)
        flavor.transport.enqueue(
            session_status(inv_session_status_resp, 200, upo(*UPO_REFS))
        )
        flavor.transport.enqueue(content=b"<upo-1 />")
        flavor.transport.enqueue(content=b"<upo-2 />")

        assert flavor.run(session.download_upo()) == [b"<upo-1 />", b"<upo-2 />"]
        assert [call.path for call in flavor.transport.calls[1:]] == [
            SessionRoutes.GET_SESSION_UPO.format(
                referenceNumber=state.reference_number, upoReferenceNumber=ref
            )
            for ref in UPO_REFS
        ]

    def test_download_upo_requires_a_processed_session(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        session = flavor.batch_session(domain_batch_session_state.build())
        flavor.transport.enqueue(session_status(inv_session_status_resp, 150))

        with pytest.raises(KSeFSessionError, match="wait"):
            flavor.run(session.download_upo())


def test_submission_is_exported_from_ksef2_clients() -> None:
    from ksef2 import clients

    assert clients.InvoiceSubmission is InvoiceSubmission
