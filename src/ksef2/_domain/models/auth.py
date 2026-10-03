"""Domain models for authentication flows and auth sessions."""

import json
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator

from ksef2._domain.models.base import KSeFBaseModel, KSeFPersistedModel

type ContextIdentifierType = Literal["nip", "internal_id", "nip_vat_ue", "peppol_id"]

type AuthenticationMethod = Literal[
    "token",
    "trusted_profile",
    "internal_certificate",
    "qualified_signature",
    "qualified_seal",
    "personal_signature",
    "peppol_signature",
    "ksef_certificate",
    "other",
]

type AuthenticationMethodCategory = Literal[
    "xades_signature",
    "national_node",
    "token",
    "other",
]


class ContextIdentifierTypeEnum(StrEnum):
    """Runtime enum for authentication context identifier types."""

    NIP = "nip"
    INTERNAL_ID = "internal_id"
    NIP_VAT_UE = "nip_vat_ue"
    PEPPOL_ID = "peppol_id"


class AuthenticationMethodEnum(StrEnum):
    """Runtime enum for authentication methods reported by KSeF."""

    TOKEN = "token"
    TRUSTED_PROFILE = "trusted_profile"
    INTERNAL_CERTIFICATE = "internal_certificate"
    QUALIFIED_SIGNATURE = "qualified_signature"
    QUALIFIED_SEAL = "qualified_seal"
    PERSONAL_SIGNATURE = "personal_signature"
    PEPPOL_SIGNATURE = "peppol_signature"
    KSEF_CERTIFICATE = "ksef_certificate"
    OTHER = "other"


class AuthenticationMethodCategoryEnum(StrEnum):
    """Runtime enum for broad authentication method categories."""

    XADES_SIGNATURE = "xades_signature"
    NATIONAL_NODE = "national_node"
    TOKEN = "token"
    OTHER = "other"


class InitTokenAuthenticationRequest(KSeFBaseModel):
    """Payload used to authenticate with a previously generated KSeF token."""

    challenge: str
    """Challenge obtained from KSeF before authenticating."""
    context_type: ContextIdentifierType
    """Kind of identifier in ``context_value``."""
    context_value: str
    """Identifier of the context to authenticate in, such as a NIP."""
    encrypted_token: str
    """KSeF token and challenge timestamp, encrypted with the KSeF public key and Base64-encoded."""
    public_key_id: str | None = None
    """Identifier of the KSeF public key used for encryption; ``None`` for the default."""


class ChallengeResponse(KSeFBaseModel):
    """Challenge material returned before token or XAdES authentication starts."""

    challenge: str
    """Challenge string to include in the authentication request."""
    timestamp: datetime
    """Server time at which the challenge was issued."""
    timestamp_ms: int
    """Challenge issue time as Unix milliseconds."""


class TokenCredentials(KSeFBaseModel):
    """A bearer token together with its expiration time."""

    token: str = Field(exclude=True, repr=False)
    """Bearer token value. Excluded from serialization and ``repr``."""
    valid_until: datetime
    """When the token expires."""


class AuthInitResponse(KSeFBaseModel):
    """Initial authentication response containing the short-lived auth token."""

    reference_number: str
    """Reference number of the authentication operation."""
    authentication_token: TokenCredentials
    """Short-lived token used to poll the operation and redeem the access tokens."""


class AuthOperationStatus(KSeFBaseModel):
    """Status of an in-progress authentication operation."""

    start_date: datetime
    """When the authentication operation started."""
    authentication_method: AuthenticationMethod
    """Authentication method in use."""
    authentication_method_category: AuthenticationMethodCategory
    """Broad category of the authentication method."""
    authentication_method_code: str
    """Raw authentication method code reported by KSeF."""
    authentication_method_display_name: str
    """Display name of the authentication method."""
    status_code: int
    """Numeric status code; ``200`` means authentication succeeded."""
    status_description: str
    """Human-readable description of the status."""
    status_details: list[str] | None = None
    """Additional status details, if any."""
    is_token_redeemed: bool | None = None
    """Whether the access tokens were already redeemed."""
    last_token_refresh_date: datetime | None = None
    """When the access token was last refreshed; ``None`` if never."""
    refresh_token_valid_until: datetime | None = None
    """When the refresh token expires."""


class AuthenticationSession(KSeFBaseModel):
    """Metadata describing an authentication session visible in session listings."""

    reference_number: str
    """Reference number of the authentication session."""
    start_date: datetime
    """When the session started."""
    authentication_method: AuthenticationMethod
    """Authentication method used."""
    authentication_method_category: AuthenticationMethodCategory
    """Broad category of the authentication method."""
    authentication_method_code: str
    """Raw authentication method code reported by KSeF."""
    authentication_method_display_name: str
    """Display name of the authentication method."""
    status_code: int
    """Numeric status code of the session."""
    status_description: str
    """Human-readable description of the status."""
    status_details: list[str] | None = None
    """Additional status details, if any."""
    is_token_redeemed: bool | None = None
    """Whether the access tokens were already redeemed."""
    last_token_refresh_date: datetime | None = None
    """When the access token was last refreshed; ``None`` if never."""
    refresh_token_valid_until: datetime | None = None
    """When the refresh token expires."""
    is_current: bool | None = None
    """Whether this is the session of the calling client."""


class AuthenticationSessionsResponse(KSeFBaseModel):
    """A single page of authentication sessions."""

    continuation_token: str | None = None
    """Opaque token for requesting the next page; ``None`` when there are no more pages."""
    items: list[AuthenticationSession]
    """Authentication sessions on this page."""


class AuthTokens(KSeFBaseModel):
    """Access and refresh tokens returned after successful authentication."""

    access_token: TokenCredentials
    """Short-lived token sent with API requests."""
    refresh_token: TokenCredentials
    """Longer-lived token used to obtain new access tokens."""


class AuthenticationResumeState(KSeFPersistedModel):
    """Serializable authentication state used to rehydrate an authenticated client.

    Use ``to_json()`` when intentionally exporting resumable JSON containing
    bearer credentials. Normal Pydantic dumps and repr output keep token values
    redacted.
    """

    format_version: Literal[1] = 1
    """Version of the serialized state format; currently always ``1``."""
    access_token: SecretStr
    """Access token value."""
    access_token_valid_until: datetime
    """When the access token expires."""
    refresh_token: SecretStr
    """Refresh token value."""
    refresh_token_valid_until: datetime
    """When the refresh token expires."""

    @field_validator("access_token", "refresh_token", mode="before")
    @classmethod
    def _reject_missing_or_redacted_tokens(cls, value: object) -> object:
        token = value.get_secret_value() if isinstance(value, SecretStr) else value
        if token in ("", "**********"):
            raise ValueError(
                "Resume state must contain the original bearer token; "
                "use to_json() for explicit sensitive export."
            )
        return value

    @classmethod
    def from_tokens(cls, auth_tokens: AuthTokens) -> Self:
        """Create resume state from authenticated token credentials.

        Args:
            auth_tokens: Access and refresh tokens obtained from authentication.

        Returns:
            Resume state holding both tokens and their expiry times.
        """
        return cls(
            access_token=SecretStr(auth_tokens.access_token.token),
            access_token_valid_until=auth_tokens.access_token.valid_until,
            refresh_token=SecretStr(auth_tokens.refresh_token.token),
            refresh_token_valid_until=auth_tokens.refresh_token.valid_until,
        )

    def to_tokens(self) -> AuthTokens:
        """Return the token model needed to bind authenticated SDK clients.

        Returns:
            The access and refresh tokens with their expiry times.
        """
        return AuthTokens(
            access_token=TokenCredentials(
                token=self.access_token.get_secret_value(),
                valid_until=self.access_token_valid_until,
            ),
            refresh_token=TokenCredentials(
                token=self.refresh_token.get_secret_value(),
                valid_until=self.refresh_token_valid_until,
            ),
        )

    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] | str = "json",
    ) -> dict[str, object]:
        """Export authentication state with bearer credentials included.

        Store and log the result only as protected credential material.

        Args:
            mode: Pydantic dump mode, ``"json"`` for JSON-safe values or ``"python"`` for native types.

        Returns:
            A dictionary containing the plain access and refresh tokens.
        """
        data: dict[str, object] = self.model_dump(mode=mode)
        data["access_token"] = self.access_token.get_secret_value()
        data["refresh_token"] = self.refresh_token.get_secret_value()
        return data

    def to_json(self, *, indent: int | None = None) -> str:
        """Export authentication state as JSON with bearer credentials included.

        Store and log the result only as protected credential material.

        Args:
            indent: Number of spaces to indent nested values; ``None`` for compact output.

        Returns:
            JSON text containing the plain access and refresh tokens.
        """
        data = self.to_dict(mode="json")
        if indent is None:
            return json.dumps(data, separators=(",", ":"))
        return json.dumps(data, indent=indent)

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Restore authentication state from a dictionary exported by ``to_dict()``.

        Args:
            state: Mapping produced by ``to_dict()``.

        Returns:
            The restored authentication state.
        """
        return cls.model_validate(state)

    @classmethod
    def from_json(cls, state: str | bytes | bytearray) -> Self:
        """Restore authentication state from JSON exported by ``to_json()``.

        Args:
            state: JSON text produced by ``to_json()``.

        Returns:
            The restored authentication state.
        """
        return cls.model_validate_json(state)


class RefreshedToken(KSeFBaseModel):
    """Access token returned by the refresh endpoint."""

    access_token: TokenCredentials
    """New access token."""
