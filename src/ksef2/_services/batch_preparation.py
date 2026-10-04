from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from ksef2._core import exceptions
from ksef2._core.crypto import encrypt_invoice, sha256_b64
from ksef2._domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchInvoice,
    BatchInvoiceHash,
    BatchPreparedPart,
    PreparedBatch,
)
from ksef2._domain.models.session import FormSchema

MAX_BATCH_PART_SIZE = 100_000_000


def load_batch_invoices(invoice_paths: Iterable[Path | str]) -> list[BatchInvoice]:
    """Load invoice XML files into batch invoice payloads.

    Raises:
        FileNotFoundError: If any invoice path does not exist.
        OSError: If any invoice path cannot be read.
    """
    return [
        BatchInvoice(file_name=Path(path).name, content=Path(path).read_bytes())
        for path in invoice_paths
    ]


def load_batch_items(
    items: Iterable[bytes | str | Path | BatchInvoice],
) -> list[BatchInvoice]:
    """Turn mixed invoice inputs into batch invoice payloads.

    Args:
        items: Invoices to include. ``bytes`` and ``str`` are invoice XML and get the
            file name ``invoice-<position>.xml``; a ``Path`` is read from disk and
            keeps its file name; a ``BatchInvoice`` is used as is.

    Returns:
        One batch invoice payload per item, in order.

    Raises:
        KSeFValidationError: If a single invoice is passed instead of a list.
        FileNotFoundError: If a path does not exist.
        OSError: If a path cannot be read.
    """
    if isinstance(items, bytes | str | Path | BatchInvoice):
        raise exceptions.KSeFValidationError(
            "Pass the invoices as a list, for example [xml], not a single invoice."
        )
    invoices: list[BatchInvoice] = []
    for position, item in enumerate(items, start=1):
        if isinstance(item, BatchInvoice):
            invoices.append(item)
        elif isinstance(item, Path):
            invoices.append(
                BatchInvoice(file_name=item.name, content=item.read_bytes())
            )
        else:
            content = item.encode("utf-8") if isinstance(item, str) else item
            invoices.append(
                BatchInvoice(file_name=f"invoice-{position}.xml", content=content)
            )
    return invoices


def prepare_batch_package(
    *,
    invoices: Iterable[BatchInvoice],
    aes_key: bytes,
    iv: bytes,
    encrypted_key: bytes,
    public_key_id: str | None = None,
    form_code: FormSchema = FormSchema.FA3,
    offline_mode: bool = False,
    max_part_size: int = MAX_BATCH_PART_SIZE,
) -> PreparedBatch:
    """Build, split, and encrypt a batch package from invoice payloads.

    Args:
        invoices: Invoices to include; each becomes one ZIP entry.
        aes_key: AES-256 key used to encrypt the parts.
        iv: AES initialization vector.
        encrypted_key: ``aes_key`` encrypted with the KSeF public key.
        public_key_id: Identifier of the KSeF public key used for ``encrypted_key``; ``None`` for the default.
        form_code: Invoice schema of the batch.
        offline_mode: Whether the invoices were issued in offline mode.
        max_part_size: Maximum size in bytes of one encrypted part.

    Returns:
        The prepared batch: package metadata, encrypted parts and encryption material.

    Raises:
        KSeFEncryptionError: If part encryption fails.
        KSeFValidationError: If the invoice list or part size is invalid.
    """
    normalized = list(invoices)
    validate_invoices(normalized)
    validate_max_part_size(max_part_size)

    zip_bytes = build_zip(normalized)
    raw_parts = split_bytes(zip_bytes, max_part_size=max_part_size)

    prepared_parts: list[BatchPreparedPart] = []
    declared_parts: list[BatchFilePart] = []

    for ordinal_number, raw_part in enumerate(raw_parts, start=1):
        encrypted_part = encrypt_batch_part(payload=raw_part, aes_key=aes_key, iv=iv)
        part_hash = sha256_b64(encrypted_part)
        prepared_parts.append(
            BatchPreparedPart(
                ordinal_number=ordinal_number,
                content=encrypted_part,
                file_size=len(encrypted_part),
                file_hash=part_hash,
            )
        )
        declared_parts.append(
            BatchFilePart(
                ordinal_number=ordinal_number,
                file_size=len(encrypted_part),
                file_hash=part_hash,
            )
        )

    return PreparedBatch(
        form_code=form_code,
        offline_mode=offline_mode,
        batch_file=BatchFileInfo(
            file_size=len(zip_bytes),
            file_hash=sha256_b64(zip_bytes),
            compression_type="zip",
            parts=declared_parts,
        ),
        parts=prepared_parts,
        encryption=BatchEncryptionData.from_bytes(
            aes_key=aes_key,
            iv=iv,
            encrypted_key=encrypted_key,
            public_key_id=public_key_id,
        ),
        invoices=[
            BatchInvoiceHash(
                file_name=invoice.file_name,
                invoice_hash=sha256_b64(invoice.content),
            )
            for invoice in normalized
        ],
    )


def validate_invoices(invoices: list[BatchInvoice]) -> None:
    """Validate invoice payloads before creating the ZIP package.

    Raises:
        KSeFValidationError: If no invoices are provided or names are empty or
            duplicated.
    """
    if not invoices:
        raise exceptions.KSeFValidationError(
            "At least one invoice is required to build a batch package."
        )

    file_names = [invoice.file_name for invoice in invoices]
    if any(not name for name in file_names):
        raise exceptions.KSeFValidationError(
            "Every batch invoice must define a non-empty file name."
        )

    if len(file_names) != len(set(file_names)):
        raise exceptions.KSeFValidationError(
            "Batch invoice file names must be unique.",
            duplicate_file_names=sorted(
                {name for name in file_names if file_names.count(name) > 1}
            ),
        )


def validate_max_part_size(max_part_size: int) -> None:
    """Validate the batch part size limit.

    Raises:
        KSeFValidationError: If ``max_part_size`` is outside KSeF limits.
    """
    if max_part_size < 1 or max_part_size > MAX_BATCH_PART_SIZE:
        raise exceptions.KSeFValidationError(
            "max_part_size must be between 1 and 100000000 bytes.",
            max_part_size=max_part_size,
        )


def build_zip(invoices: list[BatchInvoice]) -> bytes:
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        for invoice in invoices:
            archive.writestr(invoice.file_name, invoice.content)
    return zip_buffer.getvalue()


def split_bytes(payload: bytes, *, max_part_size: int) -> list[bytes]:
    return [
        payload[offset : offset + max_part_size]
        for offset in range(0, len(payload), max_part_size)
    ]


def encrypt_batch_part(*, payload: bytes, aes_key: bytes, iv: bytes) -> bytes:
    """Encrypt a single batch part.

    Raises:
        KSeFEncryptionError: If AES-CBC encryption fails.
    """
    return encrypt_invoice(payload, key=aes_key, iv=iv)
