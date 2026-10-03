"""Deprecated invoice-workflow aliases warn exactly once and still work (sync and async)."""

import inspect
import os
import warnings
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from polyfactory import BaseFactory

from ksef2._clients.async_authenticated import AsyncAuthenticatedClient
from ksef2._clients.authenticated import AuthenticatedClient
from ksef2._core.exceptions import KSeFInvoiceRejectedError
from ksef2._core.stores import CertificateStore
from ksef2._domain.models.auth import AuthTokens
from ksef2._domain.models.batch import (
    BatchFileInfo,
    BatchInvoice,
    BatchSessionResumeState,
    PartUploadRequest,
)
from ksef2._domain.models.invoices import (
    ExportHandle,
    InvoicePackage,
    InvoicesFilter,
)
from ksef2._domain.models.session import (
    OnlineSessionResumeState,
    SessionEncryptionMaterial,
)
from ksef2._infra.schema.api import spec
from tests.unit.flavors import Flavor
from tests.unit.helpers import VALID_PUBLIC_KEY_ID
from tests.unit.payloads import (
    INVOICE_REF,
    KSEF_NUMBER,
    UPO_REFS,
    archive,
    invoice_status,
    metadata_page,
    package_status,
    session_status,
)

SUFFIX = "will be removed in ksef2 1.10.0; use `{new}` instead."
KEY = b"k" * 32
IV = b"v" * 16


def _once(flavor: Flavor, call: Callable[[], Any], old: str, new: str) -> Any:
    """Call, drain, and assert exactly one DeprecationWarning with the 1.10.0 message."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = call()
        if inspect.isgenerator(value) or inspect.isasyncgen(value):
            result = flavor.collect(value)
        else:
            result = flavor.run(value)
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecations) == 1, [str(w.message) for w in deprecations]
    message = str(deprecations[0].message)
    assert message.startswith(f"`{old}` is deprecated and ")
    assert message.endswith(SUFFIX.format(new=new))
    if not os.environ.get("KSEF2_RUNTIME_CHECKS"):
        assert deprecations[0].filename == __file__
    return result


def _filters() -> InvoicesFilter:
    return InvoicesFilter(
        role="seller",
        date_type="issue_date",
        date_from=datetime(2026, 1, 1, tzinfo=UTC),
        date_to=datetime(2026, 2, 1, tzinfo=UTC),
    )


class TestOnlineSessionAliases:
    def test_send_invoice_and_wait(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_send_resp: BaseFactory[spec.SendInvoiceResponse],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(
            inv_send_resp.build(referenceNumber=INVOICE_REF).model_dump(mode="json")
        )
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 200, KSEF_NUMBER)
        )

        status = _once(
            flavor,
            lambda: session.send_invoice_and_wait(
                invoice_xml=b"<xml />", timeout=1.0, poll_interval=0.0
            ),
            "send_invoice_and_wait()",
            "send_invoice().wait()",
        )

        assert status.ksef_number == KSEF_NUMBER

    def test_wait_for_invoice_ready(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 200, KSEF_NUMBER)
        )

        status = _once(
            flavor,
            lambda: session.wait_for_invoice_ready(
                invoice_reference_number=INVOICE_REF, timeout=1.0, poll_interval=0.0
            ),
            "wait_for_invoice_ready()",
            "send_invoice().wait()",
        )

        assert status.ksef_number == KSEF_NUMBER

    def test_wait_for_invoice_ready_still_raises_on_rejection(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
        inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(
            invoice_status(inv_session_invoice_status_resp, 450, None)
        )

        with pytest.raises(KSeFInvoiceRejectedError):
            _once(
                flavor,
                lambda: session.wait_for_invoice_ready(
                    invoice_reference_number=INVOICE_REF, timeout=1.0, poll_interval=0.0
                ),
                "wait_for_invoice_ready()",
                "send_invoice().wait()",
            )

    def test_get_invoice_upo_by_ksef_number(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(content=b"<upo />")

        result = _once(
            flavor,
            lambda: session.get_invoice_upo_by_ksef_number(ksef_number=KSEF_NUMBER),
            "get_invoice_upo_by_ksef_number()",
            "download_invoice_upo(ksef_number=...)",
        )

        assert result == b"<upo />"

    def test_get_invoice_upo_by_reference(
        self,
        flavor: Flavor,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        session = flavor.online_session(domain_online_session_state.build())
        flavor.transport.enqueue(content=b"<upo />")

        result = _once(
            flavor,
            lambda: session.get_invoice_upo_by_reference(
                invoice_reference_number=INVOICE_REF
            ),
            "get_invoice_upo_by_reference()",
            "download_invoice_upo(reference_number=...)",
        )

        assert result == b"<upo />"


class TestBatchSessionAliases:
    def test_get_upo(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        session = flavor.batch_session(domain_batch_session_state.build())
        flavor.transport.enqueue(content=b"<upo />")

        result = _once(
            flavor,
            lambda: session.get_upo(upo_reference_number=UPO_REFS[0]),
            "get_upo()",
            "download_upo()",
        )

        assert result == b"<upo />"


class TestBatchServiceAliases:
    def _service(self, flavor: Flavor, state: BatchSessionResumeState | None = None):
        def _material() -> SessionEncryptionMaterial:
            return SessionEncryptionMaterial(
                aes_key=KEY,
                iv=IV,
                encrypted_key=b"enc-key",
                public_key_id=VALID_PUBLIC_KEY_ID,
            )

        async def _async_material() -> SessionEncryptionMaterial:
            return _material()

        def _open(*, prepared_batch: Any = None, **_: Any) -> Any:
            assert state is not None
            return flavor.batch_session(state, prepared_batch=prepared_batch)

        async def _async_open(**kwargs: Any) -> Any:
            return _open(**kwargs)

        return flavor.batch_service(
            get_encryption_key=_async_material if flavor.is_async else _material,
            open_batch_session=_async_open if flavor.is_async else _open,
        )

    def _state(
        self, factory: BaseFactory[BatchSessionResumeState]
    ) -> BatchSessionResumeState:
        return factory.build(
            reference_number="batch-ref",
            part_upload_requests=[
                PartUploadRequest(
                    ordinal_number=1,
                    method="PUT",
                    url="https://example.com/upload/part-1",
                    headers={},
                )
            ],
        )

    def test_prepare_batch(self, flavor: Flavor) -> None:
        service = self._service(flavor)

        prepared = _once(
            flavor,
            lambda: service.prepare_batch(
                invoices=[BatchInvoice(file_name="a.xml", content=b"<a />")]
            ),
            "prepare_batch()",
            "prepare()",
        )

        assert [item.file_name for item in prepared.invoices] == ["a.xml"]

    def test_prepare_batch_from_paths(self, flavor: Flavor, tmp_path: Path) -> None:
        file = tmp_path / "a.xml"
        file.write_bytes(b"<a />")
        service = self._service(flavor)

        prepared = _once(
            flavor,
            lambda: service.prepare_batch_from_paths(invoice_paths=[file]),
            "prepare_batch_from_paths()",
            "prepare()",
        )

        assert [item.file_name for item in prepared.invoices] == ["a.xml"]

    def test_submit_batch(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = self._state(domain_batch_session_state)
        service = self._service(flavor, state)
        flavor.transport.enqueue(status_code=201, json_body={})
        flavor.transport.enqueue(json_body={})

        result = _once(
            flavor,
            lambda: service.submit_batch(
                invoices=[BatchInvoice(file_name="a.xml", content=b"<a />")]
            ),
            "submit_batch()",
            "submit()",
        )

        assert result == state

    def test_submit_prepared_batch(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = self._state(domain_batch_session_state)
        service = self._service(flavor, state)
        prepared = flavor.run(service.prepare([b"<a />"]))
        flavor.transport.enqueue(status_code=201, json_body={})
        flavor.transport.enqueue(json_body={})

        result = _once(
            flavor,
            lambda: service.submit_prepared_batch(prepared_batch=prepared),
            "submit_prepared_batch()",
            "submit()",
        )

        assert result == state

    def test_open_session(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = self._state(domain_batch_session_state)
        service = self._service(flavor, state)
        prepared = flavor.run(service.prepare([b"<a />"]))

        session = _once(
            flavor,
            lambda: service.open_session(prepared_batch=prepared),
            "open_session()",
            "auth.batch_session()",
        )

        assert session.reference_number == "batch-ref"

    def test_get_status(
        self,
        flavor: Flavor,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = self._service(flavor)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 200))

        status = _once(
            flavor,
            lambda: service.get_status(session="batch-ref"),
            "get_status()",
            "BatchSessionClient.get_status()",
        )

        assert status.status.code == 200

    def test_list_invoices(
        self,
        flavor: Flavor,
        inv_session_invoices_resp: BaseFactory[spec.SessionInvoicesResponse],
    ) -> None:
        service = self._service(flavor)
        flavor.transport.enqueue(
            inv_session_invoices_resp.build(
                continuationToken=None, invoices=[]
            ).model_dump(mode="json")
        )

        page = _once(
            flavor,
            lambda: service.list_invoices(session="batch-ref"),
            "list_invoices()",
            "BatchSessionClient.list_invoices()",
        )

        assert page.invoices == []

    def test_list_failed_invoices(
        self,
        flavor: Flavor,
        inv_session_invoices_resp: BaseFactory[spec.SessionInvoicesResponse],
    ) -> None:
        service = self._service(flavor)
        flavor.transport.enqueue(
            inv_session_invoices_resp.build(
                continuationToken=None, invoices=[]
            ).model_dump(mode="json")
        )

        page = _once(
            flavor,
            lambda: service.list_failed_invoices(session="batch-ref"),
            "list_failed_invoices()",
            "BatchSessionClient.list_failed_invoices()",
        )

        assert page.invoices == []

    def test_get_upo(self, flavor: Flavor) -> None:
        service = self._service(flavor)
        flavor.transport.enqueue(content=b"<upo />")

        result = _once(
            flavor,
            lambda: service.get_upo(session="batch-ref", upo_reference_number="u"),
            "get_upo()",
            "BatchSessionClient.download_upo()",
        )

        assert result == b"<upo />"

    def test_wait_for_completion(
        self,
        flavor: Flavor,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = self._service(flavor)
        flavor.transport.enqueue(session_status(inv_session_status_resp, 200))

        status = _once(
            flavor,
            lambda: service.wait_for_completion(
                session="batch-ref", timeout=1.0, poll_interval=0.0
            ),
            "wait_for_completion()",
            "BatchSessionClient.wait()",
        )

        assert status.status.code == 200


class TestAuthenticatedClientAliases:
    def test_open_batch_session(
        self,
        flavor: Flavor,
        domain_auth_tokens: BaseFactory[AuthTokens],
        domain_batch_file_info: BaseFactory[BatchFileInfo],
        session_open_batch_resp: BaseFactory[spec.OpenBatchSessionResponse],
    ) -> None:
        flavor.transport.enqueue(
            session_open_batch_resp.build().model_dump(mode="json")
        )
        cls = AsyncAuthenticatedClient if flavor.is_async else AuthenticatedClient
        client = cls(
            transport=flavor.transport,  # pyright: ignore[reportArgumentType]
            auth_tokens=domain_auth_tokens.build(),
            certificate_store=CertificateStore(),
        )

        session = _once(
            flavor,
            lambda: client.open_batch_session(
                batch_file=domain_batch_file_info.build(),
                aes_key=KEY,
                iv=IV,
                encrypted_key=b"enc-key",
                public_key_id=VALID_PUBLIC_KEY_ID,
            ),
            "open_batch_session()",
            "raw",
        )

        assert session.aes_key == KEY
        assert session.iv == IV


class TestInvoicesServiceAliases:
    def test_query_metadata(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=2, has_more=False)
        )

        page = _once(
            flavor,
            lambda: service.query_metadata(filters=_filters()),
            "query_metadata()",
            "search()",
        )

        assert len(page.invoices) == 2

    def test_query_metadata_pages(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=2, has_more=False)
        )

        pages = _once(
            flavor,
            lambda: service.query_metadata_pages(filters=_filters()),
            "query_metadata_pages()",
            "search()",
        )

        assert [len(page.invoices) for page in pages] == [2]

    def test_all_metadata(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=2, has_more=False)
        )

        items = _once(
            flavor,
            lambda: service.all_metadata(filters=_filters()),
            "all_metadata()",
            "search()",
        )

        assert len(items) == 2

    def test_wait_for_invoices(
        self,
        flavor: Flavor,
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(
            metadata_page(inv_query_metadata_resp, count=1, has_more=False)
        )

        page = _once(
            flavor,
            lambda: service.wait_for_invoices(
                filters=_filters(), timeout=1.0, poll_interval=0.0
            ),
            "wait_for_invoices()",
            "search().wait()",
        )

        assert len(page.invoices) == 1

    def test_download_invoice(self, flavor: Flavor) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(content=b"<Invoice />")

        xml = _once(
            flavor,
            lambda: service.download_invoice(ksef_number=KSEF_NUMBER),
            "download_invoice()",
            "download()",
        )

        assert xml == b"<Invoice />"

    def test_wait_for_invoice_download(self, flavor: Flavor) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(content=b"<Invoice />")

        xml = _once(
            flavor,
            lambda: service.wait_for_invoice_download(
                ksef_number=KSEF_NUMBER, timeout=1.0, poll_interval=0.0
            ),
            "wait_for_invoice_download()",
            "download()",
        )

        assert xml == b"<Invoice />"

    def test_get_export_status(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(package_status(inv_export_status_resp, 100))

        status = _once(
            flavor,
            lambda: service.get_export_status(reference_number="export-ref"),
            "get_export_status()",
            "export()",
        )

        assert status.status.code == 100

    def test_wait_for_export_package(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        service = flavor.invoices_service()
        flavor.transport.enqueue(package_status(inv_export_status_resp, 200, 1))

        package = _once(
            flavor,
            lambda: service.wait_for_export_package(
                reference_number="export-ref", timeout=1.0, poll_interval=0.0
            ),
            "wait_for_export_package()",
            "export().wait()",
        )

        assert isinstance(package, InvoicePackage)
        assert len(package.parts) == 1

    def _package(
        self, factory: BaseFactory[spec.InvoiceExportStatusResponse], parts: int
    ) -> InvoicePackage:
        raw = package_status(factory, 200, parts)["package"]
        return InvoicePackage.model_validate(
            {
                "invoice_count": raw["invoiceCount"],
                "size": raw["size"],
                "is_truncated": False,
                "parts": [
                    {
                        "ordinal_number": part["ordinalNumber"],
                        "part_name": part["partName"],
                        "method": "GET",
                        "url": f"https://example.com/export/part-{part['ordinalNumber']}",
                        "part_size": 1,
                        "part_hash": "x",
                        "encrypted_part_size": 1,
                        "encrypted_part_hash": "x",
                        "expiration_date": datetime(2030, 1, 1, tzinfo=UTC),
                    }
                    for part in raw["parts"]
                ],
            }
        )

    def test_fetch_package_bytes(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        from ksef2._core.crypto import encrypt_invoice

        service = flavor.invoices_service()
        handle = ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)
        flavor.transport.enqueue(content=encrypt_invoice(b"part-1", key=KEY, iv=IV))

        parts = _once(
            flavor,
            lambda: service.fetch_package_bytes(
                package=self._package(inv_export_status_resp, 1), export=handle
            ),
            "fetch_package_bytes()",
            "export().wait()",
        )

        assert parts == [b"part-1"]

    def test_fetch_package(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
        tmp_path: Path,
    ) -> None:
        from ksef2._core.crypto import encrypt_invoice

        service = flavor.invoices_service()
        handle = ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)
        flavor.transport.enqueue(content=encrypt_invoice(b"part-1", key=KEY, iv=IV))

        written = _once(
            flavor,
            lambda: service.fetch_package(
                package=self._package(inv_export_status_resp, 1),
                export=handle,
                target_directory=tmp_path,
            ),
            "fetch_package()",
            "export().wait()",
        )

        assert [path.read_bytes() for path in written] == [b"part-1"]

    def test_schedule_export_and_export_and_download(
        self,
        flavor: Flavor,
        inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse],
    ) -> None:
        from unittest.mock import patch

        from ksef2._core.crypto import encrypt_invoice

        service = flavor.invoices_service()
        handle = ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)

        async def _async_schedule(**_: Any) -> ExportHandle:
            return handle

        def _sync_schedule(**_: Any) -> ExportHandle:
            return handle

        with patch.object(
            service,
            "_schedule_export",
            _async_schedule if flavor.is_async else _sync_schedule,
        ):
            scheduled = _once(
                flavor,
                lambda: service.schedule_export(filters=_filters()),
                "schedule_export()",
                "export()",
            )
            flavor.transport.enqueue(package_status(inv_export_status_resp, 200, 1))
            flavor.transport.enqueue(content=encrypt_invoice(archive(), key=KEY, iv=IV))
            parts = _once(
                flavor,
                lambda: service.export_and_download(
                    filters=_filters(), timeout=1.0, poll_interval=0.0
                ),
                "export_and_download()",
                "export().wait()",
            )

        assert scheduled == handle
        assert b"".join(parts) == archive()
