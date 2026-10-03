import pytest

from ksef2._domain.models.pagination import (
    PermissionsQueryParams,
    OffsetPaginationParams,
    InvoiceMetadataParams,
)


@pytest.fixture
def bearer_headers() -> dict[str, str]:
    return {"Authorization": "Bearer <token>"}


@pytest.fixture
def pagination_params() -> OffsetPaginationParams:
    return OffsetPaginationParams()


@pytest.fixture
def permissions_params() -> PermissionsQueryParams:
    return PermissionsQueryParams()


@pytest.fixture
def certificate_params() -> OffsetPaginationParams:
    return OffsetPaginationParams()


@pytest.fixture
def invoice_params() -> InvoiceMetadataParams:
    return InvoiceMetadataParams()
