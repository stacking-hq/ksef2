from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from ksef2.core import exceptions
from ksef2.core.crypto import encrypt_invoice, sha256_b64
from ksef2.domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchInvoice,
    BatchInvoiceHash,
    BatchPreparedPart,
    PreparedBatch,
)
from ksef2.domain.models.session import FormSchema

MAX_BATCH_PART_SIZE = 100_000_000


def load_batch_invoices(invoice_paths: Iterable[Path | str]) -> list[BatchInvoice]:
    return [
        BatchInvoice(file_name=Path(path).name, content=Path(path).read_bytes())
        for path in invoice_paths
    ]


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
    return encrypt_invoice(payload, key=aes_key, iv=iv)
