"""Domain models for batch session operations."""

import base64
import warnings
from typing import TYPE_CHECKING, Literal, Self, override

from pydantic import Field, SecretStr, field_validator

from ksef2.domain.models.base import KSeFBaseModel
from ksef2.domain.models.compression import (
    CompressionType,
    normalize_compression_type,
)
from ksef2.domain.models.session import BaseSessionResumeState, FormSchema


MAX_BATCH_FILE_SIZE_BYTES = 5_000_000_000
MAX_BATCH_FILE_PARTS = 50
MAX_BATCH_PART_PRE_ENCRYPTION_SIZE_BYTES = 100_000_000
MAX_AES_CBC_PADDING_BYTES = 16
# The API's 100MB part limit is pre-encryption; this model stores encrypted bytes.
MAX_BATCH_ENCRYPTED_PART_SIZE_BYTES = (
    MAX_BATCH_PART_PRE_ENCRYPTION_SIZE_BYTES + MAX_AES_CBC_PADDING_BYTES
)


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

    ordinal_number: int = Field(ge=1)
    """Sequential number of the file part (1-indexed)."""

    file_size: int = Field(ge=0, le=MAX_BATCH_ENCRYPTED_PART_SIZE_BYTES)
    """Size of the encrypted file part in bytes."""

    file_hash: str
    """SHA-256 hash of the encrypted file part, Base64 encoded."""


class BatchFileInfo(KSeFBaseModel):
    """Information about the batch file being uploaded."""

    file_size: int = Field(ge=0, le=MAX_BATCH_FILE_SIZE_BYTES)
    """Total size of the batch file in bytes. Max 5GB."""

    file_hash: str
    """SHA-256 hash of the batch file, Base64 encoded."""

    compression_type: CompressionType | None = None
    """Compression used for the batch file. Defaults to KSeF's ZIP behavior."""

    parts: list[BatchFilePart] = Field(max_length=MAX_BATCH_FILE_PARTS)
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


class BatchSessionResumeState(BaseSessionResumeState):
    """Serializable resume state of a batch session.

    This class holds all information needed to resume a batch session
    or to upload file parts. Use ``to_json()`` when
    intentionally exporting resumable JSON containing encryption material and
    presigned upload URLs.

    Inherits common session fields from BaseSessionResumeState:
    - reference_number, aes_key, iv, form_code
    - get_aes_key_bytes(), get_iv_bytes() helper methods
    """

    part_upload_requests: list[PartUploadRequest] = Field(exclude=True, repr=False)
    """Upload instructions for each file part."""

    @override
    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] | str = "json",
    ) -> dict[str, object]:
        """Export batch resume state with secrets and upload URLs included.

        The returned data contains the AES key, IV, and presigned upload URLs.
        Store and log it only as protected credential material.
        """
        data = super().to_dict(mode=mode)
        data["part_upload_requests"] = [
            request.model_dump(mode=mode) for request in self.part_upload_requests
        ]
        return data

    @classmethod
    def from_encoded(
        cls,
        reference_number: str,
        aes_key: bytes,
        iv: bytes,
        form_code: FormSchema,
        part_upload_requests: list[PartUploadRequest],
        *,
        access_token: str | None = None,
    ) -> Self:
        """Create state from raw bytes (aes_key, iv).

        Args:
            reference_number: Batch session reference number.
            aes_key: Raw AES key bytes.
            iv: Raw initialization vector bytes.
            form_code: Invoice schema for this session.
            part_upload_requests: Upload instructions for file parts.
            access_token: Deprecated and ignored. Persist authentication state
                separately with ``AuthenticationResumeState``.

        Returns:
            BatchSessionResumeState with Base64-encoded key and IV.
        """
        if access_token is not None:
            warnings.warn(
                "BatchSessionResumeState.from_encoded(access_token=...) is "
                "deprecated and ignored; persist AuthenticationResumeState separately.",
                DeprecationWarning,
                stacklevel=2,
            )
        return cls(
            reference_number=reference_number,
            aes_key=SecretStr(base64.b64encode(aes_key).decode()),
            iv=SecretStr(base64.b64encode(iv).decode()),
            form_code=form_code,
            part_upload_requests=part_upload_requests,
        )


if TYPE_CHECKING:
    BatchSessionState = BatchSessionResumeState


_DEPRECATED_BATCH_EXPORTS = {
    "BatchSessionState": (
        BatchSessionResumeState,
        "BatchSessionState is deprecated and will be removed in a future release; "
        "use BatchSessionResumeState instead.",
    ),
}


def __getattr__(name: str) -> object:
    if name in _DEPRECATED_BATCH_EXPORTS:
        value, message = _DEPRECATED_BATCH_EXPORTS[name]
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
