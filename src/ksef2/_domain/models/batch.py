"""Domain models for batch session operations."""

import base64
import binascii
import warnings
from typing import TYPE_CHECKING, Literal, Self, override

from pydantic import Field, SecretStr, field_validator

from ksef2._domain.models.base import KSeFBaseModel
from ksef2._domain.models.compression import (
    CompressionType,
    normalize_compression_type,
)
from ksef2._domain.models.session import (
    BaseSessionResumeState,
    FormSchema,
    deprecation_message,
)


MAX_BATCH_FILE_SIZE_BYTES = 5_000_000_000
MAX_BATCH_FILE_PARTS = 50
MAX_BATCH_PART_PRE_ENCRYPTION_SIZE_BYTES = 100_000_000
MAX_AES_CBC_PADDING_BYTES = 16
# The API's 100MB part limit is pre-encryption; this model stores encrypted bytes.
MAX_BATCH_ENCRYPTED_PART_SIZE_BYTES = (
    MAX_BATCH_PART_PRE_ENCRYPTION_SIZE_BYTES + MAX_AES_CBC_PADDING_BYTES
)


def _validate_encoded_batch_material(
    value: str, *, field_name: str, expected_length: int | None = None
) -> str:
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{field_name} must be valid Base64") from exc
    if expected_length is not None and len(decoded) != expected_length:
        raise ValueError(f"{field_name} must decode to {expected_length} bytes")
    if not decoded:
        raise ValueError(f"{field_name} must not be empty")
    return value


class BatchInvoice(KSeFBaseModel):
    """Single invoice payload to include in a batch ZIP."""

    file_name: str
    """Name of the ZIP entry, for example ``invoice-1.xml``."""
    content: bytes
    """Invoice XML bytes."""


class BatchInvoiceHash(KSeFBaseModel):
    """Correlation data between a ZIP entry and the original XML hash."""

    file_name: str
    """Name of the ZIP entry the hash belongs to."""
    invoice_hash: str
    """SHA-256 hash of the original invoice XML, Base64-encoded."""


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

    aes_key: str = Field(exclude=True, repr=False)
    """AES-256 session key, Base64-encoded. Excluded from serialization and ``repr``."""
    iv: str = Field(exclude=True, repr=False)
    """AES initialization vector, Base64-encoded. Excluded from serialization and ``repr``."""
    encrypted_key: str = Field(exclude=True, repr=False)
    """Session key encrypted with the KSeF public key, Base64-encoded. Excluded from serialization and ``repr``."""
    public_key_id: str | None = None
    """Identifier of the KSeF public key used for encryption; ``None`` for the default."""

    @field_validator("aes_key")
    @classmethod
    def _validate_aes_key(cls, value: str) -> str:
        return _validate_encoded_batch_material(
            value, field_name="aes_key", expected_length=32
        )

    @field_validator("iv")
    @classmethod
    def _validate_iv(cls, value: str) -> str:
        return _validate_encoded_batch_material(
            value, field_name="iv", expected_length=16
        )

    @field_validator("encrypted_key")
    @classmethod
    def _validate_encrypted_key(cls, value: str) -> str:
        return _validate_encoded_batch_material(value, field_name="encrypted_key")

    @classmethod
    def from_bytes(
        cls,
        *,
        aes_key: bytes,
        iv: bytes,
        encrypted_key: bytes,
        public_key_id: str | None = None,
    ) -> Self:
        """Create encoded batch encryption data from raw key bytes.

        Args:
            aes_key: Raw AES-256 key.
            iv: Raw AES initialization vector.
            encrypted_key: AES key encrypted with the KSeF public key.
            public_key_id: Identifier of the KSeF public key used; ``None`` for the default.

        Returns:
            Encryption data with all byte values Base64-encoded.
        """
        return cls(
            aes_key=base64.b64encode(aes_key).decode(),
            iv=base64.b64encode(iv).decode(),
            encrypted_key=base64.b64encode(encrypted_key).decode(),
            public_key_id=public_key_id,
        )

    def get_aes_key_bytes(self) -> bytes:
        """Return the decoded AES key.

        Returns:
            The raw AES key bytes.
        """
        return base64.b64decode(self.aes_key, validate=True)

    def get_iv_bytes(self) -> bytes:
        """Return the decoded initialization vector.

        Returns:
            The raw initialization vector bytes.
        """
        return base64.b64decode(self.iv, validate=True)

    def get_encrypted_key_bytes(self) -> bytes:
        """Return the decoded encrypted symmetric key.

        Returns:
            The raw encrypted key bytes.
        """
        return base64.b64decode(self.encrypted_key, validate=True)

    def to_sensitive_dict(self) -> dict[str, str | None]:
        """Export encryption material for deliberately protected persistence.

        Returns:
            A dictionary with the Base64 AES key, IV, encrypted key and public key identifier.
        """
        return {
            "aes_key": self.aes_key,
            "iv": self.iv,
            "encrypted_key": self.encrypted_key,
            "public_key_id": self.public_key_id,
        }


class BatchPreparedPart(KSeFBaseModel):
    """Prepared encrypted batch part ready for upload."""

    ordinal_number: int
    """One-based position of the part in the package."""
    content: bytes
    """Encrypted part bytes to upload."""
    file_size: int
    """Size of the encrypted part in bytes."""
    file_hash: str
    """SHA-256 hash of the encrypted part, Base64-encoded."""


class PreparedBatch(KSeFBaseModel):
    """Prepared batch package with encrypted parts and upload metadata."""

    form_code: FormSchema = FormSchema.FA3
    """Invoice schema of the batch. Defaults to FA(3)."""
    offline_mode: bool = False
    """Whether the invoices were issued in offline mode."""
    batch_file: BatchFileInfo
    """Size, hash and part metadata of the whole batch file."""
    parts: list[BatchPreparedPart]
    """Encrypted parts to upload."""
    encryption: BatchEncryptionData
    """Encryption material used for the parts."""
    invoices: list[BatchInvoiceHash]
    """Hash of each invoice in the package, keyed by ZIP entry name."""


class OpenBatchSessionRequest(KSeFBaseModel):
    """Request to open a batch session."""

    encrypted_key: bytes
    """Session AES key encrypted with the KSeF public key."""
    iv: bytes
    """AES initialization vector used for the session."""
    public_key_id: str | None = None
    """Identifier of the KSeF public key used for encryption; ``None`` for the default."""
    batch_file: BatchFileInfo
    """Size, hash and part metadata of the batch file."""
    form_code: FormSchema = FormSchema.FA3
    """Invoice schema of the batch. Defaults to FA(3)."""
    offline_mode: bool = False
    """Whether the invoices were issued in offline mode."""


class PartUploadRequest(KSeFBaseModel):
    """Upload endpoint information for a batch session part."""

    ordinal_number: int
    """Sequential number of the file part (1-indexed)."""

    method: str
    """HTTP method to use for uploading (typically PUT)."""

    url: str = Field(exclude=True, repr=False)
    """URL to upload the file part to."""

    headers: dict[str, str | None]
    """Headers to include in the upload request."""

    def to_sensitive_dict(
        self, *, mode: Literal["json", "python"] | str = "json"
    ) -> dict[str, object]:
        """Export upload instructions with the presigned capability URL.

        Args:
            mode: Pydantic dump mode, ``"json"`` for JSON-safe values or ``"python"`` for native types.

        Returns:
            A dictionary including the plain upload URL.
        """
        data: dict[str, object] = self.model_dump(mode=mode)
        data["url"] = self.url
        return data


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

    Deprecated:
        The alias ``BatchSessionState`` is removed in ksef2 2.0; use ``BatchSessionResumeState``.
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

        Args:
            mode: Pydantic dump mode, ``"json"`` for JSON-safe values or ``"python"`` for native types.

        Returns:
            A dictionary with the full resume state, including secrets.
        """
        data = super().to_dict(mode=mode)
        data["part_upload_requests"] = [
            request.to_sensitive_dict(mode=mode)
            for request in self.part_upload_requests
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
                "The `access_token` argument of "
                "`BatchSessionResumeState.from_encoded()` is deprecated and will "
                "be removed in ksef2 2.0; it is ignored, persist "
                "`AuthenticationResumeState` separately instead.",
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
        deprecation_message(
            "ksef2._domain.models.batch.BatchSessionState", "BatchSessionResumeState"
        ),
    ),
}


def __getattr__(name: str) -> object:
    if name in _DEPRECATED_BATCH_EXPORTS:
        value, message = _DEPRECATED_BATCH_EXPORTS[name]
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
