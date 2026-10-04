"""prepare / submit on the batch service, sync and async."""

import io
import zipfile
from pathlib import Path
from typing import Any

import pytest
from polyfactory import BaseFactory

from ksef2._core.crypto import decrypt_aes_cbc
from ksef2._core.exceptions import KSeFValidationError
from ksef2._core.routes import SessionRoutes
from ksef2._domain.models.batch import (
    BatchInvoice,
    BatchSessionResumeState,
    PartUploadRequest,
    PreparedBatch,
)
from ksef2._domain.models.session import SessionEncryptionMaterial
from ksef2._infra.schema.api import spec
from tests.unit.flavors import Flavor
from tests.unit.helpers import VALID_PUBLIC_KEY_ID

KEY = b"k" * 32
IV = b"v" * 16


def _material() -> SessionEncryptionMaterial:
    return SessionEncryptionMaterial(
        aes_key=KEY,
        iv=IV,
        encrypted_key=b"enc-key",
        public_key_id=VALID_PUBLIC_KEY_ID,
    )


def _service(flavor: Flavor, opener: Any = None) -> Any:
    def _unused(**_: Any) -> Any:
        raise AssertionError("not used")

    if flavor.is_async:

        async def _async_material() -> SessionEncryptionMaterial:
            return _material()

        return flavor.batch_service(
            get_encryption_key=_async_material,
            open_batch_session=opener or _unused,
        )
    return flavor.batch_service(
        get_encryption_key=_material, open_batch_session=opener or _unused
    )


def _entries(prepared: PreparedBatch) -> dict[str, bytes]:
    archive = b"".join(
        decrypt_aes_cbc(part.content, key=KEY, iv=IV) for part in prepared.parts
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


class TestPrepare:
    def test_accepts_bytes_str_path_and_batch_invoice(
        self, flavor: Flavor, tmp_path: Path
    ) -> None:
        file = tmp_path / "from-disk.xml"
        file.write_bytes(b"<disk />")
        service = _service(flavor)

        prepared = flavor.run(
            service.prepare(
                [
                    b"<bytes />",
                    "<text>zażółć</text>",
                    file,
                    BatchInvoice(file_name="explicit.xml", content=b"<explicit />"),
                ]
            )
        )

        assert _entries(prepared) == {
            "invoice-1.xml": b"<bytes />",
            "invoice-2.xml": "<text>zażółć</text>".encode(),
            "from-disk.xml": b"<disk />",
            "explicit.xml": b"<explicit />",
        }

    def test_rejects_a_single_xml_string_instead_of_a_list(
        self, flavor: Flavor
    ) -> None:
        # A bare str would otherwise be iterated into one "invoice" per character.
        with pytest.raises(KSeFValidationError, match="as a list"):
            flavor.run(_service(flavor).prepare("<one />"))

    def test_rejects_an_empty_batch(self, flavor: Flavor) -> None:
        with pytest.raises(KSeFValidationError):
            flavor.run(_service(flavor).prepare([]))

    def test_rejects_a_missing_file(self, flavor: Flavor, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            flavor.run(_service(flavor).prepare([tmp_path / "missing.xml"]))

    def test_passes_form_code_and_offline_mode(self, flavor: Flavor) -> None:
        prepared = flavor.run(_service(flavor).prepare([b"<one />"], offline_mode=True))

        assert prepared.offline_mode is True


class TestSubmit:
    def _opener(
        self,
        flavor: Flavor,
        state: BatchSessionResumeState,
        opened: list[PreparedBatch],
    ) -> Any:
        def _open(*, prepared_batch: PreparedBatch | None = None, **_: Any) -> Any:
            assert prepared_batch is not None
            opened.append(prepared_batch)
            return flavor.batch_session(state, prepared_batch=prepared_batch)

        if flavor.is_async:

            async def _async_open(**kwargs: Any) -> Any:
                return _open(**kwargs)

            return _async_open
        return _open

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
                    headers={"x-ms-blob-type": "BlockBlob"},
                )
            ],
        )

    def test_submit_invoices_opens_uploads_closes_and_returns_the_session(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        opened: list[PreparedBatch] = []
        service = _service(
            flavor,
            self._opener(flavor, self._state(domain_batch_session_state), opened),
        )
        flavor.transport.enqueue(status_code=201, json_body={})
        flavor.transport.enqueue(json_body={})
        flavor.transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=200, description="done"), upo=None
            ).model_dump(mode="json")
        )

        session = flavor.run(service.submit([b"<one />", b"<two />"]))

        assert len(opened) == 1
        assert _entries(opened[0]).keys() == {"invoice-1.xml", "invoice-2.xml"}
        upload, close = flavor.transport.calls[:2]
        assert (upload.method, upload.path) == (
            "PUT",
            "https://example.com/upload/part-1",
        )
        assert close.path == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber="batch-ref"
        )
        assert session.reference_number == "batch-ref"
        # The returned session is closed, so wait() is allowed straight away.
        assert (
            flavor.run(session.wait(timeout=1.0, poll_interval=0.0)).status.code == 200
        )

    def test_submit_accepts_a_prepared_batch(
        self,
        flavor: Flavor,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        opened: list[PreparedBatch] = []
        service = _service(
            flavor,
            self._opener(flavor, self._state(domain_batch_session_state), opened),
        )
        prepared = flavor.run(service.prepare([b"<one />"]))
        flavor.transport.enqueue(status_code=201, json_body={})
        flavor.transport.enqueue(json_body={})

        flavor.run(service.submit(prepared))

        assert opened == [prepared]
