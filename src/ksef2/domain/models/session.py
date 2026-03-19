import base64
from datetime import datetime
from enum import Enum, StrEnum
from typing import Self, Literal

from pydantic import AwareDatetime, AnyUrl, field_validator

from ksef2.domain.models.base import KSeFBaseModel


class FormSchema(Enum):
    """Supported form schemas for online sessions."""

    FA2 = ("FA (2)", "1-0E", "FA")
    FA3 = ("FA (3)", "1-0E", "FA")
    FA_RR1 = ("FA_RR (1)", "1-1E", "FA_RR")
    PEF3 = ("PEF (3)", "2-1", "PEF")
    PEF_KOR3 = ("PEF_KOR (3)", "2-1", "PEF")

    def __init__(self, system_code: str, schema_version: str, schema_value: str):
        self.system_code = system_code
        self.schema_version = schema_version
        self.schema_value = schema_value


type SessionType = Literal["online", "batch"]


type SessionStatus = Literal["in_progress", "succeeded", "failed", "cancelled"]

type SessionTypeSpecValue = Literal["Online", "Batch"]


type SessionStatusSpecValue = Literal["InProgress", "Succeeded", "Failed", "Cancelled"]


class SessionTypeEnum(StrEnum):
    ONLINE = "Online"
    BATCH = "Batch"


class SessionStatusEnum(StrEnum):
    IN_PROGRESS = "InProgress"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


_SESSION_TYPE_TO_SPEC: dict[SessionType, SessionTypeSpecValue] = {
    "online": "Online",
    "batch": "Batch",
}
_SESSION_STATUS_TO_SPEC: dict[SessionStatus, SessionStatusSpecValue] = {
    "in_progress": "InProgress",
    "succeeded": "Succeeded",
    "failed": "Failed",
    "cancelled": "Cancelled",
}
_SESSION_TYPE_FROM_SPEC: dict[SessionTypeSpecValue, SessionType] = {
    value: key for key, value in _SESSION_TYPE_TO_SPEC.items()
}
_SESSION_STATUS_FROM_SPEC: dict[SessionStatusSpecValue, SessionStatus] = {
    value: key for key, value in _SESSION_STATUS_TO_SPEC.items()
}


def normalize_session_type(value: SessionType | SessionTypeEnum | str) -> SessionType:
    if isinstance(value, SessionTypeEnum):
        return _SESSION_TYPE_FROM_SPEC[value.value]

    lowered_value = value.strip().lower()
    if lowered_value in _SESSION_TYPE_TO_SPEC:
        return lowered_value  # pyright: ignore[reportReturnType]

    if value in _SESSION_TYPE_FROM_SPEC:
        return _SESSION_TYPE_FROM_SPEC[value]

    raise ValueError(
        f"Invalid session type: {value}. Valid session types are: "
        f"{', '.join(_SESSION_TYPE_TO_SPEC)}"
    )


def normalize_session_status(
    value: SessionStatus | SessionStatusEnum | str,
) -> SessionStatus:
    if isinstance(value, SessionStatusEnum):
        return _SESSION_STATUS_FROM_SPEC[value.value]

    lowered_value = value.strip().lower()
    if lowered_value in _SESSION_STATUS_TO_SPEC:
        return lowered_value  # pyright: ignore[reportReturnType]

    if value in _SESSION_STATUS_FROM_SPEC:
        return _SESSION_STATUS_FROM_SPEC[value]

    raise ValueError(
        f"Invalid session status: {value}. Valid session statuses are: "
        f"{', '.join(_SESSION_STATUS_TO_SPEC)}"
    )


def session_type_to_spec(
    value: SessionType | SessionTypeEnum | str,
) -> SessionTypeSpecValue:
    return _SESSION_TYPE_TO_SPEC[normalize_session_type(value)]


def session_status_to_spec(
    value: SessionStatus | SessionStatusEnum | str,
) -> SessionStatusSpecValue:
    return _SESSION_STATUS_TO_SPEC[normalize_session_status(value)]


class StatusInfo(KSeFBaseModel):
    code: int
    description: str
    details: list[str] | None = None


class InvoiceStatusInfo(KSeFBaseModel):
    code: int
    description: str
    details: list[str] | None = None
    extensions: dict[str, str | None] | None = None


class OpenOnlineSessionRequest(KSeFBaseModel):
    encrypted_key: bytes
    iv: bytes
    form_code: FormSchema = FormSchema.FA3


class OpenOnlineSessionResponse(KSeFBaseModel):
    reference_number: str
    valid_until: AwareDatetime


class UpoPage(KSeFBaseModel):
    reference_number: str
    download_url: AnyUrl
    download_url_expiration_date: AwareDatetime


class Upo(KSeFBaseModel):
    pages: list[UpoPage]


class SessionStatusResponse(KSeFBaseModel):
    status: StatusInfo
    date_created: AwareDatetime
    date_updated: AwareDatetime
    valid_until: AwareDatetime | None = None
    upo: Upo | None = None
    invoice_count: int | None = None
    successful_invoice_count: int | None = None
    failed_invoice_count: int | None = None


class SessionInvoiceStatusResponse(KSeFBaseModel):
    ordinal_number: int
    invoice_number: str | None = None
    ksef_number: str | None = None
    reference_number: str
    invoice_hash: str
    invoice_file_name: str | None = None
    acquisition_date: AwareDatetime | None = None
    invoicing_date: AwareDatetime
    permanent_storage_date: AwareDatetime | None = None
    upo_download_url: AnyUrl | None = None
    upo_download_url_expiration_date: AwareDatetime | None = None
    invoicing_mode: str | None = None
    status: InvoiceStatusInfo


class SessionInvoicesResponse(KSeFBaseModel):
    continuation_token: str | None = None
    invoices: list[SessionInvoiceStatusResponse]


class SessionSummary(KSeFBaseModel):
    reference_number: str
    status: StatusInfo
    date_created: AwareDatetime
    date_updated: AwareDatetime
    valid_until: AwareDatetime | None = None
    total_invoice_count: int
    successful_invoice_count: int
    failed_invoice_count: int


class ListSessionsResponse(KSeFBaseModel):
    continuation_token: str | None = None
    sessions: list[SessionSummary]


class BaseSessionState(KSeFBaseModel):
    """Base class for session state with common fields.

    This class contains fields shared between online and batch sessions.
    It provides serialization/deserialization support and helper methods
    for accessing the encryption keys.
    """

    reference_number: str
    """Reference number of the session."""

    aes_key: str
    """AES key for encrypting data, Base64 encoded."""

    iv: str
    """Initialization vector for AES encryption, Base64 encoded."""

    access_token: str
    """Bearer token for API authentication."""

    form_code: FormSchema
    """Invoice schema used for this session."""

    @field_validator("form_code", mode="before")
    @classmethod
    def _coerce_form_code(cls, value: object) -> object:
        """
        Pydantic serializes Enum values that are tuples as JSON arrays (lists).
        On restore, convert list -> tuple so Enum validation succeeds.
        Also accept enum names as a convenience ("FA3", etc.).
        """
        if isinstance(value, list):
            return tuple(value)
        if isinstance(value, str):
            try:
                return FormSchema[value]
            except KeyError:
                return value
        return value

    def get_aes_key_bytes(self) -> bytes:
        """Get the AES key as raw bytes."""
        return base64.b64decode(self.aes_key)

    def get_iv_bytes(self) -> bytes:
        """Get the initialization vector as raw bytes."""
        return base64.b64decode(self.iv)


class OnlineSessionState(BaseSessionState):
    """Serializable state of an online session.

    This class holds all information needed to resume an online session.
    Can be serialized to JSON for persistence.
    """

    valid_until: AwareDatetime
    """Expiration time of the session."""

    @classmethod
    def from_encoded(
        cls,
        reference_number: str,
        aes_key: bytes,
        iv: bytes,
        access_token: str,
        valid_until: datetime,
        form_code: FormSchema,
    ) -> Self:
        """Create state from raw bytes (aes_key, iv).

        Args:
            reference_number: Session reference number.
            aes_key: Raw AES key bytes.
            iv: Raw initialization vector bytes.
            access_token: Bearer token for authentication.
            valid_until: Session expiration time.
            form_code: Invoice schema for this session.

        Returns:
            SessionState with Base64-encoded key and IV.
        """
        return cls(
            reference_number=reference_number,
            aes_key=base64.b64encode(aes_key).decode(),
            iv=base64.b64encode(iv).decode(),
            access_token=access_token,
            valid_until=valid_until,
            form_code=form_code,
        )
