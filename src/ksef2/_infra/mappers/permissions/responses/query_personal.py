"""Mappings from personal permission query responses to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2._domain.models.permissions import (
    PersonalPermissionsAuthorizedIdentifierType,
    PersonalPermissionsContextIdentifierType,
    PersonalPermissionsTargetIdentifierType,
    PersonalPermissionScope,
    PermissionState,
    PersonalPermissionDetail,
    PersonalPermissionsQueryResponse,
)
from ksef2._infra.schema.api import spec


def _map_personal_authorized_identifier_type(
    response: spec.PersonalPermissionsAuthorizedIdentifierType,
) -> PersonalPermissionsAuthorizedIdentifierType:
    value = response.value
    match value:
        case "Nip":
            return "nip"
        case "Pesel":
            return "pesel"
        case "Fingerprint":
            return "fingerprint"
        case _:
            raise ValueError(f"Unknown personal authorized identifier type: {value!r}")


def _map_personal_context_identifier_type(
    response: spec.PersonalPermissionsContextIdentifierType,
) -> PersonalPermissionsContextIdentifierType:
    value = response.value
    match value:
        case "Nip":
            return "nip"
        case "InternalId":
            return "internal_id"
        case _:
            raise ValueError(f"Unknown personal context identifier type: {value!r}")


def _map_personal_target_identifier_type(
    response: spec.PersonalPermissionsTargetIdentifierType,
) -> PersonalPermissionsTargetIdentifierType:
    value = response.value
    match value:
        case "Nip":
            return "nip"
        case "InternalId":
            return "internal_id"
        case "AllPartners":
            return "all_partners"
        case _:
            raise ValueError(f"Unknown personal target identifier type: {value!r}")


def _map_personal_permission(
    response: spec.PersonalPermissionScope,
) -> PersonalPermissionScope:
    match response:
        case spec.PersonalPermissionScope.InvoiceRead:
            return "invoice_read"
        case spec.PersonalPermissionScope.InvoiceWrite:
            return "invoice_write"
        case spec.PersonalPermissionScope.Introspection:
            return "introspection"
        case spec.PersonalPermissionScope.CredentialsRead:
            return "credentials_read"
        case spec.PersonalPermissionScope.CredentialsManage:
            return "credentials_manage"
        case spec.PersonalPermissionScope.EnforcementOperations:
            return "enforcement_operations"
        case spec.PersonalPermissionScope.SubunitManage:
            return "subunit_manage"
        case spec.PersonalPermissionScope.VatUeManage:
            return "vat_ue_manage"
        case spec.PersonalPermissionScope.CollectiveIdentifierManage:
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
def personal_from_spec(
    response: spec.PersonalPermission,
) -> PersonalPermissionDetail: ...


@overload
def personal_from_spec(
    response: spec.QueryPersonalPermissionsResponse,
) -> PersonalPermissionsQueryResponse: ...


def personal_from_spec(response: BaseModel | Enum) -> object:
    """Convert personal permission query responses into domain models."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(response: spec.PersonalPermission) -> PersonalPermissionDetail:
    subject_first_name, subject_last_name = None, None
    if response.subjectPersonDetails:
        subject_first_name = response.subjectPersonDetails.firstName
        subject_last_name = response.subjectPersonDetails.lastName

    entity_first_name, entity_address = None, None
    if response.subjectEntityDetails:
        entity_first_name = response.subjectEntityDetails.fullName
        entity_address = response.subjectEntityDetails.address

    return PersonalPermissionDetail(
        id=response.id,
        context_type=_map_personal_context_identifier_type(
            response.contextIdentifier.type
        )
        if response.contextIdentifier
        else None,
        context_value=response.contextIdentifier.value
        if response.contextIdentifier
        else None,
        authorized_type=_map_personal_authorized_identifier_type(
            response.authorizedIdentifier.type
        )
        if response.authorizedIdentifier
        else None,
        authorized_value=response.authorizedIdentifier.value
        if response.authorizedIdentifier
        else None,
        target_type=_map_personal_target_identifier_type(response.targetIdentifier.type)
        if response.targetIdentifier
        else None,
        target_value=response.targetIdentifier.value
        if response.targetIdentifier
        else None,
        permission_type=_map_personal_permission(response.permissionScope),
        description=response.description,
        subject_first_name=subject_first_name,
        subject_last_name=subject_last_name,
        entity_first_name=entity_first_name,
        entity_address=entity_address,
        permission_state=_map_permission_state(response.permissionState),
        start_date=response.startDate,
        can_delegate=response.canDelegate,
    )


@_from_spec.register
def _(
    response: spec.QueryPersonalPermissionsResponse,
) -> PersonalPermissionsQueryResponse:
    return PersonalPermissionsQueryResponse(
        permissions=[personal_from_spec(p) for p in response.permissions],
        has_more=response.hasMore,
    )
