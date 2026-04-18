"""Mappings from auth domain models to generated API schema models."""

from enum import Enum
from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2.domain.models.auth import (
    ContextIdentifierType,
    ContextIdentifierTypeEnum,
    InitTokenAuthenticationRequest,
)
from ksef2.infra.mappers.helpers import get_matching_enum
from ksef2.infra.schema.api import spec
from ksef2.infra.schema.api.supp.auth import InitTokenAuthenticationRequest as supp


class ValidAuthEnums(Enum):
    ContextIdentifierType = ContextIdentifierTypeEnum


VALID_AUTH_ENUMS = [v.value for v in ValidAuthEnums.__members__.values()]


@overload
def to_spec(request: InitTokenAuthenticationRequest) -> supp: ...


@overload
def to_spec(
    request: ContextIdentifierType,
) -> spec.AuthenticationContextIdentifierType: ...


@overload
def to_spec(request: str) -> object: ...


def to_spec(request: BaseModel | Enum | str) -> object:
    """Convert an auth domain object or literal into its schema counterpart.

    Args:
        request: Domain model, enum, or supported string literal to map.

    Returns:
        The matching generated API schema object or enum value.

    Raises:
        NotImplementedError: If no mapper exists for the provided value.
    """
    if isinstance(request, str):
        enum_cls = get_matching_enum(request, VALID_AUTH_ENUMS)
        if enum_cls is None:
            raise NotImplementedError(f"No mapper for string value: {request!r}")
        return _to_spec(enum_cls(request))
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel | Enum | str) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: ContextIdentifierTypeEnum) -> spec.AuthenticationContextIdentifierType:
    match request:
        case ContextIdentifierTypeEnum.NIP:
            return spec.AuthenticationContextIdentifierType.Nip
        case ContextIdentifierTypeEnum.INTERNAL_ID:
            return spec.AuthenticationContextIdentifierType.InternalId
        case ContextIdentifierTypeEnum.NIP_VAT_UE:
            return spec.AuthenticationContextIdentifierType.NipVatUe
        case ContextIdentifierTypeEnum.PEPPOL_ID:
            return spec.AuthenticationContextIdentifierType.PeppolId
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@_to_spec.register
def _(request: InitTokenAuthenticationRequest) -> supp:
    return supp(
        challenge=request.challenge,
        contextIdentifier=spec.AuthenticationContextIdentifier(
            type=to_spec(request.context_type),
            value=request.context_value,
        ),
        encryptedToken=request.encrypted_token,
        authorizationPolicy=None,
    )
