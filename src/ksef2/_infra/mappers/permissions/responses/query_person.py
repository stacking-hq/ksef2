"""Mappings from person permission query responses to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2._domain.models.permissions import (
    PersonPermissionDetail,
    PersonPermissionScope,
    PersonPermissionsAuthorizedIdentifierType,
    PersonPermissionsContextIdentifierType,
    PersonPermissionsQueryResponse,
    PersonPermissionsTargetIdentifierType,
    PermissionState,
    PersonAuthorIdentifierType,
)
from ksef2._infra.schema.api import spec


def _map_person_context_identifier_type(
    response: spec.PersonPermissionsContextIdentifierType,
) -> PersonPermissionsContextIdentifierType:
    value = response.value
    match value:
        case "Nip":
            return "nip"
        case "InternalId":
            return "internal_id"
        case _:
            raise ValueError(f"Unknown person context identifier type: {value!r}")


def _map_person_target_identifier_type(
    response: spec.PersonPermissionsTargetIdentifierType,
) -> PersonPermissionsTargetIdentifierType:
    value = response.value
    match value:
        case "Nip":
            return "nip"
        case "InternalId":
            return "internal_id"
        case "AllPartners":
            return "all_partners"
        case _:
            raise ValueError(f"Unknown person target identifier type: {value!r}")


def _map_author_identifier_type(
    response: spec.PersonPermissionsAuthorIdentifierType,
) -> PersonAuthorIdentifierType:
    match response:
        case spec.PersonPermissionsAuthorIdentifierType.Nip:
            return "nip"
        case spec.PersonPermissionsAuthorIdentifierType.Pesel:
            return "pesel"
        case spec.PersonPermissionsAuthorIdentifierType.Fingerprint:
            return "fingerprint"
        case spec.PersonPermissionsAuthorIdentifierType.System:
            return "system"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def _map_cert_subject_identifier_type(
    response: spec.CertificateSubjectIdentifierType,
) -> PersonPermissionsAuthorizedIdentifierType:
    match response:
        case spec.CertificateSubjectIdentifierType.Nip:
            return "nip"
        case spec.CertificateSubjectIdentifierType.Pesel:
            return "pesel"
        case spec.CertificateSubjectIdentifierType.Fingerprint:
            return "fingerprint"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def _map_person_permission(
    response: spec.PersonPermissionScope,
) -> PersonPermissionScope:
    match response:
        case spec.PersonPermissionScope.InvoiceRead:
            return "invoice_read"
        case spec.PersonPermissionScope.InvoiceWrite:
            return "invoice_write"
        case spec.PersonPermissionScope.Introspection:
            return "introspection"
        case spec.PersonPermissionScope.CredentialsRead:
            return "credentials_read"
        case spec.PersonPermissionScope.CredentialsManage:
            return "credentials_manage"
        case spec.PersonPermissionScope.EnforcementOperations:
            return "enforcement_operations"
        case spec.PersonPermissionScope.SubunitManage:
            return "subunit_manage"
        case spec.PersonPermissionScope.CollectiveIdentifierManage:
            return "collective_identifier_manage"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def _map_permission_state(response: spec.PermissionState) -> PermissionState:
    match response:
        case spec.PermissionState.Active:
            return "active"
        case spec.PermissionState.Inactive:
            return "inactive"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@overload
def person_from_spec(response: spec.PersonPermission) -> PersonPermissionDetail: ...


@overload
def person_from_spec(
    response: spec.QueryPersonPermissionsResponse,
) -> PersonPermissionsQueryResponse: ...


def person_from_spec(response: BaseModel | Enum) -> object:
    """Convert person-permission query responses into domain models."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(
    response: spec.PersonPermission,
) -> PersonPermissionDetail:
    person_first_name = None
    person_last_name = None
    entity_first_name = None
    entity_last_name = None
    if response.subjectPersonDetails:
        person_first_name = response.subjectPersonDetails.firstName
        person_last_name = response.subjectPersonDetails.lastName
    if response.subjectEntityDetails:
        entity_first_name = response.subjectEntityDetails.fullName
        entity_last_name = response.subjectEntityDetails.fullName
    return PersonPermissionDetail(
        id=response.id,
        author_type=_map_author_identifier_type(response.authorIdentifier.type)
        if response.authorIdentifier.value
        else None,
        author_value=response.authorIdentifier.value
        if response.authorIdentifier.value
        else None,
        authorized_type=_map_cert_subject_identifier_type(
            response.authorizedIdentifier.type
        )
        if response.authorizedIdentifier.value
        else None,
        authorized_value=response.authorizedIdentifier.value
        if response.authorizedIdentifier.value
        else None,
        context_type=_map_person_context_identifier_type(
            response.contextIdentifier.type
        )
        if response.contextIdentifier
        else None,
        context_value=response.contextIdentifier.value
        if response.contextIdentifier
        else None,
        target_type=_map_person_target_identifier_type(response.targetIdentifier.type)
        if response.targetIdentifier
        else None,
        target_value=response.targetIdentifier.value
        if response.targetIdentifier and response.targetIdentifier.value
        else None,
        permission_state=_map_permission_state(response.permissionState),
        permission_type=_map_person_permission(response.permissionScope),
        description=response.description,
        start_date=response.startDate,
        can_delegate=response.canDelegate,
        person_first_name=person_first_name,
        person_last_name=person_last_name,
        entity_first_name=entity_first_name,
        entity_last_name=entity_last_name,
    )


@_from_spec.register
def _(
    response: spec.QueryPersonPermissionsResponse,
) -> PersonPermissionsQueryResponse:
    return PersonPermissionsQueryResponse(
        permissions=[person_from_spec(p) for p in response.permissions],
        has_more=response.hasMore,
    )
