import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import final
from collections.abc import Iterator

_KNOWN_NON_INVOICE_FILES = frozenset(
    {
        "manifest.xml",
        "metadata.xml",
        "signature.xml",
    }
)


@dataclass(frozen=True, slots=True)
class PackageInvoice:
    name: str
    xml: bytes


@final
class PackageReader:
    def __init__(self, zip_parts: list[bytes] | bytes) -> None:
        if isinstance(zip_parts, bytes):
            zip_parts = [zip_parts]
        self._parts = zip_parts

    def __iter__(self) -> Iterator[PackageInvoice]:
        return self.invoices()

    def invoices(self) -> Iterator[PackageInvoice]:
        for part in self._parts:
            with zipfile.ZipFile(io.BytesIO(part), "r") as zf:
                for entry in zf.namelist():
                    if not entry.lower().endswith(".xml"):
                        continue
                    if PurePosixPath(entry).name.lower() in _KNOWN_NON_INVOICE_FILES:
                        continue
                    yield PackageInvoice(name=entry, xml=zf.read(entry))
