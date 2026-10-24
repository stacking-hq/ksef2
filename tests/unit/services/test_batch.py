import base64
import json
from collections.abc import Callable
from io import BytesIO
from zipfile import ZipFile

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._clients.batch import BatchSessionClient
from ksef2._core.crypto import decrypt_aes_cbc, sha256_b64
from ksef2._core.exceptions import (
    KSeFBatchUploadError,
    KSeFBatchSessionTimeoutError,
    KSeFSessionError,
    KSeFSessionFailedError,
    KSeFValidationError,
)
from ksef2.models import AuthTokens
from ksef2._domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchInvoice,
    BatchPreparedPart,
    BatchSessionResumeState,
    PartUploadRequest,
    PreparedBatch,
)
from ksef2._domain.models.session import FormSchema, SessionEncryptionMaterial
from ksef2._infra.schema.api import spec
from ksef2._services.batch import BatchService, BatchSessionOpener
from tests.unit.fakes.transport import FakeTransport
from tests.unit.support.flavors import Flavor
from tests.unit.support.helpers import VALID_PUBLIC_KEY_ID, legacy_api


def _build_service(
    fake_transport: FakeTransport,
    *,
    open_batch_session: BatchSessionOpener,
    get_encryption_key: Callable[[], SessionEncryptionMaterial] | None = None,
) -> BatchService:
    return BatchService(
        authed_transport=fake_transport,
        upload_transport=fake_transport,
        get_encryption_key=get_encryption_key
        or (
            lambda: SessionEncryptionMaterial(
                aes_key=b"k" * 32,
                iv=b"v" * 16,
                encrypted_key=b"enc-key",
                public_key_id=VALID_PUBLIC_KEY_ID,
            )
        ),
        open_batch_session=open_batch_session,
    )


def _unused_open_batch_session(
    *,
    batch_file: BatchFileInfo,
    aes_key: bytes,
    iv: bytes,
    encrypted_key: bytes,
    public_key_id: str | None = None,
    form_code: FormSchema = FormSchema.FA3,
    offline_mode: bool = False,
    prepared_batch: PreparedBatch | None = None,
) -> BatchSessionClient:
    del (
        batch_file,
        aes_key,
        iv,
        encrypted_key,
        public_key_id,
        form_code,
        offline_mode,
        prepared_batch,
    )
    raise AssertionError("not used")


@pytest.fixture
def prepared_batch(fake_transport: FakeTransport) -> PreparedBatch:
    return _build_service(
        fake_transport, open_batch_session=_unused_open_batch_session
    ).prepare([b"<Invoice>1</Invoice>", b"<Invoice>2</Invoice>"], offline_mode=True)


def test_prepared_batch_sensitive_export_round_trips(
    prepared_batch: PreparedBatch,
) -> None:
    envelope = prepared_batch.to_sensitive_dict()
    assert set(envelope) == {"version", "payload"}
    assert type(envelope["version"]) is str
    assert envelope["version"] == "1"
    assert json.loads(prepared_batch.to_sensitive_json()) == envelope
    restored_batches = [
        PreparedBatch.from_sensitive_json(prepared_batch.to_sensitive_json()),
        PreparedBatch.from_sensitive_json(prepared_batch.to_sensitive_json(indent=2)),
        PreparedBatch.from_sensitive_dict(prepared_batch.to_sensitive_dict()),
    ]
    for restored in restored_batches:
        assert restored == prepared_batch
        assert restored.recovery_digest() == prepared_batch.recovery_digest()


@pytest.mark.parametrize(
    ("content", "encoded"),
    [(b"\xfb", "-w=="), (b"\xfb\xff", "-_8="), (b"\xfb\xff\xff", "-___")],
)
def test_prepared_batch_sensitive_export_is_url_safe_base64(
    prepared_batch: PreparedBatch, content: bytes, encoded: str
) -> None:
    part = BatchPreparedPart(
        ordinal_number=1,
        content=content,
        file_size=len(content),
        file_hash=sha256_b64(content),
    )
    prepared_batch.parts = [part]
    exported = json.loads(prepared_batch.to_sensitive_json())
    assert exported["payload"]["parts"][0]["content"] == encoded
    assert (
        base64.urlsafe_b64decode(exported["payload"]["parts"][0]["content"]) == content
    )
    assert part.content == content
    assert PreparedBatch.from_sensitive_dict(exported).parts[0].content == content


def test_prepared_batch_generic_dump_still_hides_payload_and_keys(
    prepared_batch: PreparedBatch,
) -> None:
    assert "parts" not in prepared_batch.model_dump()
    assert "encryption" not in prepared_batch.model_dump()
    assert "content" not in prepared_batch.parts[0].model_dump()
    assert prepared_batch.encryption.model_dump() == {
        "public_key_id": VALID_PUBLIC_KEY_ID
    }
    secrets = [
        prepared_batch.encryption.aes_key,
        prepared_batch.encryption.iv,
        prepared_batch.encryption.encrypted_key,
    ]
    for part in prepared_batch.parts:
        secrets.extend(
            [repr(part.content), base64.urlsafe_b64encode(part.content).decode()]
        )
    for model in [prepared_batch, *prepared_batch.parts, prepared_batch.encryption]:
        for output in [str(model.model_dump()), model.model_dump_json(), repr(model)]:
            assert all(secret not in output for secret in secrets)


def test_restored_prepared_batch_resumes_its_session(
    prepared_batch: PreparedBatch,
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    auth = flavor.authenticated(domain_auth_tokens.build())
    upload_url = "https://storage.example/upload?sig=secret"
    flavor.transport.enqueue(
        status_code=201,
        json_body={
            "referenceNumber": "B" * 36,
            "partUploadRequests": [
                {"ordinalNumber": 1, "method": "PUT", "url": upload_url, "headers": {}}
            ],
        },
    )
    session = flavor.run(auth.batch_session(prepared_batch=prepared_batch))
    flavor.transport.enqueue_error(
        httpx.ConnectTimeout(
            "local storage failure", request=httpx.Request("PUT", upload_url)
        )
    )
    with pytest.raises(KSeFBatchUploadError) as caught:
        flavor.run(session.upload_parts())
    saved_state = caught.value.recovery_state().to_json()
    restored = PreparedBatch.from_sensitive_json(
        caught.value.recovery_prepared_batch().to_sensitive_json()
    )
    resumed = flavor.run(auth.batch_session(state=saved_state, prepared_batch=restored))
    assert resumed.reference_number == session.reference_number
    flavor.transport.enqueue(status_code=201, json_body={})
    flavor.run(resumed.upload_parts())
    assert [
        call.content for call in flavor.transport.calls if call.method == "PUT"
    ] == [
        prepared_batch.parts[0].content,
        prepared_batch.parts[0].content,
    ]

    changed = restored.model_copy(deep=True)
    changed.parts[0].content += b"changed"
    changed = PreparedBatch.from_sensitive_json(changed.to_sensitive_json())
    calls_before = len(flavor.transport.calls)
    with pytest.raises(KSeFValidationError, match="original prepared batch"):
        flavor.run(auth.batch_session(state=saved_state, prepared_batch=changed))
    assert len(flavor.transport.calls) == calls_before


@pytest.mark.parametrize("version", [1, "1", "1.2", "1.0.1"])
def test_prepared_batch_reads_supported_versions(
    prepared_batch: PreparedBatch, version: object
) -> None:
    exported = prepared_batch.to_sensitive_dict()
    exported["version"] = version

    restored = PreparedBatch.from_sensitive_json(json.dumps(exported))

    assert restored.recovery_digest() == prepared_batch.recovery_digest()


@pytest.mark.parametrize(
    "version", [None, 0, 2, "2", True, 1.0, "1.", "v1", "01", "", "secret-version"]
)
def test_prepared_batch_rejects_unsupported_versions(
    prepared_batch: PreparedBatch,
    version: object,
) -> None:
    exported = prepared_batch.to_sensitive_dict()
    exported["version"] = version
    for reader in [
        lambda: PreparedBatch.from_sensitive_dict(exported),
        lambda: PreparedBatch.from_sensitive_json(json.dumps(exported)),
    ]:
        with pytest.raises(
            ValueError, match="Unsupported prepared batch persistence version"
        ) as caught:
            reader()
        assert "secret-version" not in repr(caught.value)
        assert caught.value.__context__ is None
        assert caught.value.__cause__ is None
    with pytest.raises(ValueError, match="Unsupported"):
        PreparedBatch.from_sensitive_dict(prepared_batch.model_dump())


@pytest.mark.parametrize(
    "corruption", ["key", "part", "extra", "nested_extra", "envelope", "raw_bytes"]
)
def test_prepared_batch_invalid_persistence_hides_values(
    prepared_batch: PreparedBatch,
    corruption: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exported = json.loads(prepared_batch.to_sensitive_json())
    secret = "DO-NOT-EXPOSE-STORED-SECRET"
    if corruption == "key":
        exported["payload"]["encryption"]["aes_key"] = secret
    elif corruption == "part":
        exported["payload"]["parts"][0]["content"] = secret + "!"
    elif corruption == "extra":
        exported["payload"][secret] = secret
    elif corruption == "nested_extra":
        exported["payload"]["encryption"][secret] = secret
    elif corruption == "envelope":
        exported[secret] = secret
    else:
        exported["payload"]["parts"][0]["content"] = secret.encode()
    with pytest.raises(
        ValueError, match="Invalid prepared batch persistence payload"
    ) as caught:
        PreparedBatch.from_sensitive_dict(exported)
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    captured = capsys.readouterr()
    assert secret not in captured.out + captured.err


@pytest.mark.parametrize(
    "stored", ["not-json-secret", '"secret"', "[]", "null", b"\xffsecret"]
)
def test_prepared_batch_malformed_json_is_safe(stored: str | bytes) -> None:
    with pytest.raises(
        ValueError, match="Invalid prepared batch persistence envelope"
    ) as caught:
        PreparedBatch.from_sensitive_json(stored)
    assert "secret" not in repr(caught.value)
    assert caught.value.__context__ is None


class TestBatchService:
    @legacy_api
    def test_prepare_batch_builds_zip_metadata_and_encrypted_part(
        self,
        fake_transport: FakeTransport,
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=_unused_open_batch_session,
        )
        invoices = [
            BatchInvoice(file_name="invoice-1.xml", content=b"<Invoice>1</Invoice>"),
            BatchInvoice(file_name="invoice-2.xml", content=b"<Invoice>2</Invoice>"),
        ]

        prepared = service.prepare_batch(invoices=invoices, form_code=FormSchema.FA3)

        assert prepared.form_code is FormSchema.FA3
        assert len(prepared.parts) == 1
        assert prepared.batch_file.compression_type == "zip"
        assert prepared.invoices[0].invoice_hash == sha256_b64(invoices[0].content)
        assert prepared.invoices[1].invoice_hash == sha256_b64(invoices[1].content)
        assert prepared.encryption.public_key_id == VALID_PUBLIC_KEY_ID

        decrypted_zip = decrypt_aes_cbc(
            prepared.parts[0].content,
            key=prepared.encryption.get_aes_key_bytes(),
            iv=prepared.encryption.get_iv_bytes(),
        )
        with ZipFile(BytesIO(decrypted_zip)) as archive:
            assert sorted(archive.namelist()) == ["invoice-1.xml", "invoice-2.xml"]
            assert archive.read("invoice-1.xml") == b"<Invoice>1</Invoice>"
            assert archive.read("invoice-2.xml") == b"<Invoice>2</Invoice>"

        assert prepared.batch_file.file_size == len(decrypted_zip)
        assert prepared.batch_file.file_hash == sha256_b64(decrypted_zip)
        assert prepared.batch_file.parts[0].file_size == len(prepared.parts[0].content)
        assert prepared.batch_file.parts[0].file_hash == sha256_b64(
            prepared.parts[0].content
        )

    @legacy_api
    def test_prepare_batch_rejects_duplicate_file_names(
        self,
        fake_transport: FakeTransport,
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=_unused_open_batch_session,
        )

        with pytest.raises(KSeFValidationError, match="must be unique"):
            _ = service.prepare_batch(
                invoices=[
                    BatchInvoice(file_name="invoice.xml", content=b"1"),
                    BatchInvoice(file_name="invoice.xml", content=b"2"),
                ]
            )

    def test_upload_parts_uses_presigned_urls_without_auth_header(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=_unused_open_batch_session,
        )
        state = domain_batch_session_state.build(
            part_upload_requests=[
                PartUploadRequest(
                    ordinal_number=1,
                    method="PUT",
                    url="https://example.com/upload/part-1",
                    headers={"x-ms-blob-type": "BlockBlob"},
                )
            ]
        )
        session = BatchSessionClient(fake_transport, state)
        prepared_batch = PreparedBatch(
            batch_file=BatchFileInfo(
                file_size=10,
                file_hash=sha256_b64(b"plaintext"),
                parts=[
                    BatchFilePart(
                        ordinal_number=1,
                        file_size=12,
                        file_hash=sha256_b64(b"encrypted"),
                    )
                ],
            ),
            parts=[
                BatchPreparedPart(
                    ordinal_number=1,
                    content=b"encrypted",
                    file_size=len(b"encrypted"),
                    file_hash=sha256_b64(b"encrypted"),
                )
            ],
            encryption=BatchEncryptionData.from_bytes(
                aes_key=b"k" * 32,
                iv=b"v" * 16,
                encrypted_key=b"enc-key",
            ),
            invoices=[],
        )
        fake_transport.enqueue(status_code=201, json_body={})

        service.upload_parts(session=session, prepared_batch=prepared_batch)

        assert fake_transport.calls[0].method == "PUT"
        assert fake_transport.calls[0].path == "https://example.com/upload/part-1"
        assert fake_transport.calls[0].headers == {
            "Content-Type": "application/octet-stream",
            "x-ms-blob-type": "BlockBlob",
        }

    @legacy_api
    def test_submit_prepared_batch_uploads_parts_and_closes_session(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build(
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

        def _open_batch_session(
            *,
            batch_file: BatchFileInfo,
            aes_key: bytes,
            iv: bytes,
            encrypted_key: bytes,
            public_key_id: str | None = None,
            form_code: FormSchema = FormSchema.FA3,
            offline_mode: bool = False,
            prepared_batch: PreparedBatch | None = None,
        ) -> BatchSessionClient:
            del (
                batch_file,
                aes_key,
                iv,
                encrypted_key,
                public_key_id,
                form_code,
                offline_mode,
            )
            return BatchSessionClient(
                fake_transport,
                state,
                prepared_batch=prepared_batch,
            )

        service = _build_service(
            fake_transport,
            open_batch_session=_open_batch_session,
        )
        prepared_batch = PreparedBatch(
            batch_file=BatchFileInfo(
                file_size=10,
                file_hash=sha256_b64(b"plaintext"),
                parts=[
                    BatchFilePart(
                        ordinal_number=1,
                        file_size=12,
                        file_hash=sha256_b64(b"encrypted"),
                    )
                ],
            ),
            parts=[
                BatchPreparedPart(
                    ordinal_number=1,
                    content=b"encrypted",
                    file_size=len(b"encrypted"),
                    file_hash=sha256_b64(b"encrypted"),
                )
            ],
            encryption=BatchEncryptionData.from_bytes(
                aes_key=b"k" * 32,
                iv=b"v" * 16,
                encrypted_key=b"enc-key",
            ),
            invoices=[],
        )
        fake_transport.enqueue(status_code=201, json_body={})
        fake_transport.enqueue(json_body={})

        result = service.submit_prepared_batch(prepared_batch=prepared_batch)

        assert result.reference_number == "batch-ref"
        assert fake_transport.calls[0].method == "PUT"
        assert fake_transport.calls[1].method == "POST"

    @legacy_api
    def test_wait_for_completion_returns_terminal_success(
        self,
        fake_transport: FakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=_unused_open_batch_session,
        )
        fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=100, description="In progress"),
            ).model_dump(mode="json")
        )
        fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=200, description="Processed"),
            ).model_dump(mode="json")
        )

        status = service.wait_for_completion(
            session="batch-ref",
            timeout=1.0,
            poll_interval=0.0,
        )

        assert status.status.code == 200
        assert len(fake_transport.calls) == 2

    @legacy_api
    def test_wait_for_completion_raises_on_terminal_failure(
        self,
        fake_transport: FakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=_unused_open_batch_session,
        )
        fake_transport.enqueue(
            inv_session_status_resp.build(
                status=spec.StatusInfo(code=450, description="Rejected"),
            ).model_dump(mode="json")
        )

        with pytest.raises(KSeFSessionFailedError, match="Rejected") as exc_info:
            _ = service.wait_for_completion(
                session="batch-ref",
                timeout=1.0,
                poll_interval=0.0,
            )

        error = exc_info.value
        assert isinstance(error, KSeFSessionError)
        assert error.reference_number == "batch-ref"
        assert error.session_status_code == 450
        assert error.context["description"] == "Rejected"

    @legacy_api
    def test_wait_for_completion_raises_on_timeout(
        self,
        fake_transport: FakeTransport,
        inv_session_status_resp: BaseFactory[spec.SessionStatusResponse],
    ) -> None:
        service = _build_service(
            fake_transport,
            open_batch_session=_unused_open_batch_session,
        )
        for _ in range(3):
            fake_transport.enqueue(
                inv_session_status_resp.build(
                    status=spec.StatusInfo(code=100, description="In progress"),
                ).model_dump(mode="json")
            )

        with pytest.raises(KSeFBatchSessionTimeoutError, match="not ready"):
            _ = service.wait_for_completion(
                session="batch-ref",
                timeout=0.0,
                poll_interval=0.0,
            )
