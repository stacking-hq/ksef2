"""TarGz reading and safe extraction through the public result API."""

import io
import stat
import tarfile
import zipfile
from pathlib import Path

import pytest
from polyfactory import BaseFactory

from ksef2 import KSeFValidationError
from ksef2.clients import ExportedInvoices
from ksef2.models import InvoicePackage
from ksef2._infra.schema.api import spec
from tests.unit.clients.test_exported_invoices import _metadata_json


def _tar(entries: list[tuple[tarfile.TarInfo, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for member, content in entries:
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return buffer.getvalue()


def _package(payload: bytes) -> ExportedInvoices:
    return ExportedInvoices(
        [payload],
        package=InvoicePackage(
            invoice_count=1,
            size=len(payload),
            parts=[],
            is_truncated=False,
            compression_type="tar_gz",
        ),
    )


def test_targz_metadata_and_invoice_selection(
    inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    tmp_path: Path,
) -> None:
    metadata, source = _metadata_json(inv_query_metadata_resp)
    directory = tarfile.TarInfo("nested")
    directory.type = tarfile.DIRTYPE
    payload = _tar(
        [
            (directory, b""),
            (tarfile.TarInfo("nested/invoice.XML"), b"<invoice />"),
            (tarfile.TarInfo("_private.xml"), b"<private />"),
            (tarfile.TarInfo("nested/_metadata.json"), metadata),
        ]
    )
    exported = _package(payload)
    assert list(exported.invoices()) == [("invoice", b"<invoice />")]
    result = exported.metadata
    assert result is not None
    assert [item.ksef_number for item in result] == [item.ksefNumber for item in source]
    assert exported.metadata is result
    assert len(exported.save(tmp_path / "out")) == 3
    assert (tmp_path / "out/nested/invoice.XML").read_bytes() == b"<invoice />"


@pytest.mark.parametrize(
    "name",
    [
        "../evil.xml",
        "a/../../evil.xml",
        "/evil.xml",
        "sub\\evil.xml",
        "C:/evil.xml",
        "c:evil.xml",
    ],
)
def test_targz_rejects_traversal_before_writing(name: str, tmp_path: Path) -> None:
    payload = _tar(
        [(tarfile.TarInfo("good.xml"), b"<ok />"), (tarfile.TarInfo(name), b"bad")]
    )
    with pytest.raises(ValueError, match="Unsafe archive entry path"):
        _ = _package(payload).save(tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "entry_type",
    [
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
        tarfile.FIFOTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
    ],
)
@pytest.mark.parametrize("operation", ["invoices", "metadata", "save"])
def test_targz_rejects_links_and_special_files(
    entry_type: bytes, operation: str, tmp_path: Path
) -> None:
    member = tarfile.TarInfo(
        "evil.xml" if operation != "metadata" else "_metadata.json"
    )
    member.type = entry_type
    member.linkname = "good.xml"
    exported = _package(_tar([(tarfile.TarInfo("good.xml"), b"<ok />"), (member, b"")]))
    with pytest.raises(ValueError, match="Unsafe archive entry type"):
        if operation == "invoices":
            _ = list(exported.invoices())
        elif operation == "metadata":
            _ = exported.metadata
        else:
            _ = exported.save(tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_targz_rejects_existing_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "out"
    root.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="Unsafe archive entry path"):
        _ = _package(_tar([(tarfile.TarInfo("link/evil.xml"), b"bad")])).save(root)
    assert list(outside.iterdir()) == []


def test_zip_rejects_symlinks_before_writing(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    member = zipfile.ZipInfo("link.xml")
    member.create_system = 3
    member.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("good.xml", b"<ok />")
        archive.writestr(member, b"../outside")
    with pytest.raises(ValueError, match="Unsafe archive entry type"):
        _ = ExportedInvoices([buffer.getvalue()]).save(tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("metadata", [b"not json", b'{"invoices": [{}]}'])
def test_targz_invalid_metadata_preserves_cause(metadata: bytes) -> None:
    with pytest.raises(KSeFValidationError, match="_metadata.json") as error:
        _ = _package(_tar([(tarfile.TarInfo("_metadata.json"), metadata)])).metadata
    assert error.value.__cause__ is not None


def test_invalid_targz_reports_archive_error() -> None:
    with pytest.raises(tarfile.ReadError):
        _ = list(_package(b"invalid tar.gz").invoices())
