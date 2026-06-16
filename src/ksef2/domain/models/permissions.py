"""Domain models for permission grants, queries, and operation status."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, BaseModel

from ksef2.domain.models.base import KSeFBaseModel

# ---------------------------------------------------------------------------
# Type aliases (replace StrEnums)
# ---------------------------------------------------------------------------

type IdentifierType = Literal[
    "nip", "pesel", "fingerprint", "system", "internal_id", "all_partners", "peppol_id"
]

type CertificateSubjectIdentifierType = Literal["nip", "pesel", "fingerprint"]

type PersonAuthorIdentifierType = Literal["nip", "pesel", "fingerprint", "system"]

type PersonContextIdentifierType = Literal["nip", "internal_id"]

type EntityIdentifierType = Literal["nip"]

type EntityPermissionsContextIdentifierType = Literal["nip", "internal_id"]

type PersonPermissionScope = Literal[
    "invoice_read",
    "invoice_write",
    "introspection",
    "credentials_read",
    "credentials_manage",
    "enforcement_operations",
    "subunit_manage",
]

type PersonalPermissionScope = Literal[
    "invoice_read",
    "invoice_write",
    "introspection",
    "credentials_read",
    "credentials_manage",
    "enforcement_operations",
    "subunit_manage",
    "vat_ue_manage",
]

type EntityPermissionType = Literal["invoice_read", "invoice_write"]

type AuthorizationPermissionType = Literal[
    "self_invoicing", "rr_invoicing", "tax_representative", "pef_invoicing"
]

type AuthorizationSubjectIdentifierType = Literal["nip", "peppol_id"]

type IndirectPermissionType = Literal["invoice_read", "invoice_write"]

type IndirectTargetIdentifierType = Literal["nip", "all_partners", "internal_id"]

type SubunitIdentifierType = Literal["nip", "internal_id"]

type EuEntityPermissionType = Literal["invoice_read", "invoice_write"]

type EuEntityAdminContextIdentifierType = Literal["nip_vat_ue"]

type EntityRoleType = Literal[
    "court_bailiff",
    "enforcement_authority",
    "local_government_unit",
    "local_government_sub_unit",
    "vat_group_unit",
    "vat_group_sub_unit",
]

type PermissionState = Literal["active", "inactive"]

type OperationStatusCode = Literal[100, 200, 400, 410, 420, 430, 440, 450, 500, 550]

type QueryType = Literal["granted", "received"]

type PersonPermissionsQueryType = Literal["in_context", "granted_in_context"]

type PersonPermissionsAuthorizedIdentifierType = Literal["nip", "pesel", "fingerprint"]

type PersonPermissionsContextIdentifierType = Literal["nip", "internal_id"]

type PersonPermissionsTargetIdentifierType = Literal[
    "nip", "all_partners", "internal_id"
]

type PersonalPermissionsAuthorizedIdentifierType = Literal[
    "nip", "pesel", "fingerprint"
]

type PersonalPermissionsContextIdentifierType = Literal["nip", "internal_id"]

type PersonalPermissionsTargetIdentifierType = Literal[
    "nip", "all_partners", "internal_id"
]

type SubordinateEntityRoleType = Literal[
    "local_government_sub_unit", "vat_group_sub_unit"
]

type EuEntityQueryPermissionType = Literal[
    "vat_ue_manage", "invoice_write", "invoice_read", "introspection"
]


class IdentifierTypeEnum(StrEnum):
    """Runtime enum for permission identifier types."""

    NIP = "nip"
    PESEL = "pesel"
    FINGERPRINT = "fingerprint"
    SYSTEM = "system"
    INTERNAL_ID = "internal_id"
    ALL_PARTNERS = "all_partners"
    PEPPOL_ID = "peppol_id"


class PersonPermissionTypeEnum(StrEnum):
    """Runtime enum for person permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"
    PEF_INVOICE_WRITE = "pef_invoice_write"
    INTROSPECTION = "introspection"
    CREDENTIALS_READ = "credentials_read"
    CREDENTIALS_MANAGE = "credentials_manage"
    ENFORCEMENT_OPERATIONS = "enforcement_operations"
    SUBUNIT_MANAGE = "subunit_manage"
    VAT_UE_MANAGE = "vat_ue_manage"


class EntityPermissionTypeEnum(StrEnum):
    """Runtime enum for entity permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"


class AuthorizationPermissionTypeEnum(StrEnum):
    """Runtime enum for authorization permission scopes."""

    SELF_INVOICING = "self_invoicing"
    RR_INVOICING = "rr_invoicing"
    TAX_REPRESENTATIVE = "tax_representative"
    PEF_INVOICING = "pef_invoicing"


class AuthorizationSubjectIdentifierTypeEnum(StrEnum):
    """Runtime enum for authorization subject identifier types."""

    NIP = "nip"
    PEPPOL_ID = "peppol_id"


class IndirectPermissionTypeEnum(StrEnum):
    """Runtime enum for indirect permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"


class IndirectTargetIdentifierTypeEnum(StrEnum):
    """Runtime enum for indirect permission target identifiers."""

    NIP = "nip"
    ALL_PARTNERS = "all_partners"
    INTERNAL_ID = "internal_id"


class SubunitIdentifierTypeEnum(StrEnum):
    """Runtime enum for subunit context identifiers."""

    NIP = "nip"
    INTERNAL_ID = "internal_id"


class EuEntityPermissionTypeEnum(StrEnum):
    """Runtime enum for EU-entity permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"


class EuEntityAdminContextIdentifierTypeEnum(StrEnum):
    """Runtime enum for EU-entity administration context identifiers."""

    NIP_VAT_UE = "nip_vat_ue"


class EntityRoleTypeEnum(StrEnum):
    """Runtime enum for entity role values."""

    COURT_BAILIFF = "court_bailiff"
    ENFORCEMENT_AUTHORITY = "enforcement_authority"
    LOCAL_GOVERNMENT_UNIT = "local_government_unit"
    LOCAL_GOVERNMENT_SUB_UNIT = "local_government_sub_unit"
    VAT_GROUP_UNIT = "vat_group_unit"
    VAT_GROUP_SUB_UNIT = "vat_group_sub_unit"


class PermissionStateEnum(StrEnum):
    """Runtime enum for permission state filters."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class QueryTypeEnum(StrEnum):
    """Runtime enum for granted/received permission query directions."""

    GRANTED = "granted"
    RECEIVED = "received"


class PersonPermissionsQueryTypeEnum(StrEnum):
    """Runtime enum for person permission query modes."""

    IN_CONTEXT = "in_context"
    GRANTED_IN_CONTEXT = "granted_in_context"


class SubordinateEntityRoleTypeEnum(StrEnum):
    """Runtime enum for subordinate entity role values."""

    LOCAL_GOVERNMENT_SUB_UNIT = "local_government_sub_unit"
    VAT_GROUP_SUB_UNIT = "vat_group_sub_unit"


class EuEntityQueryPermissionTypeEnum(StrEnum):
    """Runtime enum for EU-entity permission query scopes."""

    VAT_UE_MANAGE = "vat_ue_manage"
    INVOICE_WRITE = "invoice_write"
    INVOICE_READ = "invoice_read"
    INTROSPECTION = "introspection"


class ScopeLiteralEnum(StrEnum):
    """Runtime enum for simple invoice permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"


# ---------------------------------------------------------------------------
# Grant models
# ---------------------------------------------------------------------------


class EntityPermission(KSeFBaseModel):
    """Entity permission scope together with delegation capability."""

    type: EntityPermissionType
    can_delegate: bool = False


class GrantPermissionsResponse(KSeFBaseModel):
    """Reference returned after starting a permission grant or revoke operation."""

    reference_number: str


class GrantPersonPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions directly to a person."""

    subject_type: CertificateSubjectIdentifierType
    subject_value: str
    permissions: list[PersonPermissionScope]
    description: str
    first_name: str
    last_name: str


class GrantEntityPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions to an entity."""

    subject_value: str
    permissions: list[EntityPermission]
    description: str
    entity_name: str


class GrantAuthorizationPermissionsRequest(KSeFBaseModel):
    """Payload for granting invoice authorization rights to an entity."""

    subject_type: AuthorizationSubjectIdentifierType
    subject_value: str
    permission: AuthorizationPermissionType
    description: str
    entity_name: str


class GrantIndirectPermissionsRequest(KSeFBaseModel):
    """Payload for granting indirect permissions, optionally scoped to a target."""

    subject_type: CertificateSubjectIdentifierType
    subject_value: str
    permissions: list[IndirectPermissionType]
    description: str
    first_name: str
    last_name: str
    target_type: IndirectTargetIdentifierType | None = None
    target_value: str | None = None


class GrantSubunitPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions in a subunit context."""

    subject_type: CertificateSubjectIdentifierType
    subject_value: str
    context_type: SubunitIdentifierType
    context_value: str
    description: str
    first_name: str
    last_name: str
    subunit_name: str | None = None


class GrantEuEntityPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions to an EU entity."""

    subject_value: str
    permissions: list[EuEntityPermissionType]
    description: str


class GrantEuEntityAdministrationRequest(KSeFBaseModel):
    """Payload for granting EU-entity administration rights in a VAT UE context."""

    subject_value: str
    context_type: EuEntityAdminContextIdentifierType
    context_value: str
    description: str
    eu_entity_name: str


# ---------------------------------------------------------------------------
# Status models
# ---------------------------------------------------------------------------


class OperationStatus(KSeFBaseModel):
    """Operation status code and description returned by asynchronous permission APIs."""

    code: OperationStatusCode
    description: str


class PermissionOperationStatusResponse(KSeFBaseModel):
    """Status wrapper for a permission grant or revoke operation."""

    status: OperationStatus


class AttachmentPermissionStatus(KSeFBaseModel):
    """Current attachment availability for the authenticated subject."""

    is_attachment_allowed: bool
    revoked_date: datetime | None = None


# ---------------------------------------------------------------------------
# Entity roles
# ---------------------------------------------------------------------------


class EntityRole(KSeFBaseModel):
    """Role assigned to the authenticated entity, optionally within a parent entity."""

    role: EntityRoleType
    description: str
    start_date: datetime
    parent_entity_id_type: EntityIdentifierType | None = None
    parent_entity_id_value: str | None = None


class EntityRolesResponse(KSeFBaseModel):
    """One page of entity roles."""

    roles: list[EntityRole]
    has_more: bool


# ---------------------------------------------------------------------------
# Query: entities
# ---------------------------------------------------------------------------


class EntityPermissionsQuery(KSeFBaseModel):
    """Filters for querying entity permission grants in the current context."""

    context_type: EntityPermissionsContextIdentifierType | None = None
    context_value: str | None = None


class EntityPermissionDetail(KSeFBaseModel):
    """Permission record returned from entity permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    context_type: EntityPermissionsContextIdentifierType
    context_value: str
    permission_type: EntityPermissionType
    description: str
    start_date: datetime
    can_delegate: bool


class EntityPermissionsQueryResponse(KSeFBaseModel):
    """One page of entity permission query results."""

    permissions: list[EntityPermissionDetail]
    has_more: bool


# ---------------------------------------------------------------------------
# Query: persons
# ---------------------------------------------------------------------------


class PersonPermissionsQuery(KSeFBaseModel):
    """Filters for querying person-related permission grants."""

    query_type: PersonPermissionsQueryType
    permission_types: list[PersonPermissionScope] | None = None
    permission_state: PermissionState | None = None
    author_type: PersonAuthorIdentifierType | None = None
    author_value: str | None = None
    authorized_type: PersonPermissionsAuthorizedIdentifierType | None = None
    authorized_value: str | None = None
    context_type: PersonPermissionsContextIdentifierType | None = None
    context_value: str | None = None
    target_type: PersonPermissionsTargetIdentifierType | None = None
    target_value: str | None = None


class PersonPermissionDetail(KSeFBaseModel):
    """Permission record returned from person permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    author_type: PersonAuthorIdentifierType | None = None
    author_value: str | None = None
    authorized_type: PersonPermissionsAuthorizedIdentifierType | None = None
    authorized_value: str | None = None
    context_type: PersonPermissionsContextIdentifierType | None = None
    context_value: str | None = None
    target_type: PersonPermissionsTargetIdentifierType | None = None
    target_value: str | None = None
    permission_state: PermissionState
    permission_type: PersonPermissionScope
    description: str
    start_date: datetime
    can_delegate: bool
    person_first_name: str | None = None
    person_last_name: str | None = None
    entity_first_name: str | None = None
    entity_last_name: str | None = None


class PersonPermissionsQueryResponse(KSeFBaseModel):
    """One page of person permission query results."""

    permissions: list[PersonPermissionDetail]
    has_more: bool


# ---------------------------------------------------------------------------
# Query: authorizations
# ---------------------------------------------------------------------------


class AuthorizationPermissionsQuery(KSeFBaseModel):
    """Filters for querying authorization grants between entities."""

    query_type: QueryType
    permission_types: list[AuthorizationPermissionType] | None = None
    authorizing_type: EntityIdentifierType | None = None
    authorizing_value: str | None = None
    authorized_type: AuthorizationSubjectIdentifierType | None = None
    authorized_value: str | None = None


class AuthorizationGrantDetail(KSeFBaseModel):
    """Authorization grant returned from authorization queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    author_type: CertificateSubjectIdentifierType | None = None
    author_value: str | None = None
    authorized_entity_type: AuthorizationSubjectIdentifierType
    authorized_entity_value: str
    authorizing_entity_type: EntityIdentifierType
    authorizing_entity_value: str
    authorization_scope: AuthorizationPermissionType
    description: str
    entity_full_name: str | None = None
    start_date: datetime


class AuthorizationPermissionsQueryResponse(KSeFBaseModel):
    """One page of authorization grant query results."""

    authorization_grants: list[AuthorizationGrantDetail]
    has_more: bool


# ---------------------------------------------------------------------------
# Query: personal
# ---------------------------------------------------------------------------


class PersonalPermissionsQuery(KSeFBaseModel):
    """Filters for querying permissions held by the authenticated subject."""

    permission_types: list[PersonalPermissionScope] | None = None
    permission_state: PermissionState | None = None
    context_type: PersonalPermissionsContextIdentifierType | None = None
    context_value: str | None = None
    target_type: PersonalPermissionsTargetIdentifierType | None = None
    target_value: str | None = None


class PersonalPermissionDetail(KSeFBaseModel):
    """Permission record returned from personal permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    context_type: PersonalPermissionsContextIdentifierType | None = None
    context_value: str | None = None
    authorized_type: PersonalPermissionsAuthorizedIdentifierType | None = None
    authorized_value: str | None = None
    target_type: PersonalPermissionsTargetIdentifierType | None = None
    target_value: str | None = None
    permission_type: PersonalPermissionScope
    description: str
    subject_first_name: str | None = None
    subject_last_name: str | None = None
    entity_first_name: str | None = None
    entity_address: str | None = None
    permission_state: PermissionState
    start_date: datetime
    can_delegate: bool


class PersonalPermissionsQueryResponse(KSeFBaseModel):
    """One page of personal permission query results."""

    permissions: list[PersonalPermissionDetail]
    has_more: bool


# ---------------------------------------------------------------------------
# Query: EU entities
# ---------------------------------------------------------------------------


class EuEntityPermissionsQuery(KSeFBaseModel):
    """Filters for querying EU-entity permissions."""

    vat_ue_identifier: str | None = None
    authorized_fingerprint_identifier: str | None = None
    permission_types: list[EuEntityQueryPermissionType] | None = None


class EuEntityPermission(KSeFBaseModel):
    """Permission record returned from EU-entity permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    author_type: CertificateSubjectIdentifierType
    author_value: str
    vat_ue_identifier: str
    eu_entity_name: str
    authorized_fingerprint_identifier: str
    permission_type: EuEntityQueryPermissionType
    description: str
    subject_first_name: str | None = None
    subject_last_name: str | None = None
    entity_full_name: str | None = None
    entity_address: str | None = None
    start_date: datetime


class EuEntityPermissionsQueryResponse(KSeFBaseModel):
    """One page of EU-entity permission query results."""

    permissions: list[EuEntityPermission]
    has_more: bool


# ---------------------------------------------------------------------------
# Query: subordinate entities
# ---------------------------------------------------------------------------


class SubordinateEntityRolesQuery(KSeFBaseModel):
    """Filters for querying subordinate entity roles."""

    subordinate_nip: str | None = None


class SubordinateEntityRoleDetail(KSeFBaseModel):
    """Role record returned from subordinate-entity role queries."""

    subordinate_entity_type: EntityIdentifierType
    subordinate_entity_value: str
    role: SubordinateEntityRoleType
    description: str
    start_date: datetime


class SubordinateEntityRolesQueryResponse(KSeFBaseModel):
    """One page of subordinate entity role query results."""

    roles: list[SubordinateEntityRoleDetail]
    has_more: bool


# ---------------------------------------------------------------------------
# Query: subunits
# ---------------------------------------------------------------------------


class SubunitPermissionsQuery(KSeFBaseModel):
    """Filters for querying permissions assigned to subunits."""

    subunit_nip: str | None = None


class SubunitPermission(KSeFBaseModel):
    """Permission record returned from subunit permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    authorized_type: CertificateSubjectIdentifierType
    authorized_value: str
    subunit_type: SubunitIdentifierType
    subunit_value: str
    author_type: CertificateSubjectIdentifierType
    author_value: str
    permission_type: PersonPermissionScope
    description: str
    subject_first_name: str | None = None
    subject_last_name: str | None = None
    entity_first_name: str | None = None
    entity_last_name: str | None = None
    subunit_name: str | None = None
    start_date: datetime


class SubunitPermissionsQueryResponse(KSeFBaseModel):
    """One page of subunit permission query results."""

    permissions: list[SubunitPermission]
    has_more: bool


class ItemsListResponse[ItemT: BaseModel](KSeFBaseModel):
    """Generic paginated item-list response."""

    items: list[ItemT]
    has_more: bool
