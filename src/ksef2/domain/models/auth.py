"""Domain models for authentication flows and auth sessions."""

import json
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import SecretStr

from ksef2.domain.models.base import KSeFBaseModel

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
    context_type: ContextIdentifierType
    context_value: str
    encrypted_token: str
    public_key_id: str | None = None


class ChallengeResponse(KSeFBaseModel):
    """Challenge material returned before token or XAdES authentication starts."""

    challenge: str
    timestamp: datetime
    timestamp_ms: int


class TokenCredentials(KSeFBaseModel):
    """A bearer token together with its expiration time."""

    token: str
    valid_until: datetime


class AuthInitResponse(KSeFBaseModel):
    """Initial authentication response containing the short-lived auth token."""

    reference_number: str
    authentication_token: TokenCredentials


class AuthOperationStatus(KSeFBaseModel):
    """Status of an in-progress authentication operation."""

    start_date: datetime
    authentication_method: AuthenticationMethod
    authentication_method_category: AuthenticationMethodCategory
    authentication_method_code: str
    authentication_method_display_name: str
    status_code: int
    status_description: str
    status_details: list[str] | None = None
    is_token_redeemed: bool | None = None
    last_token_refresh_date: datetime | None = None
    refresh_token_valid_until: datetime | None = None


class AuthenticationSession(KSeFBaseModel):
    """Metadata describing an authentication session visible in session listings."""

    reference_number: str
    start_date: datetime
    authentication_method: AuthenticationMethod
    authentication_method_category: AuthenticationMethodCategory
    authentication_method_code: str
    authentication_method_display_name: str
    status_code: int
    status_description: str
    status_details: list[str] | None = None
    is_token_redeemed: bool | None = None
    last_token_refresh_date: datetime | None = None
    refresh_token_valid_until: datetime | None = None
    is_current: bool | None = None


class AuthenticationSessionsResponse(KSeFBaseModel):
    """A single page of authentication sessions."""

    continuation_token: str | None = None
    items: list[AuthenticationSession]


class AuthTokens(KSeFBaseModel):
    """Access and refresh tokens returned after successful authentication."""

    access_token: TokenCredentials
    refresh_token: TokenCredentials


class AuthenticationResumeState(KSeFBaseModel):
    """Serializable authentication state used to rehydrate an authenticated client.

    Use ``to_json()`` when intentionally exporting resumable JSON containing
    bearer credentials. Normal Pydantic dumps and repr output keep token values
    redacted.
    """

    access_token: SecretStr
    access_token_valid_until: datetime
    refresh_token: SecretStr
    refresh_token_valid_until: datetime

    @classmethod
    def from_tokens(cls, auth_tokens: AuthTokens) -> Self:
        """Create resume state from authenticated token credentials."""
        return cls(
            access_token=SecretStr(auth_tokens.access_token.token),
            access_token_valid_until=auth_tokens.access_token.valid_until,
            refresh_token=SecretStr(auth_tokens.refresh_token.token),
            refresh_token_valid_until=auth_tokens.refresh_token.valid_until,
        )

    def to_tokens(self) -> AuthTokens:
        """Return the token model needed to bind authenticated SDK clients."""
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
        """Export authentication state with bearer credentials included."""
        data: dict[str, object] = self.model_dump(mode=mode)
        data["access_token"] = self.access_token.get_secret_value()
        data["refresh_token"] = self.refresh_token.get_secret_value()
        return data

    def to_json(self, *, indent: int | None = None) -> str:
        """Export authentication state as JSON with bearer credentials included."""
        data = self.to_dict(mode="json")
        if indent is None:
            return json.dumps(data, separators=(",", ":"))
        return json.dumps(data, indent=indent)

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Restore authentication state from a dictionary exported by ``to_dict()``."""
        return cls.model_validate(state)

    @classmethod
    def from_json(cls, state: str | bytes | bytearray) -> Self:
        """Restore authentication state from JSON exported by ``to_json()``."""
        return cls.model_validate_json(state)


class RefreshedToken(KSeFBaseModel):
    """Access token returned by the refresh endpoint."""

    access_token: TokenCredentials
