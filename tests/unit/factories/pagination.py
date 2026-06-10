import pytest

from ksef2.domain.models.pagination import (
    InvoiceMetadataParams,
    OffsetPaginationParams,
    PermissionsQueryParams,
    SessionInvoiceListParams,
    TokenPaginationParams,
    TokenListParams,
)


@pytest.fixture
def offset_pagination_params() -> OffsetPaginationParams:
    return OffsetPaginationParams()


@pytest.fixture
def invoice_query_params() -> InvoiceMetadataParams:
    return InvoiceMetadataParams()


@pytest.fixture
def certificate_query_params() -> OffsetPaginationParams:
    return OffsetPaginationParams()


@pytest.fixture
def permissions_query_params() -> PermissionsQueryParams:
    return PermissionsQueryParams()


@pytest.fixture
def token_pagination_params() -> TokenPaginationParams:
    return TokenPaginationParams()


@pytest.fixture
def session_invoice_list_params() -> SessionInvoiceListParams:
    return SessionInvoiceListParams()


@pytest.fixture
def token_list_params() -> TokenListParams:
    return TokenListParams()
