from datetime import datetime, timezone

from ksef2.domain.models import permissions as domain_permissions
from ksef2.infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

_UUID = "123e4567-e89b-12d3-a456-426614174000"
_START = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


@register_fixture(name="perm_grant_person_req")
class PersonPermissionsGrantRequestFactory(
    ModelFactory[spec.PersonPermissionsGrantRequest]
): ...


@register_fixture(name="perm_grant_entity_req")
class EntityPermissionsGrantRequestFactory(
    ModelFactory[spec.EntityPermissionsGrantRequest]
): ...


@register_fixture(name="perm_grant_auth_req")
class EntityAuthorizationPermissionsGrantRequestFactory(
    ModelFactory[spec.EntityAuthorizationPermissionsGrantRequest]
): ...


@register_fixture(name="perm_grant_indirect_req")
class IndirectPermissionsGrantRequestFactory(
    ModelFactory[spec.IndirectPermissionsGrantRequest]
): ...


@register_fixture(name="perm_grant_subunit_req")
class SubunitPermissionsGrantRequestFactory(
    ModelFactory[spec.SubunitPermissionsGrantRequest]
): ...


@register_fixture(name="perm_grant_eu_admin_req")
class EuEntityAdministrationPermissionsGrantRequestFactory(
    ModelFactory[spec.EuEntityAdministrationPermissionsGrantRequest]
): ...


@register_fixture(name="perm_grant_eu_entity_req")
class EuEntityPermissionsGrantRequestFactory(
    ModelFactory[spec.EuEntityPermissionsGrantRequest]
): ...


@register_fixture(name="perm_op_resp")
class PermissionsOperationResponseFactory(
    ModelFactory[spec.PermissionsOperationResponse]
): ...


@register_fixture(name="perm_query_personal_req")
class PersonalPermissionsQueryRequestFactory(
    ModelFactory[spec.PersonalPermissionsQueryRequest]
): ...


@register_fixture(name="perm_query_personal_resp")
class QueryPersonalPermissionsResponseFactory(
    ModelFactory[spec.QueryPersonalPermissionsResponse]
): ...


@register_fixture(name="perm_attachment_status_resp")
class CheckAttachmentPermissionStatusResponseFactory(
    ModelFactory[spec.CheckAttachmentPermissionStatusResponse]
): ...


@register_fixture(name="perm_query_auth_req")
class EntityAuthorizationPermissionsQueryRequestFactory(
    ModelFactory[spec.EntityAuthorizationPermissionsQueryRequest]
): ...


@register_fixture(name="perm_query_auth_resp")
class QueryEntityAuthorizationPermissionsResponseFactory(
    ModelFactory[spec.QueryEntityAuthorizationPermissionsResponse]
): ...


@register_fixture(name="perm_query_entity_req")
class EntityPermissionsQueryRequestFactory(
    ModelFactory[spec.EntityPermissionsQueryRequest]
): ...


@register_fixture(name="perm_query_entity_resp")
class QueryEntityPermissionsResponseFactory(
    ModelFactory[spec.QueryEntityPermissionsResponse]
): ...


@register_fixture(name="perm_query_eu_entity_req")
class EuEntityPermissionsQueryRequestFactory(
    ModelFactory[spec.EuEntityPermissionsQueryRequest]
): ...


@register_fixture(name="perm_query_eu_entity_resp")
class QueryEuEntityPermissionsResponseFactory(
    ModelFactory[spec.QueryEuEntityPermissionsResponse]
): ...


@register_fixture(name="perm_query_person_req")
class PersonPermissionsQueryRequestFactory(
    ModelFactory[spec.PersonPermissionsQueryRequest]
): ...


@register_fixture(name="perm_query_person_resp")
class QueryPersonPermissionsResponseFactory(
    ModelFactory[spec.QueryPersonPermissionsResponse]
): ...


@register_fixture(name="perm_query_subordinate_req")
class SubordinateEntityRolesQueryRequestFactory(
    ModelFactory[spec.SubordinateEntityRolesQueryRequest]
): ...


@register_fixture(name="perm_query_subordinate_resp")
class QuerySubordinateEntityRolesResponseFactory(
    ModelFactory[spec.QuerySubordinateEntityRolesResponse]
): ...


@register_fixture(name="perm_query_subunit_req")
class SubunitPermissionsQueryRequestFactory(
    ModelFactory[spec.SubunitPermissionsQueryRequest]
): ...


@register_fixture(name="perm_query_subunit_resp")
class QuerySubunitPermissionsResponseFactory(
    ModelFactory[spec.QuerySubunitPermissionsResponse]
): ...


@register_fixture(name="perm_op_status_resp")
class PermissionsOperationStatusResponseFactory(
    ModelFactory[spec.PermissionsOperationStatusResponse]
):
    status = spec.StatusInfo(code=200, description="Accepted", details=["ok"])


@register_fixture(name="perm_entity_roles_resp")
class QueryEntityRolesResponseFactory(ModelFactory[spec.QueryEntityRolesResponse]): ...


@register_fixture(name="perm_person_context_identifier")
class PersonPermissionsContextIdentifierFactory(
    ModelFactory[spec.PersonPermissionsContextIdentifier]
):
    type = spec.PersonPermissionsContextIdentifierType.InternalId
    value = "1234567890-12345"


@register_fixture(name="perm_person_target_identifier")
class PersonPermissionsTargetIdentifierFactory(
    ModelFactory[spec.PersonPermissionsTargetIdentifier]
):
    type = spec.IndirectPermissionsTargetIdentifierType.AllPartners
    value = "1234567890"


@register_fixture(name="perm_personal_context_identifier")
class PersonalPermissionsContextIdentifierFactory(
    ModelFactory[spec.PersonalPermissionsContextIdentifier]
):
    type = spec.PersonalPermissionsContextIdentifierType.InternalId
    value = "1234567890-12345"


@register_fixture(name="perm_personal_authorized_identifier")
class PersonalPermissionsAuthorizedIdentifierFactory(
    ModelFactory[spec.PersonalPermissionsAuthorizedIdentifier]
):
    type = spec.PersonalPermissionsAuthorizedIdentifierType.Nip
    value = "1234567890"


@register_fixture(name="perm_personal_target_identifier")
class PersonalPermissionsTargetIdentifierFactory(
    ModelFactory[spec.PersonalPermissionsTargetIdentifier]
): ...


@register_fixture(name="perm_entity_role_parent_identifier")
class EntityRolesParentEntityIdentifierFactory(
    ModelFactory[spec.EntityRolesParentEntityIdentifier]
): ...


@register_fixture(name="perm_subject_person_details")
class PermissionsSubjectPersonDetailsFactory(
    ModelFactory[spec.PermissionsSubjectPersonDetails]
): ...


@register_fixture(name="perm_subject_entity_details")
class PermissionsSubjectEntityDetailsFactory(
    ModelFactory[spec.PermissionsSubjectEntityDetails]
): ...


@register_fixture(name="perm_subject_entity_by_identifier_details")
class PermissionsSubjectEntityByIdentifierDetailsFactory(
    ModelFactory[spec.PermissionsSubjectEntityByIdentifierDetails]
):
    subjectDetailsType = spec.EntitySubjectByIdentifierDetailsType.EntityByIdentifier
    fullName = "Authorized Entity"


@register_fixture(name="perm_eu_entity_details")
class PermissionsEuEntityDetailsFactory(ModelFactory[spec.PermissionsEuEntityDetails]):
    fullName = "EU Context Entity"
    address = "EU Street 2"


@register_fixture(name="perm_person_item")
class PersonPermissionFactory(ModelFactory[spec.PersonPermission]):
    id = _UUID
    authorIdentifier = spec.PersonPermissionsAuthorIdentifier(
        type=spec.PersonPermissionsAuthorIdentifierType.Nip,
        value="1234567890",
    )
    authorizedIdentifier = spec.PersonPermissionsAuthorizedIdentifier(
        type=spec.CertificateSubjectIdentifierType.Nip,
        value="1234567890",
    )
    permissionScope = spec.PersonPermissionScope.InvoiceRead
    description = "Read invoices"
    permissionState = spec.PermissionState.Active
    startDate = _START
    canDelegate = True


@register_fixture(name="perm_authorization_grant_item")
class EntityAuthorizationGrantFactory(ModelFactory[spec.EntityAuthorizationGrant]):
    id = _UUID
    authorIdentifier = spec.EntityAuthorizationsAuthorIdentifier(
        type=spec.EntityAuthorizationsAuthorIdentifierType.Nip,
        value="1234567890",
    )
    authorizedEntityIdentifier = spec.EntityAuthorizationsAuthorizedEntityIdentifier(
        type=spec.EntityAuthorizationsAuthorizedEntityIdentifierType.Nip,
        value="1234567890",
    )
    authorizingEntityIdentifier = spec.EntityAuthorizationsAuthorizingEntityIdentifier(
        type=spec.EntityAuthorizationsAuthorizingEntityIdentifierType.Nip,
        value="1234567890",
    )
    authorizationScope = spec.InvoicePermissionType.SelfInvoicing
    description = "Authorization"
    startDate = _START


@register_fixture(name="perm_entity_role_item")
class EntityRoleFactory(ModelFactory[spec.EntityRole]):
    role = spec.EntityRoleType.LocalGovernmentUnit
    description = "Entity role"
    startDate = _START


@register_fixture(name="perm_entity_permission_item")
class EntityPermissionItemFactory(ModelFactory[spec.EntityPermissionItem]):
    id = _UUID
    contextIdentifier = spec.EntityPermissionsContextIdentifier(
        type=spec.EntityPermissionsContextIdentifierType.Nip,
        value="1234567890",
    )
    permissionScope = spec.EntityPermissionItemScope.InvoiceRead
    description = "Entity permission"
    startDate = _START
    canDelegate = True


@register_fixture(name="perm_personal_permission_item")
class PersonalPermissionFactory(ModelFactory[spec.PersonalPermission]):
    id = _UUID
    permissionScope = spec.PersonalPermissionScope.VatUeManage
    description = "Personal permission"
    permissionState = spec.PermissionState.Active
    startDate = _START
    canDelegate = True


@register_fixture(name="perm_eu_entity_permission_item")
class EuEntityPermissionFactory(ModelFactory[spec.EuEntityPermission]):
    id = _UUID
    authorIdentifier = spec.EuEntityPermissionsAuthorIdentifier(
        type=spec.EuEntityPermissionsAuthorIdentifierType.Nip,
        value="1234567890",
    )
    vatUeIdentifier = "PL1234567890"
    euEntityName = "Example EU Entity"
    authorizedFingerprintIdentifier = "a" * 64
    permissionScope = spec.EuEntityPermissionsQueryPermissionType.InvoiceRead
    description = "EU permission"
    startDate = _START


@register_fixture(name="perm_subordinate_role_item")
class SubordinateEntityRoleFactory(ModelFactory[spec.SubordinateEntityRole]):
    subordinateEntityIdentifier = spec.SubordinateRoleSubordinateEntityIdentifier(
        type=spec.SubordinateRoleSubordinateEntityIdentifierType.Nip,
        value="1234567890",
    )
    role = spec.SubordinateEntityRoleType.LocalGovernmentSubUnit
    description = "Subordinate role"
    startDate = _START


@register_fixture(name="perm_subunit_permission_item")
class SubunitPermissionFactory(ModelFactory[spec.SubunitPermission]):
    id = _UUID
    authorizedIdentifier = spec.SubunitPermissionsAuthorizedIdentifier(
        type=spec.SubunitPermissionsSubjectIdentifierType.Nip,
        value="1234567890",
    )
    subunitIdentifier = spec.SubunitPermissionsSubunitIdentifier(
        type=spec.SubunitPermissionsSubunitIdentifierType.InternalId,
        value="1234567890-12345",
    )
    authorIdentifier = spec.SubunitPermissionsAuthorIdentifier(
        type=spec.SubunitPermissionsAuthorIdentifierType.Pesel,
        value="12345678901",
    )
    permissionScope = spec.SubunitPermissionScope.CredentialsManage
    description = "Subunit permission"
    subunitName = "Subunit A"
    startDate = _START


# --- factories for domain models ---


@register_fixture(name="domain_perm_grant_person_req")
class DomainGrantPersonPermissionsRequestFactory(
    ModelFactory[domain_permissions.GrantPersonPermissionsRequest]
):
    subject_type: str = "nip"
    subject_value = "1234567890"
    permissions: list[str] = ["invoice_read"]


@register_fixture(name="domain_perm_grant_entity_req")
class DomainGrantEntityPermissionsRequestFactory(
    ModelFactory[domain_permissions.GrantEntityPermissionsRequest]
):
    subject_value = "1234567890"
    permissions: list[domain_permissions.EntityPermission] = [
        domain_permissions.EntityPermission(type="invoice_read", can_delegate=False)
    ]


@register_fixture(name="domain_perm_grant_auth_req")
class DomainGrantAuthorizationPermissionsRequestFactory(
    ModelFactory[domain_permissions.GrantAuthorizationPermissionsRequest]
):
    subject_type: str = "nip"
    subject_value = "1234567890"
    permission: str = "self_invoicing"


@register_fixture(name="domain_perm_grant_indirect_req")
class DomainGrantIndirectPermissionsRequestFactory(
    ModelFactory[domain_permissions.GrantIndirectPermissionsRequest]
): ...


@register_fixture(name="domain_perm_grant_subunit_req")
class DomainGrantSubunitPermissionsRequestFactory(
    ModelFactory[domain_permissions.GrantSubunitPermissionsRequest]
):
    subject_type: str = "nip"
    subject_value = "1234567890"
    context_type: str = "nip"
    context_value = "1234567890"
    first_name = "Jan"


@register_fixture(name="domain_perm_grant_eu_entity_req")
class DomainGrantEuEntityPermissionsRequestFactory(
    ModelFactory[domain_permissions.GrantEuEntityPermissionsRequest]
):
    subject_value = "a" * 64
    permissions: list[str] = ["invoice_read"]


@register_fixture(name="domain_perm_grant_eu_admin_req")
class DomainGrantEuEntityAdministrationRequestFactory(
    ModelFactory[domain_permissions.GrantEuEntityAdministrationRequest]
):
    subject_value = "a" * 64
    context_type: str = "nip_vat_ue"
    context_value = "1234567890-PL1234567890"


@register_fixture(name="domain_perm_query_persons")
class DomainPersonPermissionsQueryFactory(
    ModelFactory[domain_permissions.PersonPermissionsQuery]
):
    query_type: str = "in_context"
    permission_types = None
    permission_state = None
    author_type = None
    author_value = None
    authorized_type = None
    authorized_value = None
    context_type = None
    context_value = None
    target_type = None
    target_value = None


@register_fixture(name="domain_perm_query_authorizations")
class DomainAuthorizationPermissionsQueryFactory(
    ModelFactory[domain_permissions.AuthorizationPermissionsQuery]
):
    query_type: str = "granted"
    permission_types = None
    authorizing_type = None
    authorizing_value = None
    authorized_type = None
    authorized_value = None


@register_fixture(name="domain_perm_query_entities")
class DomainEntityPermissionsQueryFactory(
    ModelFactory[domain_permissions.EntityPermissionsQuery]
):
    context_type = None
    context_value = None


@register_fixture(name="domain_perm_query_personal")
class DomainPersonalPermissionsQueryFactory(
    ModelFactory[domain_permissions.PersonalPermissionsQuery]
):
    permission_state: str | None = "active"
    permission_types = None
    context_type = None
    context_value = None
    target_type = None
    target_value = None


@register_fixture(name="domain_perm_query_eu_entities")
class DomainEuEntityPermissionsQueryFactory(
    ModelFactory[domain_permissions.EuEntityPermissionsQuery]
):
    vat_ue_identifier = None
    authorized_fingerprint_identifier = None
    permission_types = None


@register_fixture(name="domain_perm_query_subordinate")
class DomainSubordinateEntityRolesQueryFactory(
    ModelFactory[domain_permissions.SubordinateEntityRolesQuery]
):
    subordinate_nip = None


@register_fixture(name="domain_perm_query_subunits")
class DomainSubunitPermissionsQueryFactory(
    ModelFactory[domain_permissions.SubunitPermissionsQuery]
):
    subunit_nip = None
