"""Mappings from entity and authorization query responses to domain models."""

from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2.domain.models.permissions import (
    AuthorizationGrantDetail,
    AuthorizationPermissionType,
    AuthorizationPermissionsQueryResponse,
    AuthorizationSubjectIdentifierType,
    CertificateSubjectIdentifierType,
    EntityIdentifierType,
    EntityPermissionDetail,
    EntityPermissionsContextIdentifierType,
    EntityPermissionsQueryResponse,
    EntityPermissionType,
    EntityRole,
    EntityRoleType,
    EntityRolesResponse,
)
from ksef2.infra.schema.api import spec


def certificate_subject_identifier_from_spec(
    response: spec.CertificateSubjectIdentifierType,
) -> CertificateSubjectIdentifierType:
    match response:
        case spec.CertificateSubjectIdentifierType.Nip:
            return "nip"
        case spec.CertificateSubjectIdentifierType.Pesel:
            return "pesel"
        case spec.CertificateSubjectIdentifierType.Fingerprint:
            return "fingerprint"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def authorization_author_identifier_from_spec(
    response: spec.EntityAuthorizationsAuthorIdentifierType,
) -> CertificateSubjectIdentifierType:
    match response:
        case spec.EntityAuthorizationsAuthorIdentifierType.Nip:
            return "nip"
        case spec.EntityAuthorizationsAuthorIdentifierType.Pesel:
            return "pesel"
        case spec.EntityAuthorizationsAuthorIdentifierType.Fingerprint:
            return "fingerprint"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def entity_role_type_from_spec(response: spec.EntityRoleType) -> EntityRoleType:
    match response:
        case spec.EntityRoleType.CourtBailiff:
            return "court_bailiff"
        case spec.EntityRoleType.EnforcementAuthority:
            return "enforcement_authority"
        case spec.EntityRoleType.LocalGovernmentUnit:
            return "local_government_unit"
        case spec.EntityRoleType.LocalGovernmentSubUnit:
            return "local_government_sub_unit"
        case spec.EntityRoleType.VatGroupUnit:
            return "vat_group_unit"
        case spec.EntityRoleType.VatGroupSubUnit:
            return "vat_group_sub_unit"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def authorization_subject_identifier_from_spec(
    response: spec.EntityAuthorizationPermissionsSubjectIdentifierType
    | spec.EntityAuthorizationsAuthorizedEntityIdentifierType,
) -> AuthorizationSubjectIdentifierType:
    match response:
        case (
            spec.EntityAuthorizationPermissionsSubjectIdentifierType.Nip
            | spec.EntityAuthorizationsAuthorizedEntityIdentifierType.Nip
        ):
            return "nip"
        case (
            spec.EntityAuthorizationPermissionsSubjectIdentifierType.PeppolId
            | spec.EntityAuthorizationsAuthorizedEntityIdentifierType.PeppolId
        ):
            return "peppol_id"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def entity_identifier_from_spec(
    response: spec.EntityAuthorizationsAuthorizingEntityIdentifierType
    | spec.EntityRolesParentEntityIdentifierType,
) -> EntityIdentifierType:
    match response:
        case (
            spec.EntityAuthorizationsAuthorizingEntityIdentifierType.Nip
            | spec.EntityRolesParentEntityIdentifierType.Nip
        ):
            return "nip"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def entity_context_identifier_from_spec(
    response: spec.EntityPermissionsContextIdentifierType,
) -> EntityPermissionsContextIdentifierType:
    match response:
        case spec.EntityPermissionsContextIdentifierType.Nip:
            return "nip"
        case spec.EntityPermissionsContextIdentifierType.InternalId:
            return "internal_id"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def entity_permission_scope_from_spec(
    response: spec.EntityPermissionItemScope,
) -> EntityPermissionType:
    match response:
        case spec.EntityPermissionItemScope.InvoiceRead:
            return "invoice_read"
        case spec.EntityPermissionItemScope.InvoiceWrite:
            return "invoice_write"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def authorization_permission_from_spec(
    response: spec.InvoicePermissionType,
) -> AuthorizationPermissionType:
    match response:
        case spec.InvoicePermissionType.SelfInvoicing:
            return "self_invoicing"
        case spec.InvoicePermissionType.RRInvoicing:
            return "rr_invoicing"
        case spec.InvoicePermissionType.TaxRepresentative:
            return "tax_representative"
        case spec.InvoicePermissionType.PefInvoicing:
            return "pef_invoicing"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@overload
def entity_from_spec(
    response: spec.EntityPermissionItem,
) -> EntityPermissionDetail: ...


@overload
def entity_from_spec(
    response: spec.QueryEntityPermissionsResponse,
) -> EntityPermissionsQueryResponse: ...


@overload
def entity_from_spec(response: spec.EntityRole) -> EntityRole: ...


@overload
def entity_from_spec(
    response: spec.EntityAuthorizationGrant,
) -> AuthorizationGrantDetail: ...


@overload
def entity_from_spec(
    response: spec.QueryEntityRolesResponse,
) -> EntityRolesResponse: ...


@overload
def entity_from_spec(
    response: spec.QueryEntityAuthorizationPermissionsResponse,
) -> AuthorizationPermissionsQueryResponse: ...


def entity_from_spec(response: BaseModel) -> object:
    """Convert entity-role and authorization query responses into domain models."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(response: spec.EntityPermissionItem) -> EntityPermissionDetail:
    return EntityPermissionDetail(
        id=response.id,
        context_type=entity_context_identifier_from_spec(
            response.contextIdentifier.type
        ),
        context_value=response.contextIdentifier.value,
        permission_type=entity_permission_scope_from_spec(response.permissionScope),
        description=response.description,
        start_date=response.startDate,
        can_delegate=response.canDelegate,
    )


@_from_spec.register
def _(response: spec.QueryEntityPermissionsResponse) -> EntityPermissionsQueryResponse:
    return EntityPermissionsQueryResponse(
        permissions=[
            entity_from_spec(permission) for permission in response.permissions
        ],
        has_more=response.hasMore,
    )


@_from_spec.register
def _(response: spec.EntityAuthorizationGrant) -> AuthorizationGrantDetail:
    entity_full_name = None
    if response.subjectEntityDetails:
        entity_full_name = response.subjectEntityDetails.fullName
    return AuthorizationGrantDetail(
        id=response.id,
        author_type=authorization_author_identifier_from_spec(
            response.authorIdentifier.type
        )
        if response.authorIdentifier
        else None,
        author_value=response.authorIdentifier.value
        if response.authorIdentifier
        else None,
        authorized_entity_type=authorization_subject_identifier_from_spec(
            response.authorizedEntityIdentifier.type
        ),
        authorized_entity_value=response.authorizedEntityIdentifier.value,
        authorizing_entity_type=entity_identifier_from_spec(
            response.authorizingEntityIdentifier.type
        ),
        authorizing_entity_value=response.authorizingEntityIdentifier.value,
        authorization_scope=authorization_permission_from_spec(
            response.authorizationScope
        ),
        description=response.description,
        entity_full_name=entity_full_name,
        start_date=response.startDate,
    )


@_from_spec.register
def _(response: spec.EntityRole) -> EntityRole:
    parent_type = None
    parent_value = None
    if response.parentEntityIdentifier:
        parent_type = entity_identifier_from_spec(response.parentEntityIdentifier.type)
        parent_value = response.parentEntityIdentifier.value
    return EntityRole(
        role=entity_role_type_from_spec(response.role),
        description=response.description,
        start_date=response.startDate,
        parent_entity_id_type=parent_type,
        parent_entity_id_value=parent_value,
    )


@_from_spec.register
def _(
    response: spec.QueryEntityRolesResponse,
) -> EntityRolesResponse:
    return EntityRolesResponse(
        roles=[entity_from_spec(role) for role in response.roles],
        has_more=response.hasMore,
    )


@_from_spec.register
def _(
    response: spec.QueryEntityAuthorizationPermissionsResponse,
) -> AuthorizationPermissionsQueryResponse:
    return AuthorizationPermissionsQueryResponse(
        authorization_grants=[
            entity_from_spec(g) for g in response.authorizationGrants
        ],
        has_more=response.hasMore,
    )
