"""Mappings from EU-entity permission query responses to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2._domain.models.permissions import (
    CertificateSubjectIdentifierType,
    EuEntityPermission,
    EuEntityPermissionsQueryResponse,
    EuEntityQueryPermissionType,
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


def _map_eu_query_permission(
    response: spec.EuEntityPermissionsQueryPermissionType,
) -> EuEntityQueryPermissionType:
    match response:
        case spec.EuEntityPermissionsQueryPermissionType.VatUeManage:
            return "vat_ue_manage"
        case spec.EuEntityPermissionsQueryPermissionType.InvoiceWrite:
            return "invoice_write"
        case spec.EuEntityPermissionsQueryPermissionType.InvoiceRead:
            return "invoice_read"
        case spec.EuEntityPermissionsQueryPermissionType.Introspection:
            return "introspection"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@overload
def eu_entity_from_spec(response: spec.EuEntityPermission) -> EuEntityPermission: ...


@overload
def eu_entity_from_spec(
    response: spec.CertificateSubjectIdentifierType,
) -> CertificateSubjectIdentifierType: ...


@overload
def eu_entity_from_spec(
    response: spec.EuEntityPermissionsAuthorIdentifierType,
) -> CertificateSubjectIdentifierType: ...


@overload
def eu_entity_from_spec(
    response: spec.QueryEuEntityPermissionsResponse,
) -> EuEntityPermissionsQueryResponse: ...


def eu_entity_from_spec(response: BaseModel | Enum) -> object:
    """Convert EU-entity permission query responses into domain models."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


def _map_author_identifier_type(
    response: spec.EuEntityPermissionsAuthorIdentifierType,
) -> CertificateSubjectIdentifierType:
    return _certificate_subject_identifier_from_value(response.value)


@_from_spec.register
def _(
    response: spec.EuEntityPermission,
) -> EuEntityPermission:
    subject_first_name = None
    subject_last_name = None
    if response.subjectPersonDetails:
        subject_first_name = response.subjectPersonDetails.firstName
        subject_last_name = response.subjectPersonDetails.lastName

    entity_full_name = None
    entity_address = None
    if response.subjectEntityDetails:
        entity_full_name = response.subjectEntityDetails.fullName
        entity_address = response.subjectEntityDetails.address

    elif response.euEntityDetails:
        entity_full_name = response.euEntityDetails.fullName
        entity_address = response.euEntityDetails.address

    return EuEntityPermission(
        id=response.id,
        author_type=_map_author_identifier_type(response.authorIdentifier.type),
        author_value=response.authorIdentifier.value,
        vat_ue_identifier=response.vatUeIdentifier,
        eu_entity_name=response.euEntityName,
        authorized_fingerprint_identifier=response.authorizedFingerprintIdentifier,
        permission_type=_map_eu_query_permission(response.permissionScope),
        description=response.description,
        subject_first_name=subject_first_name,
        subject_last_name=subject_last_name,
        entity_full_name=entity_full_name,
        entity_address=entity_address,
        start_date=response.startDate,
    )


@_from_spec.register
def _(
    response: spec.QueryEuEntityPermissionsResponse,
) -> EuEntityPermissionsQueryResponse:
    return EuEntityPermissionsQueryResponse(
        permissions=[eu_entity_from_spec(p) for p in response.permissions],
        has_more=response.hasMore,
    )
