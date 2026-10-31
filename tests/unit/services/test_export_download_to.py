"""Integrity and cleanup behavior for disk-backed export downloads."""

import asyncio
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ksef2._clients.exported_invoices import ExportedInvoices
from ksef2._core.crypto import encrypt_invoice, sha256_b64
from ksef2._core.exceptions import (
    KSeFArgumentError,
    KSeFEncryptionError,
    KSeFValidationError,
)
from ksef2._domain.models.invoices import (
    ExportHandle,
    ExportResumeState,
    ExportStatusInfo,
    InvoiceExportStatusResponse,
    InvoicePackage,
    PackagePart,
)
from ksef2._services.async_invoices import AsyncExportJob, AsyncInvoicesService
from ksef2._services.invoices import ExportJob, InvoicesService

requires_unchecked_types = pytest.mark.skipif(
    bool(os.environ.get("KSEF2_RUNTIME_CHECKS")),
    reason="beartype rejects the out-of-contract value before the guard runs",
)


KEY, IV = b"k" * 32, b"i" * 16


def _part(ordinal: int, plaintext: bytes, ciphertext: bytes) -> dict[str, object]:
    return {
        "ordinal_number": ordinal,
        "part_name": f"part-{ordinal}.zip.aes",
        "method": "GET",
        "url": "https://storage.invalid/signed-capability",
        "part_size": len(plaintext),
        "part_hash": sha256_b64(plaintext),
        "encrypted_part_size": len(ciphertext),
        "encrypted_part_hash": sha256_b64(ciphertext),
        "expiration_date": datetime(2030, 1, 1, tzinfo=UTC),
    }


def _package(parts: list[dict[str, object]]) -> InvoicePackage:
    return InvoicePackage.model_construct(
        compression_type="zip",
        parts=[PackagePart.model_validate(part) for part in parts],
    )


def _export() -> ExportHandle:
    return ExportHandle.model_construct(
        reference_number="export-ref", aes_key=KEY, iv=IV
    )


def _download(
    is_async: bool, package: InvoicePackage, side_effect: list[object], target: Path
) -> None:
    if is_async:
        async_service = object.__new__(AsyncInvoicesService)
        async_service._external_transfers = Mock()
        async_service._external_transfers.download_part = AsyncMock(
            side_effect=side_effect
        )
        _ = asyncio.run(
            async_service._download_package_to(
                package=package, export=_export(), path=target
            )
        )
        return
    service = object.__new__(InvoicesService)
    service._external_transfers = Mock()
    service._external_transfers.download_part.side_effect = side_effect
    _ = service._download_package_to(package=package, export=_export(), path=target)


def _partials(directory: Path) -> list[str]:
    return sorted(item.name for item in directory.iterdir() if ".partial" in item.name)


def _two_part_package(plaintext: bytes) -> tuple[InvoicePackage, bytes]:
    ciphertext = encrypt_invoice(plaintext, key=KEY, iv=IV)
    package = _package(
        [_part(1, plaintext, ciphertext), _part(2, plaintext, ciphertext)]
    )
    return package, ciphertext


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_disk_download_joins_parts_in_ordinal_order(
    is_async: bool, tmp_path: Path
) -> None:
    # Large enough to cross the 64 KiB decryption chunk boundary.
    chunks = [bytes([n]) * (70 * 1024 + n) for n in range(3)]
    encrypted = [encrypt_invoice(chunk, key=KEY, iv=IV) for chunk in chunks]
    # Parts listed out of order; download must follow ordinal numbers.
    package = _package([_part(n + 1, chunks[n], encrypted[n]) for n in (2, 0, 1)])
    target = tmp_path / "nested" / "export.zip"

    _download(is_async, package, list(encrypted), target)

    assert target.read_bytes() == b"".join(chunks)
    assert _partials(target.parent) == []


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "mismatch", ["plain_hash", "plain_size", "encrypted_hash", "encrypted_size"]
)
def test_disk_download_rejects_part_integrity_mismatch_and_removes_partial(
    mismatch: str, is_async: bool, tmp_path: Path
) -> None:
    plaintext = b"archive part bytes"
    ciphertext = encrypt_invoice(plaintext, key=KEY, iv=IV)
    first_part = _part(1, plaintext, ciphertext)
    second_part = _part(2, plaintext, ciphertext)
    if mismatch == "plain_hash":
        second_part["part_hash"] = sha256_b64(b"wrong")
    elif mismatch == "plain_size":
        second_part["part_size"] = len(plaintext) + 1
    elif mismatch == "encrypted_hash":
        second_part["encrypted_part_hash"] = sha256_b64(b"wrong")
    else:
        second_part["encrypted_part_size"] = len(ciphertext) + 1
    target = tmp_path / "export.zip"
    target.write_bytes(b"previous archive")

    with pytest.raises(KSeFValidationError):
        _download(
            is_async,
            _package([first_part, second_part]),
            [ciphertext, ciphertext],
            target,
        )

    assert target.read_bytes() == b"previous archive"
    assert _partials(tmp_path) == []


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_disk_download_rejects_invalid_padding_and_removes_partial(
    is_async: bool, tmp_path: Path
) -> None:
    # Deterministic: plaintext block ending in 0x00 is never valid PKCS#7.
    encryptor = Cipher(algorithms.AES(KEY), modes.CBC(IV)).encryptor()
    ciphertext = encryptor.update(b"\x00" * 16) + encryptor.finalize()
    part = _part(1, b"", ciphertext)
    target = tmp_path / "export.zip"

    with pytest.raises(KSeFEncryptionError):
        _download(is_async, _package([part]), [ciphertext], target)

    assert not target.exists()
    assert _partials(tmp_path) == []


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_interrupted_download_removes_partial_and_keeps_existing_target(
    is_async: bool, tmp_path: Path
) -> None:
    plaintext = b"archive part bytes"
    ciphertext = encrypt_invoice(plaintext, key=KEY, iv=IV)
    package = _package(
        [_part(1, plaintext, ciphertext), _part(2, plaintext, ciphertext)]
    )
    target = tmp_path / "export.zip"
    target.write_bytes(b"previous archive")

    with pytest.raises(ConnectionError):
        _download(is_async, package, [ciphertext, ConnectionError("reset")], target)

    assert target.read_bytes() == b"previous archive"
    assert _partials(tmp_path) == []


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("fails", [False, True], ids=["success", "failure"])
def test_existing_partial_symlink_is_neither_followed_nor_clobbered(
    is_async: bool, fails: bool, tmp_path: Path
) -> None:
    package, ciphertext = _two_part_package(b"archive part bytes")
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"do not touch")
    target = tmp_path / "export.zip"
    planted = tmp_path / "export.zip.partial"
    planted.symlink_to(victim)
    second: object = ConnectionError("reset") if fails else ciphertext

    if fails:
        with pytest.raises(ConnectionError):
            _download(is_async, package, [ciphertext, second], target)
        assert not target.exists()
    else:
        _download(is_async, package, [ciphertext, second], target)
        assert target.read_bytes() == b"archive part bytes" * 2

    assert victim.read_bytes() == b"do not touch"
    assert planted.is_symlink() and planted.readlink() == victim
    assert _partials(tmp_path) == ["export.zip.partial"]


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_failed_download_leaves_destination_symlink_and_its_file_alone(
    is_async: bool, tmp_path: Path
) -> None:
    package, ciphertext = _two_part_package(b"archive part bytes")
    archive = tmp_path / "kept.zip"
    archive.write_bytes(b"previous archive")
    target = tmp_path / "export.zip"
    target.symlink_to(archive)

    with pytest.raises(KSeFValidationError):
        _download(is_async, package, [ciphertext, b"x" * len(ciphertext)], target)

    assert target.is_symlink() and target.readlink() == archive
    assert archive.read_bytes() == b"previous archive"
    assert _partials(tmp_path) == []


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_successful_download_replaces_destination_symlink_not_its_file(
    is_async: bool, tmp_path: Path
) -> None:
    package, ciphertext = _two_part_package(b"archive part bytes")
    archive = tmp_path / "kept.zip"
    archive.write_bytes(b"previous archive")
    target = tmp_path / "export.zip"
    target.symlink_to(archive)

    _download(is_async, package, [ciphertext, ciphertext], target)

    assert not target.is_symlink()
    assert target.read_bytes() == b"archive part bytes" * 2
    assert archive.read_bytes() == b"previous archive"


def test_concurrent_downloads_in_one_directory_do_not_collide(
    tmp_path: Path,
) -> None:
    contents = {
        "a.zip": b"first archive",
        "b.zip": b"second archive",
        "same.zip": b"third archive",
    }
    seen_partials: list[list[str]] = []

    async def download(target: Path, plaintext: bytes) -> None:
        package, ciphertext = _two_part_package(plaintext)

        async def download_part(**_: object) -> bytes:
            # Yield so the downloads interleave between parts.
            await asyncio.sleep(0)
            seen_partials.append(_partials(tmp_path))
            return ciphertext

        service = object.__new__(AsyncInvoicesService)
        service._external_transfers = Mock()
        service._external_transfers.download_part = download_part
        _ = await service._download_package_to(
            package=package, export=_export(), path=target
        )

    async def main() -> None:
        _ = await asyncio.gather(
            *(download(tmp_path / name, data) for name, data in contents.items()),
            # A second download to the same target gets its own temporary file.
            download(tmp_path / "same.zip", b"third archive"),
        )

    asyncio.run(main())

    assert max(len(names) for names in seen_partials) == 4
    for name, data in contents.items():
        assert (tmp_path / name).read_bytes() == data * 2
    assert _partials(tmp_path) == []


class _CustomPath:
    def __init__(self, value: Path) -> None:
        self._value = value

    def __fspath__(self) -> str:
        return str(self._value)


def _job(is_async: bool, download_to: Mock) -> ExportJob | AsyncExportJob:
    ready = InvoiceExportStatusResponse.model_construct(
        status=ExportStatusInfo.model_construct(code=200, description="ready"),
        package=None,
    )
    state = ExportResumeState.model_construct(
        reference_number="export-ref", aes_key=KEY, iv=IV
    )
    if is_async:
        return AsyncExportJob(
            state,
            get_status=AsyncMock(return_value=ready),
            download_parts=AsyncMock(),
            download_to=AsyncMock(side_effect=download_to),
        )
    return ExportJob(
        state,
        get_status=Mock(return_value=ready),
        download_parts=Mock(),
        download_to=download_to,
    )


def _run_download(job: ExportJob | AsyncExportJob, path: object) -> object:
    if isinstance(job, AsyncExportJob):
        return asyncio.run(job.download(path, poll_interval=0.0))  # pyright: ignore[reportArgumentType]
    return job.download(path, poll_interval=0.0)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("wrap", [Path, _CustomPath], ids=["path", "pathlike"])
def test_job_download_accepts_pathlike_and_passes_a_path(
    is_async: bool, wrap: type, tmp_path: Path
) -> None:
    exported = ExportedInvoices([])
    download_to = Mock(return_value=exported)
    job = _job(is_async, download_to)

    assert _run_download(job, wrap(tmp_path / "export.zip")) is exported

    download_to.assert_called_once_with(None, tmp_path / "export.zip")
    assert type(download_to.call_args.args[1]) is type(tmp_path)


@requires_unchecked_types
@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("value", ["export.zip", b"export.zip", None])
def test_job_download_rejects_non_paths_before_polling(
    is_async: bool, value: object
) -> None:
    download_to = Mock()
    job = _job(is_async, download_to)

    with pytest.raises(KSeFArgumentError, match=r"pass Path\(\.\.\.\)"):
        _ = _run_download(job, value)

    download_to.assert_not_called()


@pytest.mark.parametrize(
    "cancel_at",
    ["download-1", "decrypt-1", "download-2", "decrypt-2", None],
    ids=[
        "first-download",
        "first-decrypt",
        "second-download",
        "second-decrypt",
        "completed",
    ],
)
def test_cancellation_at_each_transfer_boundary_never_leaves_a_mixed_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cancel_at: str | None,
) -> None:
    plaintext = bytes(range(256)) * 1024
    package, ciphertext = _two_part_package(plaintext)
    target = tmp_path / "export.zip"
    target.write_bytes(b"previous archive")
    real_to_thread = asyncio.to_thread

    async def main() -> None:
        reached = asyncio.Event()
        downloads = 0
        decrypts = 0

        async def checkpoint(name: str) -> None:
            if name == cancel_at:
                reached.set()
                await asyncio.Event().wait()

        async def download_part(**_: object) -> bytes:
            nonlocal downloads
            downloads += 1
            await checkpoint(f"download-{downloads}")
            return ciphertext

        async def run_in_thread(
            func: Callable[..., object], /, *args: object, **kwargs: object
        ) -> object:
            nonlocal decrypts
            result = await real_to_thread(func, *args, **kwargs)
            decrypts += 1
            # Keep the service suspended at its thread await after the real
            # decryption has written the part, without racing the scheduler.
            await checkpoint(f"decrypt-{decrypts}")
            return result

        monkeypatch.setattr(asyncio, "to_thread", run_in_thread)
        service = object.__new__(AsyncInvoicesService)
        service._external_transfers = Mock()
        service._external_transfers.download_part = download_part
        task = asyncio.create_task(
            service._download_package_to(package=package, export=_export(), path=target)
        )
        try:
            if cancel_at is None:
                _ = await asyncio.wait_for(task, timeout=10)
                assert target.read_bytes() == plaintext * 2
            else:
                await asyncio.wait_for(reached.wait(), timeout=10)
                _ = task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    _ = await task
                assert target.read_bytes() == b"previous archive"
            assert _partials(tmp_path) == []
        finally:
            if not task.done():
                _ = task.cancel()
                _ = await asyncio.gather(task, return_exceptions=True)

    asyncio.run(main())
