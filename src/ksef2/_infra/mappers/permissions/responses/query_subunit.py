"""Mappings from subunit permission query responses to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2._domain.models.permissions import (
    CertificateSubjectIdentifierType,
    PersonPermissionScope,
    SubunitIdentifierType,
    SubunitPermission,
    SubunitPermissionsQueryResponse,
)
from ksef2._infra.schema.api import spec


def _certificate_subject_identifier_from_value(
    value: str,
) -> CertificateSubjectIdentifierType:
    match value:
        case "Nip":
            return "nip"
        case "Pesel":
            return "pesel"
        case "Fingerprint":
            return "fingerprint"
        case _:
            raise ValueError(f"Unknown certificate subject identifier type: {value!r}")


def _subunit_identifier_from_value(value: str) -> SubunitIdentifierType:
    match value:
        case "Nip":
            return "nip"
        case "InternalId":
            return "internal_id"
        case _:
            raise ValueError(f"Unknown subunit identifier type: {value!r}")


def _map_subunit_permission_scope(
    response: spec.SubunitPermissionScope,
) -> PersonPermissionScope:
    match response:
        case spec.SubunitPermissionScope.CredentialsManage:
            return "credentials_manage"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@overload
def subunit_from_spec(response: spec.SubunitPermission) -> SubunitPermission: ...


@overload
def subunit_from_spec(
    response: spec.CertificateSubjectIdentifierType,
) -> CertificateSubjectIdentifierType: ...


@overload
def subunit_from_spec(
    response: spec.SubunitPermissionsAuthorIdentifierType,
) -> CertificateSubjectIdentifierType: ...


@overload
def subunit_from_spec(
    response: spec.SubunitPermissionsSubjectIdentifierType,
) -> CertificateSubjectIdentifierType: ...


@overload
def subunit_from_spec(
    response: spec.SubunitPermissionsContextIdentifierType,
) -> SubunitIdentifierType: ...


@overload
def subunit_from_spec(
    response: spec.SubunitPermissionsSubunitIdentifierType,
) -> SubunitIdentifierType: ...


@overload
def subunit_from_spec(
    response: spec.QuerySubunitPermissionsResponse,
) -> SubunitPermissionsQueryResponse: ...


def subunit_from_spec(response: BaseModel | Enum) -> object:
    """Convert subunit permission query responses into domain models."""
    return _from_spec(response)


@_from_spec.register
def _(
    response: spec.CertificateSubjectIdentifierType,
) -> CertificateSubjectIdentifierType:
    return _certificate_subject_identifier_from_value(response.value)


@_from_spec.register
def _(
    response: spec.SubunitPermissionsAuthorIdentifierType,
) -> CertificateSubjectIdentifierType:
    return _certificate_subject_identifier_from_value(response.value)


@_from_spec.register
def _(
    response: spec.SubunitPermissionsSubjectIdentifierType,
) -> CertificateSubjectIdentifierType:
    return _certificate_subject_identifier_from_value(response.value)


@_from_spec.register
def _(response: spec.SubunitPermissionsContextIdentifierType) -> SubunitIdentifierType:
    return _subunit_identifier_from_value(response.value)


@_from_spec.register
def _(response: spec.SubunitPermissionsSubunitIdentifierType) -> SubunitIdentifierType:
    return _subunit_identifier_from_value(response.value)


@_from_spec.register
def _(response: spec.SubunitPermission) -> SubunitPermission:
    person_first_name = None
    person_last_name = None
    entity_first_name = None
    entity_last_name = None
    if response.subjectPersonDetails:
        person_first_name = response.subjectPersonDetails.firstName
        person_last_name = response.subjectPersonDetails.lastName

    return SubunitPermission(
        id=response.id,
        author_type=subunit_from_spec(response.authorIdentifier.type),
        author_value=response.authorIdentifier.value,
        authorized_type=subunit_from_spec(response.authorizedIdentifier.type),
        authorized_value=response.authorizedIdentifier.value,
        permission_type=_map_subunit_permission_scope(response.permissionScope),
        description=response.description,
        start_date=response.startDate,
        subject_first_name=person_first_name,
        subject_last_name=person_last_name,
        entity_first_name=entity_first_name,
        entity_last_name=entity_last_name,
        subunit_name=response.subunitName,
        subunit_type=subunit_from_spec(response.subunitIdentifier.type),
        subunit_value=response.subunitIdentifier.value,
    )


@_from_spec.register
def _(
    response: spec.QuerySubunitPermissionsResponse,
) -> SubunitPermissionsQueryResponse:
    return SubunitPermissionsQueryResponse(
        permissions=[subunit_from_spec(p) for p in response.permissions],
        has_more=response.hasMore,
    )
