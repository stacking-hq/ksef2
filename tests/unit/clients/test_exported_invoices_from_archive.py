"""Restore plain archive bytes through the public export API."""

import io
import stat
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from polyfactory import BaseFactory

from ksef2 import KSeFValidationError
from ksef2.clients import ExportedInvoices
from ksef2.models import CompressionType
from ksef2._infra.schema.api import spec
from tests.unit.clients.test_exported_invoices import _metadata_json, _zip
from tests.unit.clients.test_targz_exported_invoices import _tar


def _archive(entries: dict[str, bytes], compression: CompressionType) -> bytes:
    if compression == "zip":
        return _zip(entries)
    return _tar([(tarfile.TarInfo(name), content) for name, content in entries.items()])


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
def test_restore_archive(
    compression: CompressionType,
    inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    tmp_path: Path,
) -> None:
    metadata, source = _metadata_json(inv_query_metadata_resp)
    payload = _archive(
        {"nested/invoice.xml": b"<invoice />", "_metadata.json": metadata}, compression
    )
    stored = tmp_path / "archive"
    stored.write_bytes(payload)
    with patch.object(
        ExportedInvoices, "_open", side_effect=AssertionError("eager read")
    ):
        restored = ExportedInvoices.from_archive(
            stored.read_bytes(), compression=compression
        )
        assert restored.archive == payload
        assert restored.package is None
    assert list(restored.invoices()) == [("invoice", b"<invoice />")]
    result = restored.metadata
    assert result is not None
    assert [item.ksef_number for item in result] == [item.ksefNumber for item in source]
    with patch.object(
        ExportedInvoices, "_open", side_effect=AssertionError("uncached")
    ):
        assert restored.metadata is result
    target = tmp_path / "out"
    assert set(restored.save(target)) == {
        target / "nested/invoice.xml",
        target / "_metadata.json",
    }
    assert (target / "nested/invoice.xml").read_bytes() == b"<invoice />"
    assert (target / "_metadata.json").read_bytes() == metadata


def test_default_compression_is_zip() -> None:
    restored = ExportedInvoices.from_archive(_zip({"invoice.xml": b"<invoice />"}))
    assert list(restored.invoices()) == [("invoice", b"<invoice />")]


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
@pytest.mark.parametrize("metadata", [None, b'{"invoices": []}'])
def test_absent_and_empty_metadata(
    compression: CompressionType, metadata: bytes | None
) -> None:
    entries = {} if metadata is None else {"_metadata.json": metadata}
    restored = ExportedInvoices.from_archive(
        _archive(entries, compression), compression=compression
    )
    assert restored.metadata == (None if metadata is None else [])
    assert list(restored.invoices()) == []


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
def test_empty_archive(compression: CompressionType, tmp_path: Path) -> None:
    restored = ExportedInvoices.from_archive(b"", compression=compression)
    assert restored.archive == b""
    assert restored.metadata is None
    assert list(restored.invoices()) == []
    assert restored.save(tmp_path / "out") == []
    assert (tmp_path / "out").is_dir()


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
@pytest.mark.parametrize("operation", ["metadata", "invoices", "save"])
def test_invalid_archive_is_rejected_on_access(
    compression: CompressionType, operation: str, tmp_path: Path
) -> None:
    restored = ExportedInvoices.from_archive(
        b"invalid archive", compression=compression
    )
    with pytest.raises((zipfile.BadZipFile, tarfile.TarError)):
        if operation == "metadata":
            _ = restored.metadata
        elif operation == "invoices":
            _ = list(restored.invoices())
        else:
            _ = restored.save(tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
@pytest.mark.parametrize("metadata", [b"not json", b'{"invoices": [{}]}'])
def test_invalid_metadata_stays_lazy(
    compression: CompressionType, metadata: bytes
) -> None:
    restored = ExportedInvoices.from_archive(
        _archive({"invoice.xml": b"<ok />", "_metadata.json": metadata}, compression),
        compression=compression,
    )
    assert list(restored.invoices()) == [("invoice", b"<ok />")]
    with pytest.raises(KSeFValidationError, match="_metadata.json"):
        _ = restored.metadata


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
@pytest.mark.parametrize(
    "name", ["../evil.xml", "/evil.xml", "sub\\evil.xml", "C:/evil.xml"]
)
def test_unsafe_extraction_writes_nothing(
    compression: CompressionType, name: str, tmp_path: Path
) -> None:
    restored = ExportedInvoices.from_archive(
        _archive({"good.xml": b"<ok />", name: b"bad"}, compression),
        compression=compression,
    )
    with pytest.raises(ValueError, match="Unsafe archive entry path"):
        _ = restored.save(tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
def test_existing_symlink_cannot_escape_target(
    compression: CompressionType, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    target = tmp_path / "out"
    target.mkdir()
    (target / "link").symlink_to(outside, target_is_directory=True)
    restored = ExportedInvoices.from_archive(
        _archive({"link/evil.xml": b"bad"}, compression), compression=compression
    )
    with pytest.raises(ValueError, match="Unsafe archive entry path"):
        _ = restored.save(target)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("compression", ["zip", "tar_gz"])
@pytest.mark.parametrize("operation", ["metadata", "invoices", "save"])
def test_archive_links_are_rejected(
    compression: CompressionType, operation: str, tmp_path: Path
) -> None:
    if compression == "zip":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("_metadata.json")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "outside")
        payload = buffer.getvalue()
    else:
        member = tarfile.TarInfo("_metadata.json")
        member.type = tarfile.SYMTYPE
        member.linkname = "outside"
        payload = _tar([(member, b"")])
    restored = ExportedInvoices.from_archive(payload, compression=compression)
    with pytest.raises(ValueError, match="Unsafe archive entry type"):
        if operation == "metadata":
            _ = restored.metadata
        elif operation == "invoices":
            _ = list(restored.invoices())
        else:
            _ = restored.save(tmp_path / "out")
    assert not (tmp_path / "out").exists()
