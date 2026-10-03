"""Domain models for KSeF authentication tokens."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field

from ksef2._domain.models.base import KSeFBaseModel

type TokenPermission = Literal[
    "invoice_read",
    "invoice_write",
    "introspection",
    "credentials_read",
    "credentials_manage",
    "subunit_manage",
    "enforcement_operations",
    "collective_identifier_manage",
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
    COLLECTIVE_IDENTIFIER_MANAGE = "collective_identifier_manage"


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
    """Kind of identifier in ``value``."""
    value: str
    """Identifier of the subject that created the token."""


class TokenContextIdentifier(KSeFBaseModel):
    """Identifies the taxpayer or organizational context bound to a token."""

    type: TokenContextIdentifierType
    """Kind of identifier in ``value``."""
    value: str
    """Identifier of the context the token is bound to."""


class GenerateTokenResponse(KSeFBaseModel):
    """Token value returned after a successful generate operation."""

    reference_number: str
    """KSeF reference number of the operation or resource."""
    token: str = Field(exclude=True, repr=False)
    """KSeF token value. Returned only once, so store it securely. Excluded from serialization and ``repr``."""

    def to_sensitive_dict(self) -> dict[str, str]:
        """Export the one-time token for deliberately protected persistence.

        Returns:
            A dictionary with the reference number and the plain token.
        """
        return {"reference_number": self.reference_number, "token": self.token}


class TokenStatusResponse(KSeFBaseModel):
    """Current lifecycle status of one token."""

    reference_number: str
    """KSeF reference number of the operation or resource."""
    status: TokenStatus
    """Current lifecycle status of the token."""


class TokenInfo(KSeFBaseModel):
    """Metadata returned when querying tokens."""

    reference_number: str
    """KSeF reference number of the operation or resource."""
    author_identifier: TokenAuthorIdentifier
    """Subject that created the token."""
    context_identifier: TokenContextIdentifier
    """Context the token is bound to."""
    description: str
    """Description given when the token was generated."""
    requested_permissions: list[TokenPermission]
    """Permissions the token was generated with."""
    date_created: datetime
    """When the token was generated."""
    last_use_date: datetime | None
    """When the token was last used; ``None`` if never used."""
    status: TokenStatus
    """Current lifecycle status of the token."""
    status_details: list[str] | None
    """Additional status details, if any."""


class QueryTokensResponse(KSeFBaseModel):
    """A single page of token search results."""

    continuation_token: str | None
    """Opaque token for requesting the next page; ``None`` when there are no more pages."""
    tokens: list[TokenInfo]
    """Tokens on this page."""


class GenerateTokenRequest(KSeFBaseModel):
    """Payload used to request a new KSeF token."""

    permissions: list[TokenPermission]
    """Permissions the token should carry."""
    description: str
    """Description of the token."""


class QueryTokensRequest(KSeFBaseModel):
    """Optional filters for listing tokens."""

    status: list[TokenStatus] | None = None
    """Match tokens in any of these statuses."""
    description: str | None = None
    """Match tokens whose description contains this text."""
    author_identifier: TokenAuthorIdentifier | None = None
    """Match tokens created by this subject."""
    page_size: int | None = None
    """Number of results per page; ``None`` for the server default."""
