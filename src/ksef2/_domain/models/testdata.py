"""Domain models for the TEST-only data seeding endpoints."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime

from ksef2._domain.models.base import KSeFBaseModel

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
    "collective_identifier_manage",
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
    COLLECTIVE_IDENTIFIER_MANAGE = "collective_identifier_manage"


class SubUnit(KSeFBaseModel):
    """Subunit belonging to a TEST subject."""

    subject_nip: str
    """NIP of the subunit."""
    description: str
    """Description of the subunit."""


class Identifier(KSeFBaseModel):
    """Generic subject identifier used in testdata operations."""

    type: IdentifierType
    """Kind of identifier in ``value``."""
    value: str
    """Identifier value."""


class AuthContextIdentifier(KSeFBaseModel):
    """Authentication context identifier used for blocking and unblocking access."""

    type: AuthContextIdentifierType
    """Kind of identifier in ``value``."""
    value: str
    """Identifier of the authentication context."""


class Permission(KSeFBaseModel):
    """Permission granted through the testdata helper endpoints."""

    type: PermissionType
    """Permission scope."""
    description: str
    """Description stored with the permission."""


class CreateSubjectRequest(KSeFBaseModel):
    """Payload used to create a test subject."""

    subject_nip: str
    """NIP of the subject to create."""
    subject_type: SubjectType
    """Kind of subject, such as an enforcement authority or a VAT group."""
    description: str
    """Description of the subject."""
    subunits: list[SubUnit] | None = None
    """Subunits to create with the subject; ``None`` for none."""
    created_date: AwareDatetime | None = None
    """Creation date to record for the subject; ``None`` for now."""


class DeleteSubjectRequest(KSeFBaseModel):
    """Payload used to delete a TEST subject."""

    subject_nip: str
    """NIP of the subject to delete."""


class CreatePersonRequest(KSeFBaseModel):
    """Payload used to create a test person within a subject."""

    nip: str
    """NIP of the person."""
    pesel: str
    """PESEL of the person."""
    description: str
    """Description of the person."""
    is_bailiff: bool = False
    """Whether the person is a bailiff."""
    is_deceased: bool = False
    """Whether the person is marked as deceased."""
    created_date: AwareDatetime | None = None
    """Creation date to record for the person; ``None`` for now."""


class DeletePersonRequest(KSeFBaseModel):
    """Payload used to delete a TEST person."""

    nip: str
    """NIP of the person to delete."""


class GrantPermissionsRequest(KSeFBaseModel):
    """Payload used to grant test permissions in a chosen context."""

    permissions: list[Permission]
    """Permissions to grant."""
    grant_to: Identifier
    """Identifier of the subject receiving the permissions."""
    in_context_of: Identifier
    """Identifier of the context in which the permissions apply."""


class RevokePermissionsRequest(KSeFBaseModel):
    """Payload used to revoke TEST permissions in a chosen context."""

    revoke_from: Identifier
    """Identifier of the subject losing the permissions."""
    in_context_of: Identifier
    """Identifier of the context from which the permissions are revoked."""


class EnableAttachmentsRequest(KSeFBaseModel):
    """Payload used to enable attachments for a TEST subject."""

    nip: str
    """NIP of the subject to enable attachments for."""


class RevokeAttachmentsRequest(KSeFBaseModel):
    """Payload used to schedule or perform attachment revocation."""

    nip: str
    """NIP of the subject to revoke attachments for."""
    expected_end_date: date | None = None
    """Date on which attachment permission should end; ``None`` to revoke immediately."""


class BlockContextRequest(KSeFBaseModel):
    """Payload used to block authentication for a TEST context."""

    context: AuthContextIdentifier
    """Authentication context to block."""


class UnblockContextRequest(KSeFBaseModel):
    """Payload used to unblock authentication for a TEST context."""

    context: AuthContextIdentifier
    """Authentication context to unblock."""


class UpdateCertificateRequest(KSeFBaseModel):
    """Payload used to shorten a TEST certificate's validity."""

    valid_to: AwareDatetime
    """New, earlier end of the certificate validity period."""
