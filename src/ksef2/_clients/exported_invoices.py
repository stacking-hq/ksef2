"""Decrypted invoice export, ready to read or save."""

import io
import json
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import cast, final

from ksef2._core import exceptions
from ksef2._domain.models.invoices import InvoiceMetadata, InvoicePackage
from ksef2._infra.mappers.invoices import from_spec
from ksef2._infra.schema.api import spec

METADATA_FILE_NAME = "_metadata.json"
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


@final
class ExportedInvoices:
    """Decrypted result of an invoice export.

    The decrypted package parts are joined into one ZIP archive, which holds one
    ``<ksef_number>.xml`` file per invoice and a ``_metadata.json`` file. The ZIP is
    opened lazily; construct this object through ``ExportJob.wait()``. An export that
    matched no invoices has an empty archive.
    """

    def __init__(
        self,
        parts: list[bytes],
        *,
        package: InvoicePackage | None = None,
    ) -> None:
        """Create the export result.

        Args:
            parts: Decrypted package parts in ordinal order; concatenated they form the ZIP archive.
            package: Package metadata from the export status, if known.
        """
        self._archive = b"".join(parts)
        self._package = package
        self._metadata: list[InvoiceMetadata] | None = None
        self._metadata_loaded = False

    @property
    def archive(self) -> bytes:
        """Get the raw ZIP archive.

        Returns:
            The decrypted and joined package parts, exactly as KSeF built the archive.
        """
        return self._archive

    @property
    def package(self) -> InvoicePackage | None:
        """Get the package metadata reported by the export status.

        Returns:
            Invoice count, size, truncation flag and the dates for continuing a truncated export; ``None`` if unknown.
        """
        return self._package

    @property
    def metadata(self) -> list[InvoiceMetadata] | None:
        """Get the invoice metadata stored in the package.

        Returns:
            The parsed ``invoices`` list of ``_metadata.json``, or ``None`` if the package has no such file.

        Raises:
            KSeFValidationError: If ``_metadata.json`` is not valid metadata.
            zipfile.BadZipFile: If the archive is not a valid ZIP file.
        """
        if not self._metadata_loaded:
            self._metadata = self._read_metadata()
            self._metadata_loaded = True
        return self._metadata

    def invoices(self) -> Iterator[tuple[str, bytes]]:
        """Iterate over the invoices in the package.

        Yields:
            A ``(ksef_number, xml)`` pair for each invoice file, in archive order.

        Raises:
            zipfile.BadZipFile: If the archive is not a valid ZIP file.
        """
        if not self._archive:
            return
        with self._open() as archive:
            for info in archive.infolist():
                name = PurePosixPath(info.filename)
                if info.is_dir() or name.suffix.lower() != ".xml":
                    continue
                if name.name.startswith("_"):
                    continue
                yield name.stem, archive.read(info)

    def save(self, directory: Path | str) -> list[Path]:
        """Extract the package into a directory.

        Every entry path is validated first, and nothing is written if one is
        unsafe: absolute paths, ``..`` segments, backslashes, drive letters and NUL
        bytes are refused.

        Args:
            directory: Directory to extract into; created if missing.

        Returns:
            The paths of the written files.

        Raises:
            ValueError: If an archive entry path would escape ``directory``.
            zipfile.BadZipFile: If the archive is not a valid ZIP file.
            OSError: If a file or directory cannot be written.
        """
        root = Path(directory)
        if not self._archive:
            root.mkdir(parents=True, exist_ok=True)
            return []
        with self._open() as archive:
            targets: list[tuple[zipfile.ZipInfo, Path]] = []
            resolved_root = root.resolve()
            for info in archive.infolist():
                _reject_unsafe_entry(info.filename)
                target = root.joinpath(*PurePosixPath(info.filename).parts)
                if not target.resolve().is_relative_to(resolved_root):
                    raise ValueError(f"Unsafe archive entry path: {info.filename!r}")
                targets.append((info, target))

            root.mkdir(parents=True, exist_ok=True)
            written: list[Path] = []
            for info, target in targets:
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                _ = target.write_bytes(archive.read(info))
                written.append(target)
        return written

    def _open(self) -> zipfile.ZipFile:
        return zipfile.ZipFile(io.BytesIO(self._archive), "r")

    def _read_metadata(self) -> list[InvoiceMetadata] | None:
        if not self._archive:
            return None
        with self._open() as archive:
            for info in archive.infolist():
                if PurePosixPath(info.filename).name != METADATA_FILE_NAME:
                    continue
                try:
                    payload = cast(
                        dict[str, list[object]], json.loads(archive.read(info))
                    )
                    return [
                        from_spec(spec.InvoiceMetadata.model_validate(item))
                        for item in payload["invoices"]
                    ]
                except (ValueError, KeyError, TypeError) as exc:
                    raise exceptions.KSeFValidationError(
                        f"Export package has an invalid {METADATA_FILE_NAME}: {exc}"
                    ) from exc
        return None


def _reject_unsafe_entry(name: str) -> None:
    if (
        not name
        or "\x00" in name
        or "\\" in name
        or name.startswith("/")
        or _DRIVE_RE.match(name)
        or ".." in PurePosixPath(name).parts
    ):
        raise ValueError(f"Unsafe archive entry path: {name!r}")
