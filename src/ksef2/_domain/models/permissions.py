"""Domain models for permission grants, queries, and operation status."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, BaseModel

from ksef2._domain.models.base import KSeFBaseModel

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
    "collective_identifier_manage",
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
    "collective_identifier_manage",
]

type EntityPermissionType = Literal[
    "invoice_read", "invoice_write", "collective_identifier_manage"
]

type AuthorizationPermissionType = Literal[
    "self_invoicing", "rr_invoicing", "tax_representative", "pef_invoicing"
]

type AuthorizationSubjectIdentifierType = Literal["nip", "peppol_id"]

type IndirectPermissionType = Literal[
    "invoice_read", "invoice_write", "collective_identifier_manage"
]

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
    COLLECTIVE_IDENTIFIER_MANAGE = "collective_identifier_manage"


class EntityPermissionTypeEnum(StrEnum):
    """Runtime enum for entity permission scopes."""

    INVOICE_READ = "invoice_read"
    INVOICE_WRITE = "invoice_write"
    COLLECTIVE_IDENTIFIER_MANAGE = "collective_identifier_manage"


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
    COLLECTIVE_IDENTIFIER_MANAGE = "collective_identifier_manage"


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
    """Permission scope granted to the entity."""
    can_delegate: bool = False
    """Whether the holder may delegate this permission further."""


class GrantPermissionsResponse(KSeFBaseModel):
    """Reference returned after starting a permission grant or revoke operation."""

    reference_number: str
    """KSeF reference number of the operation or resource."""


class GrantPersonPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions directly to a person."""

    subject_type: CertificateSubjectIdentifierType
    """Kind of identifier in ``subject_value`` (``nip``, ``pesel`` or ``fingerprint``)."""
    subject_value: str
    """Identifier of the person receiving the permissions (NIP, PESEL or certificate fingerprint)."""
    permissions: list[PersonPermissionScope]
    """Permission scopes to grant; at least one is required."""
    description: str
    """Free-text reason for the grant, stored by KSeF with the permission."""
    first_name: str
    """First name of the person receiving the permissions."""
    last_name: str
    """Last name of the person receiving the permissions."""


class GrantEntityPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions to an entity."""

    subject_value: str
    """NIP of the entity receiving the permissions."""
    permissions: list[EntityPermission]
    """Permissions to grant, each with its delegation flag."""
    description: str
    """Free-text reason for the grant, stored by KSeF with the permission."""
    entity_name: str
    """Full name of the entity receiving the permissions."""


class GrantAuthorizationPermissionsRequest(KSeFBaseModel):
    """Payload for granting invoice authorization rights to an entity."""

    subject_type: AuthorizationSubjectIdentifierType
    """Kind of identifier in ``subject_value`` (``nip`` or ``peppol_id``)."""
    subject_value: str
    """Identifier of the entity being authorized (NIP or Peppol ID)."""
    permission: AuthorizationPermissionType
    """Authorization scope to grant, for example ``self_invoicing``."""
    description: str
    """Free-text reason for the grant, stored by KSeF with the permission."""
    entity_name: str
    """Full name of the entity being authorized."""


class GrantIndirectPermissionsRequest(KSeFBaseModel):
    """Payload for granting indirect permissions, optionally scoped to a target."""

    subject_type: CertificateSubjectIdentifierType
    """Kind of identifier in ``subject_value`` (``nip``, ``pesel`` or ``fingerprint``)."""
    subject_value: str
    """Identifier of the person receiving the indirect permissions."""
    permissions: list[IndirectPermissionType]
    """Indirect permission scopes to grant; at least one is required."""
    description: str
    """Free-text reason for the grant, stored by KSeF with the permission."""
    first_name: str
    """First name of the person receiving the permissions."""
    last_name: str
    """Last name of the person receiving the permissions."""
    target_type: IndirectTargetIdentifierType | None = None
    """Kind of identifier in ``target_value``; ``None`` or ``all_partners`` scopes the grant to every partner."""
    target_value: str | None = None
    """Identifier of the partner context the grant is limited to; ``None`` when the target is all partners."""


class GrantSubunitPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions in a subunit context."""

    subject_type: CertificateSubjectIdentifierType
    """Kind of identifier in ``subject_value`` (``nip``, ``pesel`` or ``fingerprint``)."""
    subject_value: str
    """Identifier of the person receiving the permissions."""
    context_type: SubunitIdentifierType
    """Kind of identifier in ``context_value`` (``nip`` or ``internal_id``)."""
    context_value: str
    """Identifier of the subunit context the permissions apply to."""
    description: str
    """Free-text reason for the grant, stored by KSeF with the permission."""
    first_name: str
    """First name of the person receiving the permissions."""
    last_name: str
    """Last name of the person receiving the permissions."""
    subunit_name: str | None = None
    """Display name of the subunit; optional."""


class GrantEuEntityPermissionsRequest(KSeFBaseModel):
    """Payload for granting permissions to an EU entity."""

    subject_value: str
    """Fingerprint of the certificate of the person receiving the permissions."""
    permissions: list[EuEntityPermissionType]
    """EU-entity permission scopes to grant."""
    description: str
    """Free-text reason for the grant, stored by KSeF with the permission."""


class GrantEuEntityAdministrationRequest(KSeFBaseModel):
    """Payload for granting EU-entity administration rights in a VAT UE context."""

    subject_value: str
    """Fingerprint of the certificate of the person receiving administration rights."""
    context_type: EuEntityAdminContextIdentifierType
    """Kind of identifier in ``context_value``; always ``nip_vat_ue``."""
    context_value: str
    """NIP-VAT UE identifier of the EU entity the rights apply to."""
    description: str
    """Free-text reason for the grant, stored by KSeF with the permission."""
    eu_entity_name: str
    """Full name of the EU entity."""


# ---------------------------------------------------------------------------
# Status models
# ---------------------------------------------------------------------------


class OperationStatus(KSeFBaseModel):
    """Operation status code and description returned by asynchronous permission APIs."""

    code: OperationStatusCode
    """Numeric status code; ``200`` means the operation completed successfully, ``100`` that it is still in progress."""
    description: str
    """Human-readable description of the status."""


class PermissionOperationStatusResponse(KSeFBaseModel):
    """Status wrapper for a permission grant or revoke operation."""

    status: OperationStatus
    """Current status of the operation."""


class AttachmentPermissionStatus(KSeFBaseModel):
    """Current attachment availability for the authenticated subject."""

    is_attachment_allowed: bool
    """Whether the subject may currently send invoices with attachments."""
    revoked_date: datetime | None = None
    """When attachment permission was or will be revoked; ``None`` if it is not scheduled for revocation."""


# ---------------------------------------------------------------------------
# Entity roles
# ---------------------------------------------------------------------------


class EntityRole(KSeFBaseModel):
    """Role assigned to the authenticated entity, optionally within a parent entity."""

    role: EntityRoleType
    """Role assigned to the entity."""
    description: str
    """Human-readable description of the role."""
    start_date: datetime
    """When the role became effective."""
    parent_entity_id_type: EntityIdentifierType | None = None
    """Kind of identifier of the parent entity; ``None`` when the role has no parent."""
    parent_entity_id_value: str | None = None
    """Identifier of the parent entity; ``None`` when the role has no parent."""


class EntityRolesResponse(KSeFBaseModel):
    """One page of entity roles."""

    roles: list[EntityRole]
    """Roles on this page."""
    has_more: bool
    """Whether more results are available after this page."""


# ---------------------------------------------------------------------------
# Query: entities
# ---------------------------------------------------------------------------


class EntityPermissionsQuery(KSeFBaseModel):
    """Filters for querying entity permission grants in the current context."""

    context_type: EntityPermissionsContextIdentifierType | None = None
    """Restrict results to this kind of context identifier; ``None`` for no restriction."""
    context_value: str | None = None
    """Restrict results to this context identifier; ``None`` for no restriction."""


class EntityPermissionDetail(KSeFBaseModel):
    """Permission record returned from entity permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    """Permission identifier (36-character UUID), usable for revocation."""
    context_type: EntityPermissionsContextIdentifierType
    """Kind of identifier in ``context_value``."""
    context_value: str
    """Identifier of the context in which the permission applies."""
    permission_type: EntityPermissionType
    """Permission scope."""
    description: str
    """Reason recorded when the permission was granted."""
    start_date: datetime
    """When the permission became effective."""
    can_delegate: bool
    """Whether the holder may delegate this permission further."""


class EntityPermissionsQueryResponse(KSeFBaseModel):
    """One page of entity permission query results."""

    permissions: list[EntityPermissionDetail]
    """Permission records on this page."""
    has_more: bool
    """Whether more results are available after this page."""


# ---------------------------------------------------------------------------
# Query: persons
# ---------------------------------------------------------------------------


class PersonPermissionsQuery(KSeFBaseModel):
    """Filters for querying person-related permission grants."""

    query_type: PersonPermissionsQueryType
    """Direction of the query: ``in_context`` (held in the current context) or ``granted_in_context`` (granted by the current context)."""
    permission_types: list[PersonPermissionScope] | None = None
    """Restrict results to these permission scopes; ``None`` for all."""
    permission_state: PermissionState | None = None
    """Restrict results to ``active`` or ``inactive`` permissions; ``None`` for both."""
    author_type: PersonAuthorIdentifierType | None = None
    """Kind of identifier in ``author_value``."""
    author_value: str | None = None
    """Restrict results to permissions granted by this author."""
    authorized_type: PersonPermissionsAuthorizedIdentifierType | None = None
    """Kind of identifier in ``authorized_value``."""
    authorized_value: str | None = None
    """Restrict results to permissions held by this person."""
    context_type: PersonPermissionsContextIdentifierType | None = None
    """Kind of identifier in ``context_value``."""
    context_value: str | None = None
    """Restrict results to this context identifier."""
    target_type: PersonPermissionsTargetIdentifierType | None = None
    """Kind of identifier in ``target_value``."""
    target_value: str | None = None
    """Restrict results to permissions scoped to this target."""


class PersonPermissionDetail(KSeFBaseModel):
    """Permission record returned from person permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    """Permission identifier (36-character UUID), usable for revocation."""
    author_type: PersonAuthorIdentifierType | None = None
    """Kind of identifier in ``author_value``."""
    author_value: str | None = None
    """Identifier of the author who granted the permission."""
    authorized_type: PersonPermissionsAuthorizedIdentifierType | None = None
    """Kind of identifier in ``authorized_value``."""
    authorized_value: str | None = None
    """Identifier of the person holding the permission."""
    context_type: PersonPermissionsContextIdentifierType | None = None
    """Kind of identifier in ``context_value``."""
    context_value: str | None = None
    """Identifier of the context in which the permission applies."""
    target_type: PersonPermissionsTargetIdentifierType | None = None
    """Kind of identifier in ``target_value``."""
    target_value: str | None = None
    """Identifier of the target the permission is scoped to, if any."""
    permission_state: PermissionState
    """Whether the permission is ``active`` or ``inactive``."""
    permission_type: PersonPermissionScope
    """Permission scope."""
    description: str
    """Reason recorded when the permission was granted."""
    start_date: datetime
    """When the permission became effective."""
    can_delegate: bool
    """Whether the holder may delegate this permission further."""
    person_first_name: str | None = None
    """First name of the person holding the permission, if known."""
    person_last_name: str | None = None
    """Last name of the person holding the permission, if known."""
    entity_first_name: str | None = None
    """First name of the entity owner holding the permission, if the entity is a natural person."""
    entity_last_name: str | None = None
    """Last name of the entity owner holding the permission, if the entity is a natural person."""


class PersonPermissionsQueryResponse(KSeFBaseModel):
    """One page of person permission query results."""

    permissions: list[PersonPermissionDetail]
    """Permission records on this page."""
    has_more: bool
    """Whether more results are available after this page."""


# ---------------------------------------------------------------------------
# Query: authorizations
# ---------------------------------------------------------------------------


class AuthorizationPermissionsQuery(KSeFBaseModel):
    """Filters for querying authorization grants between entities."""

    query_type: QueryType
    """Whether to list grants ``granted`` by or ``received`` by the current context."""
    permission_types: list[AuthorizationPermissionType] | None = None
    """Restrict results to these authorization scopes; ``None`` for all."""
    authorizing_type: EntityIdentifierType | None = None
    """Kind of identifier in ``authorizing_value``."""
    authorizing_value: str | None = None
    """Restrict results to grants given by this entity (NIP)."""
    authorized_type: AuthorizationSubjectIdentifierType | None = None
    """Kind of identifier in ``authorized_value``."""
    authorized_value: str | None = None
    """Restrict results to grants received by this entity."""


class AuthorizationGrantDetail(KSeFBaseModel):
    """Authorization grant returned from authorization queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    """Grant identifier (36-character UUID), usable for revocation."""
    author_type: CertificateSubjectIdentifierType | None = None
    """Kind of identifier in ``author_value``."""
    author_value: str | None = None
    """Identifier of the person who created the grant."""
    authorized_entity_type: AuthorizationSubjectIdentifierType
    """Kind of identifier in ``authorized_entity_value``."""
    authorized_entity_value: str
    """Identifier of the entity that received the authorization."""
    authorizing_entity_type: EntityIdentifierType
    """Kind of identifier in ``authorizing_entity_value``."""
    authorizing_entity_value: str
    """Identifier of the entity that gave the authorization."""
    authorization_scope: AuthorizationPermissionType
    """Authorization scope that was granted."""
    description: str
    """Reason recorded when the grant was created."""
    entity_full_name: str | None = None
    """Full name of the authorized entity, if known."""
    start_date: datetime
    """When the grant became effective."""


class AuthorizationPermissionsQueryResponse(KSeFBaseModel):
    """One page of authorization grant query results."""

    authorization_grants: list[AuthorizationGrantDetail]
    """Authorization grants on this page."""
    has_more: bool
    """Whether more results are available after this page."""


# ---------------------------------------------------------------------------
# Query: personal
# ---------------------------------------------------------------------------


class PersonalPermissionsQuery(KSeFBaseModel):
    """Filters for querying permissions held by the authenticated subject."""

    permission_types: list[PersonalPermissionScope] | None = None
    """Restrict results to these permission scopes; ``None`` for all."""
    permission_state: PermissionState | None = None
    """Restrict results to ``active`` or ``inactive`` permissions; ``None`` for both."""
    context_type: PersonalPermissionsContextIdentifierType | None = None
    """Kind of identifier in ``context_value``."""
    context_value: str | None = None
    """Restrict results to this context identifier."""
    target_type: PersonalPermissionsTargetIdentifierType | None = None
    """Kind of identifier in ``target_value``."""
    target_value: str | None = None
    """Restrict results to permissions scoped to this target."""


class PersonalPermissionDetail(KSeFBaseModel):
    """Permission record returned from personal permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    """Permission identifier (36-character UUID)."""
    context_type: PersonalPermissionsContextIdentifierType | None = None
    """Kind of identifier in ``context_value``."""
    context_value: str | None = None
    """Identifier of the context in which the permission applies."""
    authorized_type: PersonalPermissionsAuthorizedIdentifierType | None = None
    """Kind of identifier in ``authorized_value``."""
    authorized_value: str | None = None
    """Identifier of the subject holding the permission."""
    target_type: PersonalPermissionsTargetIdentifierType | None = None
    """Kind of identifier in ``target_value``."""
    target_value: str | None = None
    """Identifier of the target the permission is scoped to, if any."""
    permission_type: PersonalPermissionScope
    """Permission scope."""
    description: str
    """Reason recorded when the permission was granted."""
    subject_first_name: str | None = None
    """First name of the subject holding the permission, if known."""
    subject_last_name: str | None = None
    """Last name of the subject holding the permission, if known."""
    entity_first_name: str | None = None
    """First name of the entity owner, if the entity is a natural person."""
    entity_address: str | None = None
    """Address of the entity the permission applies to, if known."""
    permission_state: PermissionState
    """Whether the permission is ``active`` or ``inactive``."""
    start_date: datetime
    """When the permission became effective."""
    can_delegate: bool
    """Whether the holder may delegate this permission further."""


class PersonalPermissionsQueryResponse(KSeFBaseModel):
    """One page of personal permission query results."""

    permissions: list[PersonalPermissionDetail]
    """Permission records on this page."""
    has_more: bool
    """Whether more results are available after this page."""


# ---------------------------------------------------------------------------
# Query: EU entities
# ---------------------------------------------------------------------------


class EuEntityPermissionsQuery(KSeFBaseModel):
    """Filters for querying EU-entity permissions."""

    vat_ue_identifier: str | None = None
    """Restrict results to this NIP-VAT UE identifier."""
    authorized_fingerprint_identifier: str | None = None
    """Restrict results to permissions held by the certificate with this fingerprint."""
    permission_types: list[EuEntityQueryPermissionType] | None = None
    """Restrict results to these permission scopes; ``None`` for all."""


class EuEntityPermission(KSeFBaseModel):
    """Permission record returned from EU-entity permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    """Permission identifier (36-character UUID)."""
    author_type: CertificateSubjectIdentifierType
    """Kind of identifier in ``author_value``."""
    author_value: str
    """Identifier of the author who granted the permission."""
    vat_ue_identifier: str
    """NIP-VAT UE identifier of the EU entity."""
    eu_entity_name: str
    """Full name of the EU entity."""
    authorized_fingerprint_identifier: str
    """Fingerprint of the certificate holding the permission."""
    permission_type: EuEntityQueryPermissionType
    """Permission scope."""
    description: str
    """Reason recorded when the permission was granted."""
    subject_first_name: str | None = None
    """First name of the person holding the permission, if known."""
    subject_last_name: str | None = None
    """Last name of the person holding the permission, if known."""
    entity_full_name: str | None = None
    """Full name of the entity the permission belongs to, if known."""
    entity_address: str | None = None
    """Address of the entity the permission belongs to, if known."""
    start_date: datetime
    """When the permission became effective."""


class EuEntityPermissionsQueryResponse(KSeFBaseModel):
    """One page of EU-entity permission query results."""

    permissions: list[EuEntityPermission]
    """Permission records on this page."""
    has_more: bool
    """Whether more results are available after this page."""


# ---------------------------------------------------------------------------
# Query: subordinate entities
# ---------------------------------------------------------------------------


class SubordinateEntityRolesQuery(KSeFBaseModel):
    """Filters for querying subordinate entity roles."""

    subordinate_nip: str | None = None
    """Restrict results to this subordinate entity NIP; ``None`` for all."""


class SubordinateEntityRoleDetail(KSeFBaseModel):
    """Role record returned from subordinate-entity role queries."""

    subordinate_entity_type: EntityIdentifierType
    """Kind of identifier in ``subordinate_entity_value``."""
    subordinate_entity_value: str
    """Identifier of the subordinate entity."""
    role: SubordinateEntityRoleType
    """Role of the subordinate entity."""
    description: str
    """Human-readable description of the role."""
    start_date: datetime
    """When the role became effective."""


class SubordinateEntityRolesQueryResponse(KSeFBaseModel):
    """One page of subordinate entity role query results."""

    roles: list[SubordinateEntityRoleDetail]
    """Roles on this page."""
    has_more: bool
    """Whether more results are available after this page."""


# ---------------------------------------------------------------------------
# Query: subunits
# ---------------------------------------------------------------------------


class SubunitPermissionsQuery(KSeFBaseModel):
    """Filters for querying permissions assigned to subunits."""

    subunit_nip: str | None = None
    """Restrict results to this subunit NIP; ``None`` for all."""


class SubunitPermission(KSeFBaseModel):
    """Permission record returned from subunit permission queries."""

    id: Annotated[str, Field(max_length=36, min_length=36)]
    """Permission identifier (36-character UUID)."""
    authorized_type: CertificateSubjectIdentifierType
    """Kind of identifier in ``authorized_value``."""
    authorized_value: str
    """Identifier of the person holding the permission."""
    subunit_type: SubunitIdentifierType
    """Kind of identifier in ``subunit_value``."""
    subunit_value: str
    """Identifier of the subunit."""
    author_type: CertificateSubjectIdentifierType
    """Kind of identifier in ``author_value``."""
    author_value: str
    """Identifier of the author who granted the permission."""
    permission_type: PersonPermissionScope
    """Permission scope."""
    description: str
    """Reason recorded when the permission was granted."""
    subject_first_name: str | None = None
    """First name of the person holding the permission, if known."""
    subject_last_name: str | None = None
    """Last name of the person holding the permission, if known."""
    entity_first_name: str | None = None
    """First name of the entity owner, if the entity is a natural person."""
    entity_last_name: str | None = None
    """Last name of the entity owner, if the entity is a natural person."""
    subunit_name: str | None = None
    """Display name of the subunit, if known."""
    start_date: datetime
    """When the permission became effective."""


class SubunitPermissionsQueryResponse(KSeFBaseModel):
    """One page of subunit permission query results."""

    permissions: list[SubunitPermission]
    """Permission records on this page."""
    has_more: bool
    """Whether more results are available after this page."""


class ItemsListResponse[ItemT: BaseModel](KSeFBaseModel):
    """Generic paginated item-list response."""

    items: list[ItemT]
    """Items on this page."""
    has_more: bool
    """Whether more results are available after this page."""
