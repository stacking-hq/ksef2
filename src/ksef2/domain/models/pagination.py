from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, field_serializer, field_validator

from ksef2.domain.models.base import KSeFBaseParams
from ksef2.domain.models.invoices import (
    SortOrder,
    normalize_sort_order,
    sort_order_to_spec,
)
from ksef2.domain.models.session import (
    SessionStatus,
    SessionType,
    normalize_session_status,
    normalize_session_type,
    session_status_to_spec,
    session_type_to_spec,
)
from ksef2.domain.models.tokens import TokenAuthorIdentifierType, TokenStatus
from ksef2.domain.types import (
    InvoiceMetadataQueryParams,
    ListSessionsQueryParams,
    ListTokensQueryParams,
    OffsetPaginationQueryParams,
)


class PageSizeMixin(BaseModel):
    page_size: int = Field(default=10, ge=10, le=100)


class PageOffsetMixin(BaseModel):
    page_offset: int = Field(default=0, ge=0)


class SortOrderMixin(BaseModel):
    sort_order: SortOrder = "asc"

    @field_validator("sort_order", mode="before")
    @classmethod
    def _normalize_sort_order(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_sort_order(value)
        return value

    @field_serializer("sort_order")
    def _serialize_sort_order(self, value: SortOrder) -> str:
        return sort_order_to_spec(value)


class OffsetPaginationParams(
    KSeFBaseParams[OffsetPaginationQueryParams], PageSizeMixin, PageOffsetMixin
):
    def next_page(self) -> Self:
        return self.model_copy(update={"page_offset": self.page_offset + 1})


class InvoiceMetadataParams(
    KSeFBaseParams[InvoiceMetadataQueryParams],
    PageSizeMixin,
    PageOffsetMixin,
    SortOrderMixin,
):
    page_size: int = Field(default=10, ge=10, le=250)

    def with_page_offset(self, page_offset: int) -> Self:
        return self.model_copy(update={"page_offset": page_offset})

    def next_page(self) -> Self:
        return self.with_page_offset(self.page_offset + 1)


class PermissionsQueryParams(OffsetPaginationParams): ...


class TokenPaginationParams(KSeFBaseParams[dict[str, object]]):
    """Base for endpoints using pageSize + x-continuation-token header."""

    page_size: int = Field(default=10, ge=10, le=100)


class SessionFiltersMixin(BaseModel):
    @field_validator("session_type", mode="before", check_fields=False)
    @classmethod
    def _normalize_session_type(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_session_type(value)
        return value

    @field_validator("statuses", mode="before", check_fields=False)
    @classmethod
    def _normalize_statuses(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, list):
            return [
                normalize_session_status(status) if isinstance(status, str) else status
                for status in value
            ]
        return value

    @field_serializer("session_type", check_fields=False)
    def _serialize_session_type(self, value: SessionType) -> str:
        return session_type_to_spec(value)

    @field_serializer("statuses", check_fields=False)
    def _serialize_statuses(
        self, value: list[SessionStatus] | None
    ) -> list[str] | None:
        if value is None:
            return None
        return [session_status_to_spec(status) for status in value]


class SessionInvoiceListParams(TokenPaginationParams):
    page_size: int = Field(default=10, ge=10, le=1000)


class TokenListParams(KSeFBaseParams[ListTokensQueryParams], PageSizeMixin):
    status: list[TokenStatus] | None = None
    description: str | None = None
    author_identifier: str | None = None
    author_identifier_type: TokenAuthorIdentifierType | None = None


class ListSessionsQuery(
    SessionFiltersMixin, KSeFBaseParams[ListSessionsQueryParams], PageSizeMixin
):
    session_type: SessionType
    reference_number: str | None = None
    date_created_from: datetime | None = None
    date_created_to: datetime | None = None
    date_closed_from: datetime | None = None
    date_closed_to: datetime | None = None
    date_modified_from: datetime | None = None
    date_modified_to: datetime | None = None
    statuses: list[SessionStatus] | None = None
