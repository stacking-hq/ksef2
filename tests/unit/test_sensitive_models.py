from dataclasses import asdict
from datetime import UTC, datetime

import pytest
from pydantic import AnyUrl

from ksef2._domain.models.batch import BatchEncryptionData, PartUploadRequest
from ksef2._domain.models.invoices import ExportHandle, PackagePart
from ksef2._domain.models.session import (
    InvoiceStatusInfo,
    SessionEncryptionMaterial,
    SessionInvoiceStatusResponse,
    UpoPage,
)
from ksef2._domain.models.tokens import GenerateTokenResponse


SIGNED_URL = "https://storage.example.test/part?sig=secret-signature"


def test_generated_token_requires_explicit_sensitive_export() -> None:
    response = GenerateTokenResponse(
        reference_number="token-reference",
        token="one-time-secret-token",
    )

    assert response.model_dump() == {"reference_number": "token-reference"}
    assert "one-time-secret-token" not in response.model_dump_json()
    assert "one-time-secret-token" not in repr(response)
    assert response.token == "one-time-secret-token"
    assert response.to_sensitive_dict()["token"] == "one-time-secret-token"


def test_encryption_models_hide_raw_keys_by_default() -> None:
    batch_material = BatchEncryptionData.from_bytes(
        aes_key=b"a" * 32,
        iv=b"i" * 16,
        encrypted_key=b"encrypted-key",
        public_key_id="key-id",
    )
    session_material = SessionEncryptionMaterial(
        aes_key=b"a" * 32,
        iv=b"i" * 16,
        encrypted_key=b"encrypted-key",
        public_key_id="key-id",
    )

    assert batch_material.model_dump() == {"public_key_id": "key-id"}
    assert "YWFhYWFh" not in batch_material.model_dump_json()
    assert batch_material.to_sensitive_dict()["aes_key"] == batch_material.aes_key
    assert "aes_key" not in repr(batch_material)

    assert session_material.model_dump() == {"public_key_id": "key-id"}
    assert "encrypted-key" not in repr(session_material)


def test_export_handle_requires_explicit_sensitive_export() -> None:
    handle = ExportHandle(
        reference_number="export-reference",
        aes_key=b"secret-aes-key",
        iv=b"secret-iv",
    )

    assert handle.model_dump() == {"reference_number": "export-reference"}
    assert "secret-aes-key" not in handle.model_dump_json()
    assert "secret-aes-key" not in repr(handle)
    assert "secret-iv" not in repr(handle)
    assert handle.to_sensitive_dict()["aes_key"] == b"secret-aes-key"
    with pytest.raises(TypeError):
        _ = asdict(handle)


def test_presigned_upload_and_package_urls_require_explicit_sensitive_export() -> None:
    upload = PartUploadRequest(
        ordinal_number=1,
        method="PUT",
        url=SIGNED_URL,
        headers={"x-ms-blob-type": "BlockBlob"},
    )
    package_part = PackagePart(
        ordinal_number=1,
        part_name="part.zip.aes",
        method="GET",
        url=SIGNED_URL,
        part_size=10,
        part_hash="part-hash",
        encrypted_part_size=16,
        encrypted_part_hash="encrypted-hash",
        expiration_date=datetime(2026, 1, 1, tzinfo=UTC),
    )

    for model in (upload, package_part):
        assert "url" not in model.model_dump()
        assert SIGNED_URL not in model.model_dump_json()
        assert SIGNED_URL not in repr(model)
        assert model.to_sensitive_dict()["url"] == SIGNED_URL


def test_presigned_upo_urls_require_explicit_sensitive_export() -> None:
    upo_page = UpoPage(
        reference_number="upo-reference",
        download_url=AnyUrl(SIGNED_URL),
        download_url_expiration_date=datetime(2026, 1, 1, tzinfo=UTC),
    )
    invoice_status = SessionInvoiceStatusResponse(
        ordinal_number=1,
        reference_number="invoice-reference",
        invoice_hash="invoice-hash",
        invoicing_date=datetime(2026, 1, 1, tzinfo=UTC),
        upo_download_url=AnyUrl(SIGNED_URL),
        status=InvoiceStatusInfo(code=200, description="Accepted"),
    )

    assert "download_url" not in upo_page.model_dump()
    assert SIGNED_URL not in upo_page.model_dump_json()
    assert upo_page.to_sensitive_dict()["download_url"] == SIGNED_URL

    assert "upo_download_url" not in invoice_status.model_dump()
    assert SIGNED_URL not in invoice_status.model_dump_json()
    assert invoice_status.to_sensitive_dict()["upo_download_url"] == SIGNED_URL
