from enum import Enum
from functools import singledispatch
from typing import cast, overload

from pydantic import BaseModel

from ksef2.domain.models.permissions import (
    AttachmentPermissionStatus,
    GrantPermissionsResponse,
    OperationStatus,
    OperationStatusCode,
    PermissionOperationStatusResponse,
)
from ksef2.infra.schema.api import spec


@overload
def from_spec(
    response: spec.PermissionsOperationResponse,
) -> GrantPermissionsResponse: ...


@overload
def from_spec(
    response: spec.PermissionsOperationStatusResponse,
) -> PermissionOperationStatusResponse: ...


@overload
def from_spec(
    response: spec.CheckAttachmentPermissionStatusResponse,
) -> AttachmentPermissionStatus: ...


def from_spec(response: BaseModel | Enum) -> object:
    """Convert grant-related permission responses into domain models."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(response: spec.PermissionsOperationResponse) -> GrantPermissionsResponse:
    return GrantPermissionsResponse(
        reference_number=response.referenceNumber,
    )


@_from_spec.register
def _(
    response: spec.PermissionsOperationStatusResponse,
) -> PermissionOperationStatusResponse:
    return PermissionOperationStatusResponse(
        status=OperationStatus(
            code=cast(OperationStatusCode, response.status.code),
            description=response.status.description,
        ),
    )


@_from_spec.register
def _(
    response: spec.CheckAttachmentPermissionStatusResponse,
) -> AttachmentPermissionStatus:
    return AttachmentPermissionStatus(
        is_attachment_allowed=response.isAttachmentAllowed or False,
        revoked_date=response.revokedDate,
    )
