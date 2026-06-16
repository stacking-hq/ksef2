"""Domain models for batch session operations."""

from __future__ import annotations

import base64
from typing import Self

from pydantic import field_validator

from ksef2.domain.models.base import KSeFBaseModel
from ksef2.domain.models.compression import (
    CompressionType,
    normalize_compression_type,
)
from ksef2.domain.models.session import BaseSessionState, FormSchema


class BatchInvoice(KSeFBaseModel):
    """Single invoice payload to include in a batch ZIP."""

    file_name: str
    content: bytes


class BatchInvoiceHash(KSeFBaseModel):
    """Correlation data between a ZIP entry and the original XML hash."""

    file_name: str
    invoice_hash: str


class BatchFilePart(KSeFBaseModel):
    """Information about a part of the batch file."""

    ordinal_number: int
    """Sequential number of the file part (1-indexed)."""

    file_size: int
    """Size of the encrypted file part in bytes."""

    file_hash: str
    """SHA-256 hash of the encrypted file part, Base64 encoded."""


class BatchFileInfo(KSeFBaseModel):
    """Information about the batch file being uploaded."""

    file_size: int
    """Total size of the batch file in bytes. Max 5GB."""

    file_hash: str
    """SHA-256 hash of the batch file, Base64 encoded."""

    compression_type: CompressionType | None = None
    """Compression used for the batch file. Defaults to KSeF's ZIP behavior."""

    parts: list[BatchFilePart]
    """List of file parts. Max 50 parts, each max 100MB before encryption."""

    @field_validator("compression_type", mode="before")
    @classmethod
    def _normalize_compression(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return normalize_compression_type(value)
        return value


class BatchEncryptionData(KSeFBaseModel):
    """Encryption material used for the prepared batch payload."""

    aes_key: str
    iv: str
    encrypted_key: str
    public_key_id: str | None = None

    @classmethod
    def from_bytes(
        cls,
        *,
        aes_key: bytes,
        iv: bytes,
        encrypted_key: bytes,
        public_key_id: str | None = None,
    ) -> Self:
        """Create encoded batch encryption data from raw key bytes."""
        return cls(
            aes_key=base64.b64encode(aes_key).decode(),
            iv=base64.b64encode(iv).decode(),
            encrypted_key=base64.b64encode(encrypted_key).decode(),
            public_key_id=public_key_id,
        )

    def get_aes_key_bytes(self) -> bytes:
        """Return the decoded AES key."""
        return base64.b64decode(self.aes_key)

    def get_iv_bytes(self) -> bytes:
        """Return the decoded initialization vector."""
        return base64.b64decode(self.iv)

    def get_encrypted_key_bytes(self) -> bytes:
        """Return the decoded encrypted symmetric key."""
        return base64.b64decode(self.encrypted_key)


class BatchPreparedPart(KSeFBaseModel):
    """Prepared encrypted batch part ready for upload."""

    ordinal_number: int
    content: bytes
    file_size: int
    file_hash: str


class PreparedBatch(KSeFBaseModel):
    """Prepared batch package with encrypted parts and upload metadata."""

    form_code: FormSchema = FormSchema.FA3
    offline_mode: bool = False
    batch_file: BatchFileInfo
    parts: list[BatchPreparedPart]
    encryption: BatchEncryptionData
    invoices: list[BatchInvoiceHash]


class OpenBatchSessionRequest(KSeFBaseModel):
    """Request to open a batch session."""

    encrypted_key: bytes
    iv: bytes
    public_key_id: str | None = None
    batch_file: BatchFileInfo
    form_code: FormSchema = FormSchema.FA3
    offline_mode: bool = False


class PartUploadRequest(KSeFBaseModel):
    """Upload endpoint information for a batch session part."""

    ordinal_number: int
    """Sequential number of the file part (1-indexed)."""

    method: str
    """HTTP method to use for uploading (typically PUT)."""

    url: str
    """URL to upload the file part to."""

    headers: dict[str, str | None]
    """Headers to include in the upload request."""


class OpenBatchSessionResponse(KSeFBaseModel):
    """Response from opening a batch session."""

    reference_number: str
    """Reference number of the batch session."""

    part_upload_requests: list[PartUploadRequest]
    """Upload instructions for each file part."""


class BatchSessionState(BaseSessionState):
    """Serializable state of a batch session.

    This class holds all information needed to resume a batch session
    or to upload file parts. Can be serialized to JSON for persistence.

    Inherits common session fields from BaseSessionState:
    - reference_number, aes_key, iv, access_token, form_code
    - get_aes_key_bytes(), get_iv_bytes() helper methods
    """

    part_upload_requests: list[PartUploadRequest]
    """Upload instructions for each file part."""

    @classmethod
    def from_encoded(
        cls,
        reference_number: str,
        aes_key: bytes,
        iv: bytes,
        access_token: str,
        form_code: FormSchema,
        part_upload_requests: list[PartUploadRequest],
    ) -> BatchSessionState:
        """Create state from raw bytes (aes_key, iv).

        Args:
            reference_number: Batch session reference number.
            aes_key: Raw AES key bytes.
            iv: Raw initialization vector bytes.
            access_token: Bearer token for authentication.
            form_code: Invoice schema for this session.
            part_upload_requests: Upload instructions for file parts.

        Returns:
            BatchSessionState with Base64-encoded key and IV.
        """
        return cls(
            reference_number=reference_number,
            aes_key=base64.b64encode(aes_key).decode(),
            iv=base64.b64encode(iv).decode(),
            access_token=access_token,
            form_code=form_code,
            part_upload_requests=part_upload_requests,
        )
