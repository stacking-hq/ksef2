"""Mappings from subordinate-entity role query responses to domain models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2._domain.models.permissions import (
    EntityIdentifierType,
    SubordinateEntityRoleDetail,
    SubordinateEntityRolesQueryResponse,
    SubordinateEntityRoleType,
)
from ksef2._infra.schema.api import spec


def _entity_identifier_from_value(value: str) -> EntityIdentifierType:
    match value:
        case "Nip":
            return "nip"
        case _:
            raise ValueError(f"Unknown entity identifier type: {value!r}")


def _map_subordinate_role(
    response: spec.SubordinateEntityRoleType,
) -> SubordinateEntityRoleType:
    match response:
        case spec.SubordinateEntityRoleType.LocalGovernmentSubUnit:
            return "local_government_sub_unit"
        case spec.SubordinateEntityRoleType.VatGroupSubUnit:
            return "vat_group_sub_unit"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@overload
def subordinate_roles_from_spec(
    response: spec.SubordinateEntityRole,
) -> SubordinateEntityRoleDetail: ...


@overload
def subordinate_roles_from_spec(
    response: spec.EntityAuthorizationsAuthorizingEntityIdentifierType,
) -> EntityIdentifierType: ...


@overload
def subordinate_roles_from_spec(
    response: spec.SubordinateRoleSubordinateEntityIdentifierType,
) -> EntityIdentifierType: ...


@overload
def subordinate_roles_from_spec(
    response: spec.QuerySubordinateEntityRolesResponse,
) -> SubordinateEntityRolesQueryResponse: ...


def subordinate_roles_from_spec(response: BaseModel | Enum) -> object:
    """Convert subordinate-role query responses into domain models."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


def _map_subordinate_entity_identifier(
    response: spec.SubordinateRoleSubordinateEntityIdentifierType,
) -> EntityIdentifierType:
    return _entity_identifier_from_value(response.value)


@_from_spec.register
def _(response: spec.SubordinateEntityRole) -> SubordinateEntityRoleDetail:
    return SubordinateEntityRoleDetail(
        subordinate_entity_type=_map_subordinate_entity_identifier(
            response.subordinateEntityIdentifier.type
        ),
        subordinate_entity_value=response.subordinateEntityIdentifier.value,
        role=_map_subordinate_role(response.role),
        description=response.description,
        start_date=response.startDate,
    )


@_from_spec.register
def _(
    response: spec.QuerySubordinateEntityRolesResponse,
) -> SubordinateEntityRolesQueryResponse:
    return SubordinateEntityRolesQueryResponse(
        roles=[subordinate_roles_from_spec(role) for role in response.roles],
        has_more=response.hasMore,
    )
