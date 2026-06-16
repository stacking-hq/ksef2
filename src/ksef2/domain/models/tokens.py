"""Domain models for KSeF authentication tokens."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from ksef2.domain.models.base import KSeFBaseModel

type TokenPermission = Literal[
    "invoice_read",
    "invoice_write",
    "introspection",
    "credentials_read",
    "credentials_manage",
    "subunit_manage",
    "enforcement_operations",
]

type TokenStatus = Literal["pending", "active", "revoking", "revoked", "failed"]

type TokenAuthorIdentifierType = Literal["nip", "pesel", "fingerprint"]

type TokenContextIdentifierType = Literal[
    "nip", "internal_id", "nip_vat_ue", "peppol_id"
]


class TokenPermissionEnum(StrEnum):
    """Runtime enum for token permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"
    INTROSPECTION = "introspection"
    CREDENTIALS_READ = "credentials_read"
    CREDENTIALS_MANAGE = "credentials_manage"
    SUBUNIT_MANAGE = "subunit_manage"
    ENFORCEMENT_OPERATIONS = "enforcement_operations"


class TokenStatusEnum(StrEnum):
    """Runtime enum for token lifecycle statuses."""

    PENDING = "pending"
    ACTIVE = "active"
    REVOKING = "revoking"
    REVOKED = "revoked"
    FAILED = "failed"


class TokenAuthorIdentifierTypeEnum(StrEnum):
    """Runtime enum for token author identifier types."""

    NIP = "nip"
    PESEL = "pesel"
    FINGERPRINT = "fingerprint"


class TokenContextIdentifierTypeEnum(StrEnum):
    """Runtime enum for token context identifier types."""

    NIP = "nip"
    INTERNAL_ID = "internal_id"
    NIP_VAT_UE = "nip_vat_ue"
    PEPPOL_ID = "peppol_id"


class TokenAuthorIdentifier(KSeFBaseModel):
    """Identifies the subject that created the token."""

    type: TokenAuthorIdentifierType
    value: str


class TokenContextIdentifier(KSeFBaseModel):
    """Identifies the taxpayer or organizational context bound to a token."""

    type: TokenContextIdentifierType
    value: str


class GenerateTokenResponse(KSeFBaseModel):
    """Token value returned after a successful generate operation."""

    reference_number: str
    token: str


class TokenStatusResponse(KSeFBaseModel):
    """Current lifecycle status of one token."""

    reference_number: str
    status: TokenStatus


class TokenInfo(KSeFBaseModel):
    """Metadata returned when querying tokens."""

    reference_number: str
    author_identifier: TokenAuthorIdentifier
    context_identifier: TokenContextIdentifier
    description: str
    requested_permissions: list[TokenPermission]
    date_created: datetime
    last_use_date: datetime | None
    status: TokenStatus
    status_details: list[str] | None


class QueryTokensResponse(KSeFBaseModel):
    """A single page of token search results."""

    continuation_token: str | None
    tokens: list[TokenInfo]


class GenerateTokenRequest(KSeFBaseModel):
    """Payload used to request a new KSeF token."""

    permissions: list[TokenPermission]
    description: str


class QueryTokensRequest(KSeFBaseModel):
    """Optional filters for listing tokens."""

    status: list[TokenStatus] | None = None
    description: str | None = None
    author_identifier: TokenAuthorIdentifier | None = None
    page_size: int | None = None
