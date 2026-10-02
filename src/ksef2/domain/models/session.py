"""Domain models for online, batch, and authentication sessions."""

import base64
import binascii
import json
import warnings
from collections.abc import Mapping
from datetime import datetime
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Literal, Self, cast

from pydantic import (
    AwareDatetime,
    AnyUrl,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from typing_extensions import deprecated

from ksef2.domain.models.base import KSeFBaseModel, KSeFPersistedModel


def _validate_encoded_session_secret(
    value: object, *, field_name: str, expected_length: int
) -> object:
    encoded = value.get_secret_value() if isinstance(value, SecretStr) else value
    if not isinstance(encoded, str):
        return value
    if encoded == "**********":
        raise ValueError(
            "Resume state contains redacted encryption material; "
            "use to_json() for explicit sensitive export."
        )
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{field_name} must be valid Base64") from exc
    if len(decoded) != expected_length:
        raise ValueError(f"{field_name} must decode to {expected_length} bytes")
    return value


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


class SessionEncryptionMaterial(KSeFBaseModel):
    """Raw and encrypted symmetric session key material."""

    aes_key: bytes = Field(exclude=True, repr=False)
    iv: bytes = Field(exclude=True, repr=False)
    encrypted_key: bytes = Field(exclude=True, repr=False)
    public_key_id: str | None = None


type SessionType = Literal["online", "batch"]


type SessionStatus = Literal["in_progress", "succeeded", "failed", "cancelled"]

type SessionTypeSpecValue = Literal["Online", "Batch"]


type SessionStatusSpecValue = Literal["InProgress", "Succeeded", "Failed", "Cancelled"]


class SessionTypeEnum(StrEnum):
    """Runtime enum for KSeF session type values."""

    ONLINE = "Online"
    BATCH = "Batch"


class SessionStatusEnum(StrEnum):
    """Runtime enum for KSeF session status values."""

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
    """Normalize SDK or OpenAPI session type values to SDK literals.

    Raises:
        ValueError: If ``value`` is not a supported session type.
    """
    if isinstance(value, SessionTypeEnum):
        return _SESSION_TYPE_FROM_SPEC[value.value]

    lowered_value = value.strip().lower()
    if lowered_value in _SESSION_TYPE_TO_SPEC:
        return lowered_value

    if value in _SESSION_TYPE_FROM_SPEC:
        return _SESSION_TYPE_FROM_SPEC[value]

    raise ValueError(
        f"Invalid session type: {value}. Valid session types are: "
        f"{', '.join(_SESSION_TYPE_TO_SPEC)}"
    )


def normalize_session_status(
    value: SessionStatus | SessionStatusEnum | str,
) -> SessionStatus:
    """Normalize SDK or OpenAPI session status values to SDK literals.

    Raises:
        ValueError: If ``value`` is not a supported session status.
    """
    if isinstance(value, SessionStatusEnum):
        return _SESSION_STATUS_FROM_SPEC[value.value]

    lowered_value = value.strip().lower()
    if lowered_value in _SESSION_STATUS_TO_SPEC:
        return lowered_value

    if value in _SESSION_STATUS_FROM_SPEC:
        return _SESSION_STATUS_FROM_SPEC[value]

    raise ValueError(
        f"Invalid session status: {value}. Valid session statuses are: "
        f"{', '.join(_SESSION_STATUS_TO_SPEC)}"
    )


def session_type_to_spec(
    value: SessionType | SessionTypeEnum | str,
) -> SessionTypeSpecValue:
    """Convert a session type value to the OpenAPI representation."""
    return _SESSION_TYPE_TO_SPEC[normalize_session_type(value)]


def session_status_to_spec(
    value: SessionStatus | SessionStatusEnum | str,
) -> SessionStatusSpecValue:
    """Convert a session status value to the OpenAPI representation."""
    return _SESSION_STATUS_TO_SPEC[normalize_session_status(value)]


class StatusInfo(KSeFBaseModel):
    """Generic KSeF status code, description, and optional details."""

    code: int
    description: str
    details: list[str] | None = None


class InvoiceStatusInfo(KSeFBaseModel):
    """Invoice processing status returned within session APIs."""

    code: int
    description: str
    details: list[str] | None = None
    extensions: dict[str, str | None] | None = None


class OpenOnlineSessionRequest(KSeFBaseModel):
    """Payload used to open an online invoice session."""

    encrypted_key: bytes
    iv: bytes
    public_key_id: str | None = None
    form_code: FormSchema = FormSchema.FA3


class OpenOnlineSessionResponse(KSeFBaseModel):
    """Response returned after opening an online invoice session."""

    reference_number: str
    valid_until: AwareDatetime


class UpoPage(KSeFBaseModel):
    """Download information for one UPO page."""

    reference_number: str
    download_url: AnyUrl = Field(exclude=True, repr=False)
    download_url_expiration_date: AwareDatetime

    def to_sensitive_dict(
        self, *, mode: Literal["json", "python"] | str = "json"
    ) -> dict[str, object]:
        """Export UPO metadata with its capability-bearing download URL."""
        data: dict[str, object] = self.model_dump(mode=mode)
        data["download_url"] = (
            str(self.download_url) if mode == "json" else self.download_url
        )
        return data


class Upo(KSeFBaseModel):
    """Collection of UPO pages available for a session or invoice."""

    pages: list[UpoPage]


class SessionStatusResponse(KSeFBaseModel):
    """Current status and counters for an online or batch session."""

    status: StatusInfo
    date_created: AwareDatetime
    date_updated: AwareDatetime
    valid_until: AwareDatetime | None = None
    upo: Upo | None = None
    invoice_count: int | None = None
    successful_invoice_count: int | None = None
    failed_invoice_count: int | None = None


class SessionInvoiceStatusResponse(KSeFBaseModel):
    """Processing status for one invoice submitted in a session."""

    ordinal_number: int
    invoice_number: str | None = None
    ksef_number: str | None = None
    reference_number: str
    invoice_hash: str
    invoice_file_name: str | None = None
    acquisition_date: AwareDatetime | None = None
    invoicing_date: AwareDatetime
    permanent_storage_date: AwareDatetime | None = None
    upo_download_url: AnyUrl | None = Field(default=None, exclude=True, repr=False)
    upo_download_url_expiration_date: AwareDatetime | None = None
    invoicing_mode: str | None = None
    status: InvoiceStatusInfo

    def to_sensitive_dict(
        self, *, mode: Literal["json", "python"] | str = "json"
    ) -> dict[str, object]:
        """Export invoice status with its capability-bearing UPO URL."""
        data: dict[str, object] = self.model_dump(mode=mode)
        if self.upo_download_url is not None:
            data["upo_download_url"] = (
                str(self.upo_download_url) if mode == "json" else self.upo_download_url
            )
        return data


class SessionInvoicesResponse(KSeFBaseModel):
    """One page of invoices submitted in a session."""

    continuation_token: str | None = None
    invoices: list[SessionInvoiceStatusResponse]


class SessionSummary(KSeFBaseModel):
    """Summary row returned when listing sessions."""

    reference_number: str
    status: StatusInfo
    date_created: AwareDatetime
    date_updated: AwareDatetime
    valid_until: AwareDatetime | None = None
    total_invoice_count: int
    successful_invoice_count: int
    failed_invoice_count: int


class ListSessionsResponse(KSeFBaseModel):
    """One page of session summaries."""

    continuation_token: str | None = None
    sessions: list[SessionSummary]


def deprecation_message(old_name: str, new_name: str) -> str:
    """Build the standard 2.0-removal deprecation message."""
    return (
        f"`{old_name}` is deprecated and will be removed in ksef2 2.0; "
        f"use `{new_name}` instead."
    )


class BaseSessionResumeState(KSeFPersistedModel):
    """Base class for session resume state with common fields.

    This class contains fields shared between online and batch sessions.
    It provides serialization/deserialization support and helper methods
    for accessing the encryption keys.
    """

    format_version: Literal[1] = 1

    reference_number: str
    """Reference number of the session."""

    aes_key: SecretStr
    """AES key for encrypting data, Base64 encoded."""

    iv: SecretStr
    """Initialization vector for AES encryption, Base64 encoded."""

    form_code: FormSchema
    """Invoice schema used for this session."""

    @field_validator("aes_key", mode="before")
    @classmethod
    def _validate_encoded_aes_key(cls, value: object) -> object:
        return _validate_encoded_session_secret(
            value, field_name="aes_key", expected_length=32
        )

    @field_validator("iv", mode="before")
    @classmethod
    def _validate_encoded_iv(cls, value: object) -> object:
        return _validate_encoded_session_secret(
            value, field_name="iv", expected_length=16
        )

    @model_validator(mode="before")
    @classmethod
    def _drop_legacy_access_token(cls, data: object) -> object:
        """Accept pre-auth-state resume JSON that still carried bearer auth."""
        if not isinstance(data, dict):
            return data
        state_data = cast(dict[str, object], data)
        if "access_token" not in state_data:
            return state_data

        warnings.warn(
            "The `access_token` key in session resume state is deprecated and "
            "will be removed in ksef2 2.0; it is ignored, persist "
            "`AuthenticationResumeState` separately instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        cleaned = dict(state_data)
        _ = cleaned.pop("access_token")
        return cleaned

    @field_validator("form_code", mode="before")
    @classmethod
    def _coerce_form_code(cls, value: object) -> object:
        """
        Pydantic serializes Enum values that are tuples as JSON arrays (lists).
        On restore, convert list -> tuple so Enum validation succeeds.
        Also accept enum names as a convenience ("FA3", etc.).
        """
        if isinstance(value, list):
            return tuple(cast(list[object], value))
        if isinstance(value, str):
            try:
                return FormSchema[value]
            except KeyError:
                return value
        return value

    def get_aes_key_bytes(self) -> bytes:
        """Get the AES key as raw bytes."""
        return base64.b64decode(self.aes_key.get_secret_value(), validate=True)

    def get_iv_bytes(self) -> bytes:
        """Get the initialization vector as raw bytes."""
        return base64.b64decode(self.iv.get_secret_value(), validate=True)

    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] | str = "json",
    ) -> dict[str, object]:
        """Export resume state with credentials included.

        The returned data contains the AES key, IV, and for batch sessions the
        presigned upload URLs. Store and log it only as protected credential
        material.
        """
        data: dict[str, object] = self.model_dump(mode=mode)
        data["aes_key"] = self.aes_key.get_secret_value()
        data["iv"] = self.iv.get_secret_value()
        if mode == "json":
            data["form_code"] = self.form_code.name
        return data

    def to_json(self, *, indent: int | None = None) -> str:
        """Export resume state as JSON with credentials included."""
        data = self.to_dict(mode="json")
        if indent is None:
            return json.dumps(data, separators=(",", ":"))
        return json.dumps(data, indent=indent)

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Restore resume state from a dictionary exported by ``to_dict()``."""
        return cls.model_validate(state)

    @classmethod
    def from_json(cls, state: str | bytes | bytearray) -> Self:
        """Restore resume state from JSON exported by ``to_json()``."""
        return cls.model_validate_json(state)

    @deprecated(
        "`dump_state()` is deprecated and will be removed in ksef2 2.0; "
        "use `to_dict()` instead."
    )
    def dump_state(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
    ) -> dict[str, object]:
        """Deprecated compatibility wrapper for ``to_dict()``."""
        return self.to_dict(mode=mode)

    @deprecated(
        "`model_dump_sensitive()` is deprecated and will be removed in ksef2 2.0; "
        "use `to_dict()` instead."
    )
    def model_dump_sensitive(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
    ) -> dict[str, object]:
        """Deprecated compatibility wrapper for ``to_dict()``."""
        return self.to_dict(mode=mode)

    @deprecated(
        "`model_dump_sensitive_json()` is deprecated and will be removed in ksef2 2.0; "
        "use `to_json()` instead."
    )
    def model_dump_sensitive_json(self, *, indent: int | None = None) -> str:
        """Deprecated compatibility wrapper for ``to_json()``."""
        return self.to_json(indent=indent)

    @classmethod
    @deprecated(
        "`from_state()` is deprecated and will be removed in ksef2 2.0; "
        "use `from_dict()` instead."
    )
    def from_state(cls, state: Mapping[str, object]) -> Self:
        """Deprecated compatibility wrapper for ``from_dict()``."""
        return cls.from_dict(state)


class OnlineSessionResumeState(BaseSessionResumeState):
    """Serializable resume state of an online session.

    This class holds all information needed to resume an online session.
    Use ``to_json()`` when intentionally exporting
    resumable JSON containing credentials.
    """

    valid_until: AwareDatetime
    """Expiration time of the session."""

    @classmethod
    def from_encoded(
        cls,
        reference_number: str,
        aes_key: bytes,
        iv: bytes,
        valid_until: datetime,
        form_code: FormSchema,
        *,
        access_token: str | None = None,
    ) -> Self:
        """Create state from raw bytes (aes_key, iv).

        Args:
            reference_number: Session reference number.
            aes_key: Raw AES key bytes.
            iv: Raw initialization vector bytes.
            valid_until: Session expiration time.
            form_code: Invoice schema for this session.
            access_token: Deprecated and ignored. Persist authentication state
                separately with ``AuthenticationResumeState``.

        Returns:
            OnlineSessionResumeState with Base64-encoded key and IV.
        """
        if access_token is not None:
            warnings.warn(
                "The `access_token` argument of "
                "`OnlineSessionResumeState.from_encoded()` is deprecated and will "
                "be removed in ksef2 2.0; it is ignored, persist "
                "`AuthenticationResumeState` separately instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        return cls(
            reference_number=reference_number,
            aes_key=SecretStr(base64.b64encode(aes_key).decode()),
            iv=SecretStr(base64.b64encode(iv).decode()),
            valid_until=valid_until,
            form_code=form_code,
        )


if TYPE_CHECKING:
    BaseSessionState = BaseSessionResumeState
    OnlineSessionState = OnlineSessionResumeState


_DEPRECATED_SESSION_EXPORTS = {
    "BaseSessionState": (
        BaseSessionResumeState,
        deprecation_message(
            "ksef2.domain.models.session.BaseSessionState", "BaseSessionResumeState"
        ),
    ),
    "OnlineSessionState": (
        OnlineSessionResumeState,
        deprecation_message(
            "ksef2.domain.models.session.OnlineSessionState",
            "OnlineSessionResumeState",
        ),
    ),
}


def __getattr__(name: str) -> object:
    if name in _DEPRECATED_SESSION_EXPORTS:
        value, message = _DEPRECATED_SESSION_EXPORTS[name]
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
