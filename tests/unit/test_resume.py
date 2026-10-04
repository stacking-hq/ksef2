"""Resuming through the method that starts: sessions, exports and submissions."""

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from polyfactory import BaseFactory
from pydantic import SecretStr

from ksef2 import AsyncClient, Client
from ksef2._core.crypto import encrypt_invoice
from ksef2._core.exceptions import KSeFExportFailedError
from ksef2._core.routes import SessionRoutes
from ksef2._domain.models.auth import AuthenticationResumeState, AuthTokens
from ksef2._domain.models.batch import (
    BatchFileInfo,
    BatchSessionResumeState,
    PreparedBatch,
)
from ksef2._domain.models.invoices import ExportHandle, ExportResumeState
from ksef2._domain.models.session import FormSchema, OnlineSessionResumeState
from ksef2._infra.schema.api import spec
from tests.unit.flavors import Flavor
from tests.unit.payloads import (
    INVOICE_REF,
    KSEF_1,
    KSEF_2,
    archive,
    invoice_status,
    package_status,
    session_status,
)
from tests.unit.test_invoice_workflows_helpers import filters

KEY = b"k" * 32
IV = b"v" * 16


def _auth(flavor: Flavor, tokens: BaseFactory[AuthTokens]) -> Any:
    return flavor.authenticated(tokens.build())


def _paths(flavor: Flavor) -> list[str]:
    return [call.path for call in flavor.transport.calls]


class TestOnlineSessionForms:
    def test_both_forms_or_neither_raise_type_error(
        self, flavor: Flavor, domain_auth_tokens: BaseFactory[AuthTokens]
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = OnlineSessionResumeState(
            reference_number="r",
            aes_key=SecretStr("a" * 43 + "="),
            iv=SecretStr("b" * 22 + "=="),
            valid_until="2030-01-01T00:00:00Z",  # pyright: ignore[reportArgumentType]
            form_code=FormSchema.FA3,
        )

        with pytest.raises(TypeError, match="either form_code"):
            auth.online_session()
        with pytest.raises(TypeError, match="either form_code"):
            auth.online_session(form_code=FormSchema.FA3, state=state)

    @pytest.mark.parametrize("as_json", [False, True])
    def test_state_resumes_from_object_or_json(
        self,
        flavor: Flavor,
        as_json: bool,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_online_session_state.build()

        session = flavor.run(
            auth.online_session(state=state.to_json() if as_json else state)
        )

        assert session.resume_state() == state
        assert flavor.transport.calls == []

    def test_exit_closes_an_open_resumed_session(
        self,
        flavor: Flavor,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_online_session_state.build()
        flavor.transport.enqueue(session_status(inv_session_status_resp, 100))
        flavor.transport.enqueue(content=b"", status_code=204)

        session = flavor.run(auth.online_session(state=state))
        flavor.close(session)
        flavor.close(session)

        assert _paths(flavor)[-1] == SessionRoutes.TERMINATE_ONLINE.format(
            referenceNumber=state.reference_number
        )
        assert len(flavor.transport.calls) == 2

    def test_closing_an_already_closed_resumed_session_is_a_no_op(
        self,
        flavor: Flavor,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_online_session_state.build()
        flavor.transport.enqueue(session_status(inv_session_status_resp, 200))

        session = flavor.run(auth.online_session(state=state))
        flavor.close(session)

        assert len(flavor.transport.calls) == 1  # status only, no terminate

    def test_resume_online_session_is_a_deprecated_alias(
        self,
        flavor: Flavor,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_online_session_state.build()

        with pytest.warns(DeprecationWarning, match="online_session\\(state=...\\)"):
            session = auth.resume_online_session(state)

        assert session.resume_state() == state


class TestBatchSessionForms:
    def test_exactly_one_form_is_allowed(
        self,
        flavor: Flavor,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_file_info: BaseFactory[BatchFileInfo],
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_batch_session_state.build()
        file_info = domain_batch_file_info.build()

        with pytest.raises(TypeError, match="exactly one"):
            auth.batch_session()
        with pytest.raises(TypeError, match="exactly one"):
            auth.batch_session(batch_file=file_info, state=state)
        with pytest.raises(TypeError, match="exactly one"):
            auth.batch_session(
                prepared_batch=MagicMock(spec=PreparedBatch), state=state
            )
        with pytest.raises(TypeError, match="exactly one"):
            auth.batch_session(
                prepared_batch=MagicMock(spec=PreparedBatch), batch_file=file_info
            )
        with pytest.raises(TypeError, match="only with batch_file"):
            auth.batch_session(state=state, form_code=FormSchema.FA3)

    @pytest.mark.parametrize("as_json", [False, True])
    def test_state_resumes_from_object_or_json(
        self,
        flavor: Flavor,
        as_json: bool,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_batch_session_state.build()

        session = flavor.run(
            auth.batch_session(state=state.to_json() if as_json else state)
        )

        assert session.resume_state() == state
        assert session.part_upload_requests == state.part_upload_requests

    def test_exit_closes_an_open_resumed_batch_and_skips_a_closed_one(
        self,
        flavor: Flavor,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_batch_session_state.build()
        flavor.transport.enqueue(session_status(inv_session_status_resp, 100))
        flavor.transport.enqueue(json_body={})
        flavor.transport.enqueue(session_status(inv_session_status_resp, 150))

        opened = flavor.run(auth.batch_session(state=state))
        flavor.close(opened)
        flavor.close(opened)
        closed_already = flavor.run(auth.batch_session(state=state))
        flavor.close(closed_already)

        assert _paths(flavor)[1] == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=state.reference_number
        )
        assert len(flavor.transport.calls) == 3  # status, close, status

    def test_resume_batch_session_is_a_deprecated_alias(
        self,
        flavor: Flavor,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        auth = _auth(flavor, domain_auth_tokens)
        state = domain_batch_session_state.build()

        with pytest.warns(DeprecationWarning, match="batch_session\\(state=...\\)"):
            session = auth.resume_batch_session(state)

        assert session.resume_state() == state


class TestSubmission:
    def test_submission_on_fresh_and_resumed_sessions(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        state = domain_online_session_state.build()
        for resumed in (False, True):
            flavor.transport.clear()
            session = flavor.online_session(state, resumed=resumed)
            flavor.transport.enqueue(
                invoice_status(inv_session_invoice_status_resp, 200, KSEF_1)
            )
            flavor.transport.enqueue(content=b"<upo />")

            submission = session.submission(INVOICE_REF)

            assert flavor.transport.calls == []  # lazy
            assert submission.reference_number == INVOICE_REF
            assert (
                flavor.run(submission.wait(timeout=1.0, poll_interval=0.0)).ksef_number
                == KSEF_1
            )
            assert flavor.run(submission.download_upo()) == b"<upo />"


class TestAuthenticationResume:
    def test_resume_accepts_a_json_string(
        self, domain_auth_tokens: BaseFactory[AuthTokens]
    ) -> None:
        tokens = domain_auth_tokens.build()
        state = AuthenticationResumeState.from_tokens(tokens)
        client = Client(http_client=MagicMock(spec=httpx.Client))

        authenticated = client.authentication.resume(state.to_json())

        assert authenticated.resume_state().to_tokens() == tokens

    async def test_async_resume_accepts_a_json_string(
        self, domain_auth_tokens: BaseFactory[AuthTokens]
    ) -> None:
        tokens = domain_auth_tokens.build()
        state = AuthenticationResumeState.from_tokens(tokens)
        client = AsyncClient(http_client=MagicMock(spec=httpx.AsyncClient))

        authenticated = client.authentication.resume(state.to_json())

        assert authenticated.resume_state().to_tokens() == tokens


class TestExportResumeState:
    def _state(self) -> ExportResumeState:
        return ExportResumeState.from_handle(
            ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)
        )

    def test_round_trips_through_json_and_dict(self) -> None:
        state = self._state()

        assert ExportResumeState.from_json(state.to_json()) == state
        assert ExportResumeState.from_dict(state.to_dict()) == state
        assert state.to_handle() == ExportHandle(
            reference_number="export-ref", aes_key=KEY, iv=IV
        )
        assert state.format_version == 1

    def test_secrets_are_redacted_outside_to_json_and_to_dict(self) -> None:
        state = self._state()
        secret = state.aes_key.get_secret_value()

        assert secret not in repr(state)
        assert secret not in str(state.model_dump())
        assert secret not in state.model_dump_json()
        assert secret in state.to_json()
        assert secret in str(state.to_dict())

    def test_redacted_or_invalid_state_is_rejected(self) -> None:
        state = self._state()

        with pytest.raises(ValueError):
            ExportResumeState.model_validate(state.model_dump(mode="json"))
        with pytest.raises(ValueError):
            ExportResumeState.from_dict({**state.to_dict(), "aes_key": "AAAA"})
        with pytest.raises(ValueError):
            ExportResumeState.from_dict({**state.to_dict(), "format_version": 2})
        with pytest.raises(ValueError):
            ExportResumeState.from_dict({**state.to_dict(), "extra": 1})


def _service_with_scheduled_export(flavor: Flavor) -> Any:
    service = flavor.invoices_service()
    handle = ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)

    async def _async_schedule(**_: Any) -> ExportHandle:
        return handle

    def _sync_schedule(**_: Any) -> ExportHandle:
        return handle

    service._schedule_export = _async_schedule if flavor.is_async else _sync_schedule  # pyright: ignore[reportPrivateUsage]
    return service


class TestExportResume:
    def test_a_resumed_job_decrypts_after_a_restart(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        job = flavor.run(_service_with_scheduled_export(flavor).export(filters()))
        saved = job.resume_state().to_json()
        assert "export-ref" in saved

        payload = archive()
        first, second = payload[: len(payload) // 2], payload[len(payload) // 2 :]
        # A fresh service, as after a process restart.
        restarted = flavor.invoices_service()
        resumed = flavor.run(restarted.export(state=saved))
        flavor.transport.enqueue(package_status(inv_export_status_resp, 200, 2))
        flavor.transport.enqueue(content=encrypt_invoice(first, key=KEY, iv=IV))
        flavor.transport.enqueue(content=encrypt_invoice(second, key=KEY, iv=IV))

        exported = flavor.run(resumed.wait(timeout=1.0, poll_interval=0.0))

        assert resumed.reference_number == "export-ref"
        assert resumed.resume_state() == job.resume_state()
        assert list(exported.invoices()) == [(KSEF_1, b"<one />"), (KSEF_2, b"<two />")]

    def test_state_object_is_accepted_too(self, flavor: Flavor) -> None:
        state = ExportResumeState.from_handle(
            ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)
        )

        job = flavor.run(flavor.invoices_service().export(state=state))

        assert job.resume_state() == state
        assert flavor.transport.calls == []

    def test_a_resumed_job_reports_a_failed_export(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        state = ExportResumeState.from_handle(
            ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)
        )
        job = flavor.run(flavor.invoices_service().export(state=state.to_json()))
        flavor.transport.enqueue(package_status(inv_export_status_resp, 415))

        with pytest.raises(KSeFExportFailedError):
            flavor.run(job.wait(timeout=1.0, poll_interval=0.0))

    def test_exactly_one_form_is_allowed(self, flavor: Flavor) -> None:
        service = flavor.invoices_service()
        state = ExportResumeState.from_handle(
            ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)
        )

        with pytest.raises(TypeError, match="either filters"):
            flavor.run(service.export())
        with pytest.raises(TypeError, match="either filters"):
            flavor.run(service.export(filters(), state=state))
        with pytest.raises(TypeError, match="only_metadata"):
            flavor.run(service.export(state=state, only_metadata=True))

    def test_invalid_json_state_raises_a_validation_error(self, flavor: Flavor) -> None:
        with pytest.raises(ValueError):
            flavor.run(flavor.invoices_service().export(state="{}"))
