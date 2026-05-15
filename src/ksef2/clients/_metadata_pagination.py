from datetime import date, datetime
from typing import Literal, assert_never

from ksef2.core.exceptions import KSeFMetadataPaginationError
from ksef2.domain.models.invoices import (
    InvoiceMetadata,
    InvoicesFilter,
    QueryInvoicesMetadataResponse,
)
from ksef2.domain.models.pagination import InvoiceMetadataParams

type MetadataBoundary = date | datetime
type MetadataDateType = Literal["issue_date", "invoicing_date", "permanent_storage"]
type MetadataPageRequest = tuple[
    InvoicesFilter, InvoiceMetadataParams, MetadataBoundary | None
]


def next_metadata_page_request(
    *,
    filters: InvoicesFilter,
    params: InvoiceMetadataParams,
    response: QueryInvoicesMetadataResponse,
    previous_truncation_boundary: MetadataBoundary | None,
) -> MetadataPageRequest | None:
    if not response.has_more:
        return None

    if response.is_truncated:
        boundary = _last_metadata_boundary(filters=filters, response=response)
        if boundary == previous_truncation_boundary:
            raise KSeFMetadataPaginationError(
                "KSeF metadata pagination did not advance after truncation",
                date_type=filters.date_type,
                sort_order=params.sort_order,
                boundary=boundary,
            )
        return (
            _narrow_filters_to_boundary(
                filters=filters,
                params=params,
                boundary=boundary,
            ),
            params.with_page_offset(0),
            boundary,
        )

    return filters, params.next_page(), previous_truncation_boundary


def _last_metadata_boundary(
    *,
    filters: InvoicesFilter,
    response: QueryInvoicesMetadataResponse,
) -> MetadataBoundary:
    if not response.invoices:
        raise KSeFMetadataPaginationError(
            "KSeF returned a truncated metadata page without invoices",
            date_type=filters.date_type,
        )

    return _metadata_boundary(filters.date_type, response.invoices[-1])


def _metadata_boundary(
    date_type: MetadataDateType,
    invoice: InvoiceMetadata,
) -> MetadataBoundary:
    match date_type:
        case "issue_date":
            return invoice.issue_date
        case "invoicing_date":
            return invoice.invoicing_date
        case "permanent_storage":
            return invoice.permanent_storage_date
        case _ as unreachable:
            assert_never(unreachable)


def _narrow_filters_to_boundary(
    *,
    filters: InvoicesFilter,
    params: InvoiceMetadataParams,
    boundary: MetadataBoundary,
) -> InvoicesFilter:
    if params.sort_order == "asc":
        return filters.model_copy(update={"date_from": boundary})
    if params.sort_order == "desc":
        return filters.model_copy(update={"date_to": boundary})

    raise KSeFMetadataPaginationError(
        "Unsupported metadata sort order",
        sort_order=params.sort_order,
    )
