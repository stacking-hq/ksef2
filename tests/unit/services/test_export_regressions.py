"""Public export regressions shared by the sync and async services."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from ksef2._clients.exported_invoices import ExportedInvoices
from ksef2._core.crypto import encrypt_invoice, sha256_b64
from ksef2._core.exceptions import KSeFValidationError
from ksef2._domain.models.invoices import (
    ExportHandle,
    ExportResumeState,
    InvoicePackage,
    InvoicesFilter,
)
from tests.unit.support.flavors import Flavor
from tests.unit.support.helpers import legacy_api

KEY, IV = b"k" * 32, b"i" * 16


def _handle() -> ExportHandle:
    return ExportHandle(reference_number="export-ref", aes_key=KEY, iv=IV)


def _empty_package() -> dict[str, object]:
    return {"invoiceCount": 0, "size": 0, "parts": [], "isTruncated": False}


def _ready(flavor: Flavor, package: dict[str, object]) -> None:
    flavor.transport.enqueue(
        {"status": {"code": 200, "description": "Completed"}, "package": package}
    )


@legacy_api
@pytest.mark.parametrize(
    "method", ["wait_for_export_package", "export_and_download", "wait", "download"]
)
def test_empty_export_finishes_on_first_status_without_sleeping(
    flavor: Flavor, method: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = flavor.invoices_service()
    _ready(flavor, _empty_package())
    # A completed export must return even when there is no time left to retry.
    if method == "wait_for_export_package":
        result = flavor.run(
            service.wait_for_export_package(reference_number="export-ref", timeout=0.0)
        )
        assert isinstance(result, InvoicePackage)
        assert result.invoice_count == 0
        assert result.parts == []
    elif method == "export_and_download":
        schedule = (
            AsyncMock(return_value=_handle())
            if flavor.is_async
            else Mock(return_value=_handle())
        )
        monkeypatch.setattr(service, "_schedule_export", schedule)
        result = flavor.run(
            service.export_and_download(
                filters=InvoicesFilter.for_seller(
                    date_from="2026-01-01T00:00:00Z", date_to="2026-01-02T00:00:00Z"
                ),
                timeout=0.0,
            )
        )
        assert result == []
    else:
        job = flavor.run(service.export(state=ExportResumeState.from_handle(_handle())))
        if method == "download":
            target = tmp_path / "empty.zip"
            result = flavor.run(job.download(target, timeout=0.0))
            assert target.read_bytes() == b""
        else:
            result = flavor.run(job.wait(timeout=0.0))
        assert isinstance(result, ExportedInvoices)
        assert result.archive == b""
        assert result.metadata == []
        assert list(result.invoices()) == []
    assert len(flavor.transport.calls) == 1
    assert flavor.transport.responses == []


@pytest.mark.parametrize("destination", ["memory", "disk", "legacy"])
@pytest.mark.parametrize(
    "mismatch",
    ["part_size", "part_hash", "encrypted_part_hash", "encrypted_part_size", None],
)
@legacy_api
def test_export_download_verifies_each_part(
    flavor: Flavor, destination: str, mismatch: str | None, tmp_path: Path
) -> None:
    plaintext = b"deterministic archive part"
    ciphertext = encrypt_invoice(plaintext, key=KEY, iv=IV)
    part: dict[str, object] = {
        "ordinalNumber": 1,
        "partName": "part-1.zip.aes",
        "method": "GET",
        "url": "https://storage.invalid/part-1",
        "partSize": len(plaintext),
        "partHash": sha256_b64(plaintext),
        "encryptedPartSize": len(ciphertext),
        "encryptedPartHash": sha256_b64(ciphertext),
        "expirationDate": datetime(2030, 1, 1, tzinfo=UTC).isoformat(),
    }
    if mismatch == "part_size":
        part["partSize"] = len(plaintext) + 1
    elif mismatch == "part_hash":
        part["partHash"] = sha256_b64(b"wrong plaintext")
    elif mismatch == "encrypted_part_hash":
        part["encryptedPartHash"] = sha256_b64(b"wrong ciphertext")
    elif mismatch == "encrypted_part_size":
        part["encryptedPartSize"] = len(ciphertext) + 1
    package: dict[str, object] = {
        "invoiceCount": 1,
        "size": len(plaintext),
        "parts": [part],
        "isTruncated": False,
    }
    service = flavor.invoices_service()
    _ready(flavor, package)
    flavor.transport.enqueue(content=ciphertext)
    job = flavor.run(service.export(state=ExportResumeState.from_handle(_handle())))
    target = tmp_path / "export.zip"
    target.write_bytes(b"previous archive")

    def download() -> bytes:
        if destination == "legacy":
            ready_package = flavor.run(
                service.wait_for_export_package(
                    reference_number="export-ref", timeout=0.0
                )
            )
            return b"".join(
                flavor.run(
                    service.fetch_package_bytes(package=ready_package, export=_handle())
                )
            )
        result = flavor.run(
            job.download(target, timeout=0.0)
            if destination == "disk"
            else job.wait(timeout=0.0)
        )
        assert isinstance(result, ExportedInvoices)
        return result.archive

    if mismatch is None:
        assert download() == plaintext
    else:
        label = "encrypted" if mismatch.startswith("encrypted") else "plaintext"
        with pytest.raises(
            KSeFValidationError,
            match=f"Export package part {label} size or hash mismatch",
        ):
            download()
        assert target.read_bytes() == b"previous archive"
        assert sorted(item.name for item in tmp_path.iterdir()) == ["export.zip"]
    assert len(flavor.transport.calls) == 2
    assert flavor.transport.responses == []


@legacy_api
@pytest.mark.parametrize("code", [210, 415, 500])
def test_legacy_export_wait_raises_sdk_failure(flavor: Flavor, code: int) -> None:
    from ksef2 import KSeFExportFailedError

    flavor.transport.enqueue(
        {"status": {"code": code, "description": "Failed", "details": ["reason"]}}
    )
    with pytest.raises(KSeFExportFailedError) as caught:
        flavor.run(
            flavor.invoices_service().wait_for_export_package(
                reference_number="export-ref", timeout=1.0, poll_interval=0.0
            )
        )
    assert caught.value.reference_number == "export-ref"
    assert caught.value.export_status_code == code


@legacy_api
def test_legacy_completed_export_requires_package(flavor: Flavor) -> None:
    from ksef2 import KSeFResponseValidationError

    flavor.transport.enqueue({"status": {"code": 200, "description": "Completed"}})
    with pytest.raises(KSeFResponseValidationError, match="no package"):
        flavor.run(
            flavor.invoices_service().wait_for_export_package(
                reference_number="export-ref", timeout=1.0, poll_interval=0.0
            )
        )
