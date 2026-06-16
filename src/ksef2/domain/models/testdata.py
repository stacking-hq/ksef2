"""Domain models for the TEST-only data seeding endpoints."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime

from ksef2.domain.models.base import KSeFBaseModel

type SubjectType = Literal["enforcement_authority", "vat_group", "jst"]
type IdentifierType = Literal["nip", "pesel", "fingerprint", "system"]
type AuthContextIdentifierType = Literal[
    "nip", "internal_id", "nip_vat_ue", "peppol_id"
]
type PermissionType = Literal[
    "invoice_read",
    "invoice_write",
    "pef_invoice_write",
    "introspection",
    "credentials_read",
    "credentials_manage",
    "enforcement_operations",
    "subunit_manage",
    "vat_ue_manage",
]


class SubjectTypeEnum(StrEnum):
    """Runtime enum for TEST subject types."""

    ENFORCEMENT_AUTHORITY = "enforcement_authority"
    VAT_GROUP = "vat_group"
    JST = "jst"


class IdentifierTypeEnum(StrEnum):
    """Runtime enum for TEST data identifier types."""

    NIP = "nip"
    PESEL = "pesel"
    FINGERPRINT = "fingerprint"
    SYSTEM = "system"


class AuthContextIdentifierTypeEnum(StrEnum):
    """Runtime enum for TEST authentication context identifiers."""

    NIP = "nip"
    INTERNAL_ID = "internal_id"
    NIP_VAT_UE = "nip_vat_ue"
    PEPPOL_ID = "peppol_id"


class PermissionTypeEnum(StrEnum):
    """Runtime enum for TEST permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"
    PEF_INVOICE_WRITE = "pef_invoice_write"
    INTROSPECTION = "introspection"
    CREDENTIALS_READ = "credentials_read"
    CREDENTIALS_MANAGE = "credentials_manage"
    ENFORCEMENT_OPERATIONS = "enforcement_operations"
    SUBUNIT_MANAGE = "subunit_manage"
    VAT_UE_MANAGE = "vat_ue_manage"


class SubUnit(KSeFBaseModel):
    """Subunit belonging to a TEST subject."""

    subject_nip: str
    description: str


class Identifier(KSeFBaseModel):
    """Generic subject identifier used in testdata operations."""

    type: IdentifierType
    value: str


class AuthContextIdentifier(KSeFBaseModel):
    """Authentication context identifier used for blocking and unblocking access."""

    type: AuthContextIdentifierType
    value: str


class Permission(KSeFBaseModel):
    """Permission granted through the testdata helper endpoints."""

    type: PermissionType
    description: str


class CreateSubjectRequest(KSeFBaseModel):
    """Payload used to create a test subject."""

    subject_nip: str
    subject_type: SubjectType
    description: str
    subunits: list[SubUnit] | None = None
    created_date: AwareDatetime | None = None


class DeleteSubjectRequest(KSeFBaseModel):
    """Payload used to delete a TEST subject."""

    subject_nip: str


class CreatePersonRequest(KSeFBaseModel):
    """Payload used to create a test person within a subject."""

    nip: str
    pesel: str
    description: str
    is_bailiff: bool = False
    is_deceased: bool = False
    created_date: AwareDatetime | None = None


class DeletePersonRequest(KSeFBaseModel):
    """Payload used to delete a TEST person."""

    nip: str


class GrantPermissionsRequest(KSeFBaseModel):
    """Payload used to grant test permissions in a chosen context."""

    permissions: list[Permission]
    grant_to: Identifier
    in_context_of: Identifier


class RevokePermissionsRequest(KSeFBaseModel):
    """Payload used to revoke TEST permissions in a chosen context."""

    revoke_from: Identifier
    in_context_of: Identifier


class EnableAttachmentsRequest(KSeFBaseModel):
    """Payload used to enable attachments for a TEST subject."""

    nip: str


class RevokeAttachmentsRequest(KSeFBaseModel):
    """Payload used to schedule or perform attachment revocation."""

    nip: str
    expected_end_date: date | None = None


class BlockContextRequest(KSeFBaseModel):
    """Payload used to block authentication for a TEST context."""

    context: AuthContextIdentifier


class UnblockContextRequest(KSeFBaseModel):
    """Payload used to unblock authentication for a TEST context."""

    context: AuthContextIdentifier
