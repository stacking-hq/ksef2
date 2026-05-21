"""Supplementary models for batch session operations.

These models shadow the spec models with str instead of Base64Str fields
to allow easier construction in mappers.
"""

from typing import Annotated

from pydantic import Field

from ksef2.infra.schema.api.supp.base import BaseSupp
from ksef2.infra.schema.api.supp.session import EncryptionInfo
from ksef2.infra.schema.api.spec.models import CompressionType, FormCode


class BatchFilePartInfo(BaseSupp):
    """Information about a part of the batch file."""

    ordinalNumber: Annotated[int, Field(ge=1)]
    """Sequential number of the file part."""

    fileSize: Annotated[int, Field(ge=1)]
    """Size of the encrypted file part in bytes."""

    fileHash: str
    """SHA-256 hash of the encrypted file part, Base64 encoded."""


class BatchFileInfo(BaseSupp):
    """Information about the batch file being uploaded."""

    fileSize: Annotated[int, Field(ge=1, le=5000000000)]
    """Total size of the batch file in bytes. Max 5GB."""

    fileHash: str
    """SHA-256 hash of the batch file, Base64 encoded."""

    compressionType: CompressionType | None = None
    """Compression type for the batch file."""

    fileParts: Annotated[list[BatchFilePartInfo], Field(max_length=50, min_length=1)]
    """List of file parts. Max 50 parts."""


class OpenBatchSessionRequest(BaseSupp):
    """Request to open a batch session for sending invoices in bulk."""

    formCode: FormCode
    """Invoice schema to use (FA2, FA3, etc.)."""

    batchFile: BatchFileInfo
    """Information about the batch file."""

    encryption: EncryptionInfo
    """Encryption information for the batch file."""

    offlineMode: bool = False
    """Whether offline invoicing mode is declared."""
