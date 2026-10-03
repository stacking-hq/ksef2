"""Reusable pagination and filter parameter models."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, field_serializer, field_validator

from ksef2._domain.models.base import KSeFBaseParams
from ksef2._domain.models.invoices import (
    SortOrder,
    normalize_sort_order,
    sort_order_to_spec,
)
from ksef2._domain.models.session import (
    SessionStatus,
    SessionType,
    normalize_session_status,
    normalize_session_type,
    session_status_to_spec,
    session_type_to_spec,
)
from ksef2._domain.models.tokens import TokenAuthorIdentifierType, TokenStatus
from ksef2._domain.types import (
    CollectiveIdentifierQueryParams,
    InvoiceMetadataQueryParams,
    ListSessionsQueryParams,
    ListTokensQueryParams,
    OffsetPaginationQueryParams,
)


class PageSizeMixin(BaseModel):
    """Adds a bounded ``page_size`` query parameter."""

    page_size: int = Field(default=10, ge=10, le=100)
    """Number of results per page (10–100)."""


class PageOffsetMixin(BaseModel):
    """Adds a zero-based ``page_offset`` query parameter."""

    page_offset: int = Field(default=0, ge=0)
    """Zero-based index of the page to return."""


class SortOrderMixin(BaseModel):
    """Adds a sortable ``sort_order`` query parameter."""

    sort_order: SortOrder = "asc"
    """Sort direction, ``asc`` or ``desc``."""

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
    """Offset-based pagination parameters."""

    def next_page(self) -> Self:
        """Return a copy advanced by one page offset.

        Returns:
            A copy advanced by one page offset.
        """
        return self.model_copy(update={"page_offset": self.page_offset + 1})


class InvoiceMetadataParams(
    KSeFBaseParams[InvoiceMetadataQueryParams],
    PageSizeMixin,
    PageOffsetMixin,
    SortOrderMixin,
):
    """Pagination parameters for invoice metadata queries."""

    page_size: int = Field(default=10, ge=10, le=250)
    """Number of results per page (10–250)."""

    def with_page_offset(self, page_offset: int) -> Self:
        """Return a copy with an explicit page offset.

        Args:
            page_offset: Zero-based index of the page to return.

        Returns:
            A copy of these parameters with ``page_offset`` replaced.
        """
        return self.model_copy(update={"page_offset": page_offset})

    def next_page(self) -> Self:
        """Return a copy advanced by one invoice metadata page.

        Returns:
            A copy advanced by one invoice metadata page.
        """
        return self.with_page_offset(self.page_offset + 1)


class PermissionsQueryParams(OffsetPaginationParams):
    """Offset-based pagination parameters for permission query endpoints."""


class TokenPaginationParams(KSeFBaseParams[dict[str, object]]):
    """Base for endpoints using pageSize + x-continuation-token header."""

    page_size: int = Field(default=10, ge=10, le=100)
    """Number of results per page (10–100)."""


class CollectiveIdentifierParams(
    KSeFBaseParams[CollectiveIdentifierQueryParams], PageSizeMixin
):
    """Continuation-token pagination for collective identifier endpoints."""

    page_size: int = Field(default=10, ge=10, le=200)
    """Number of results per page (10–200)."""


class SessionFiltersMixin(BaseModel):
    """Normalizes and serializes session-list filter fields."""

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
    """Continuation-token pagination for session invoice listings."""

    page_size: int = Field(default=10, ge=10, le=1000)
    """Number of results per page (10–1000)."""


class TokenListParams(KSeFBaseParams[ListTokensQueryParams], PageSizeMixin):
    """Query parameters for token listings."""

    status: list[TokenStatus] | None = None
    """Match tokens in any of these statuses."""
    description: str | None = None
    """Match tokens whose description contains this text."""
    author_identifier: str | None = None
    """Match tokens created by this identifier."""
    author_identifier_type: TokenAuthorIdentifierType | None = None
    """Kind of identifier in ``author_identifier``."""


class ListSessionsQuery(
    SessionFiltersMixin, KSeFBaseParams[ListSessionsQueryParams], PageSizeMixin
):
    """Query parameters for authentication or invoice session listings."""

    session_type: SessionType
    """Kind of sessions to list: ``online`` or ``batch``."""
    reference_number: str | None = None
    """Match this session reference number."""
    date_created_from: datetime | None = None
    """Match sessions created at or after this time."""
    date_created_to: datetime | None = None
    """Match sessions created at or before this time."""
    date_closed_from: datetime | None = None
    """Match sessions closed at or after this time."""
    date_closed_to: datetime | None = None
    """Match sessions closed at or before this time."""
    date_modified_from: datetime | None = None
    """Match sessions modified at or after this time."""
    date_modified_to: datetime | None = None
    """Match sessions modified at or before this time."""
    statuses: list[SessionStatus] | None = None
    """Match sessions in any of these statuses."""
