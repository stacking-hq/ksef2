"""ExportedInvoices: join, unzip, metadata and path-safe ``save()``."""

import io
import json
import zipfile
from pathlib import Path

import pytest
from polyfactory import BaseFactory

from ksef2._clients.exported_invoices import ExportedInvoices
from ksef2._core.exceptions import KSeFValidationError
from ksef2._domain.models.invoices import InvoiceMetadata
from ksef2._infra.schema.api import spec

KSEF_1 = "5265877635-20260101-0100100AB5B5-4B"
KSEF_2 = "5265877635-20260102-0100100AB5B5-5C"


def _zip(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _split(payload: bytes, parts: int) -> list[bytes]:
    size = -(-len(payload) // parts)
    return [payload[i : i + size] for i in range(0, len(payload), size)]


def _metadata_json(
    factory: BaseFactory[spec.QueryInvoicesMetadataResponse],
) -> tuple[bytes, list[spec.InvoiceMetadata]]:
    invoices = factory.build().invoices[:2]
    payload = {"invoices": [item.model_dump(mode="json") for item in invoices]}
    return json.dumps(payload).encode(), invoices


class TestInvoicesAndArchive:
    def test_joins_decrypted_parts_into_one_archive_and_unzips_it(self) -> None:
        archive = _zip({f"{KSEF_1}.xml": b"<one />", f"{KSEF_2}.xml": b"<two />"})
        parts = _split(archive, 3)
        assert len(parts) == 3

        exported = ExportedInvoices(parts)

        assert exported.archive == archive
        assert list(exported.invoices()) == [(KSEF_1, b"<one />"), (KSEF_2, b"<two />")]

    def test_invoices_skips_the_metadata_file_and_directories(self) -> None:
        archive = _zip(
            {
                "_metadata.json": b'{"invoices": []}',
                "nested/": b"",
                f"{KSEF_1}.xml": b"<one />",
            }
        )

        assert list(ExportedInvoices([archive]).invoices()) == [(KSEF_1, b"<one />")]

    def test_empty_export_has_no_invoices_metadata_or_files(
        self, tmp_path: Path
    ) -> None:
        exported = ExportedInvoices([])

        assert exported.archive == b""
        assert list(exported.invoices()) == []
        assert exported.metadata is None
        assert exported.save(tmp_path / "out") == []
        assert (tmp_path / "out").is_dir()


class TestMetadata:
    def test_parses_metadata_json_as_invoice_metadata(
        self, inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse]
    ) -> None:
        payload, source = _metadata_json(inv_query_metadata_resp)
        exported = ExportedInvoices([_zip({"_metadata.json": payload})])

        metadata = exported.metadata

        assert metadata is not None
        assert all(isinstance(item, InvoiceMetadata) for item in metadata)
        assert [item.ksef_number for item in metadata] == [
            item.ksefNumber for item in source
        ]
        assert exported.metadata is metadata

    def test_metadata_is_none_when_the_package_has_no_metadata_file(self) -> None:
        exported = ExportedInvoices([_zip({f"{KSEF_1}.xml": b"<one />"})])

        assert exported.metadata is None

    def test_invalid_metadata_raises_a_validation_error(self) -> None:
        exported = ExportedInvoices([_zip({"_metadata.json": b'{"invoices": [{}]}'})])

        with pytest.raises(KSeFValidationError, match="_metadata.json"):
            _ = exported.metadata

    def test_malformed_metadata_json_raises_a_validation_error(self) -> None:
        exported = ExportedInvoices([_zip({"_metadata.json": b"not json"})])

        with pytest.raises(KSeFValidationError, match="_metadata.json"):
            _ = exported.metadata


class TestSave:
    def test_writes_every_entry_into_the_directory(self, tmp_path: Path) -> None:
        exported = ExportedInvoices(
            [_zip({f"{KSEF_1}.xml": b"<one />", "sub/dir/a.xml": b"<a />"})]
        )

        written = exported.save(tmp_path / "out")

        assert sorted(
            path.relative_to(tmp_path / "out").as_posix() for path in written
        ) == [
            f"{KSEF_1}.xml",
            "sub/dir/a.xml",
        ]
        assert (tmp_path / "out" / f"{KSEF_1}.xml").read_bytes() == b"<one />"
        assert (tmp_path / "out" / "sub" / "dir" / "a.xml").read_bytes() == b"<a />"

    @pytest.mark.parametrize(
        "entry",
        [
            "../evil.xml",
            "a/../../evil.xml",
            "/etc/evil.xml",
            "..\\evil.xml",
            "sub\\evil.xml",
            "C:/evil.xml",
            "c:evil.xml",
        ],
    )
    def test_refuses_unsafe_entry_paths_and_writes_nothing(
        self, entry: str, tmp_path: Path
    ) -> None:
        archive = _zip({f"{KSEF_1}.xml": b"<ok />", entry: b"<evil />"})
        target = tmp_path / "out"

        with pytest.raises(ValueError, match="Unsafe archive entry path"):
            ExportedInvoices([archive]).save(target)

        assert not target.exists()
        assert not (tmp_path / "evil.xml").exists()
        assert not Path("/etc/evil.xml").exists()

    def test_refuses_an_entry_that_resolves_outside_through_a_symlink(
        self, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside"
        outside.mkdir()
        target = tmp_path / "out"
        target.mkdir()
        (target / "link").symlink_to(outside, target_is_directory=True)

        with pytest.raises(ValueError, match="Unsafe archive entry path"):
            ExportedInvoices([_zip({"link/evil.xml": b"<evil />"})]).save(target)

        assert list(outside.iterdir()) == []
