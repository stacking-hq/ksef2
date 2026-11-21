"""Shared wire query types for revision 2 token listing."""

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, NotRequired, TypedDict

from pydantic import AfterValidator, AwareDatetime, TypeAdapter

from ksef2._infra.schema.api import spec


_AWARE_DATETIME_ADAPTER = TypeAdapter[datetime](AwareDatetime)
type _DateFilter = Annotated[
    datetime | str, AfterValidator(_AWARE_DATETIME_ADAPTER.validate_python)
]


def _validate_status(value: str) -> str:
    return spec.TokenStatusFilterRev2(value)


def _validate_author_type(value: str) -> str:
    return spec.TokenAuthorIdentifierTypeFilterRev2(value)


class ListTokensRev2QueryParams(TypedDict):
    """Wire-format filters for the revision 2 token listing."""

    status: NotRequired[
        Sequence[Annotated[str, AfterValidator(_validate_status)]] | None
    ]
    description: NotRequired[str | None]
    authorIdentifier: NotRequired[str | None]
    authorIdentifierType: NotRequired[
        Annotated[str, AfterValidator(_validate_author_type)] | None
    ]
    validFrom: NotRequired[_DateFilter | None]
    validTo: NotRequired[_DateFilter | None]
    pageSize: NotRequired[int | None]
