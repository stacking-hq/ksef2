from enum import Enum
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2._domain.models.batch import OpenBatchSessionResponse, PartUploadRequest
from ksef2._domain.models.session import (
    InvoiceStatusInfo,
    OpenOnlineSessionResponse,
    SessionInvoiceStatusResponse,
    SessionInvoicesResponse,
    SessionStatusResponse,
    SessionSummary,
    StatusInfo,
    Upo,
    UpoPage,
    ListSessionsResponse,
)
from ksef2._infra.schema.api import spec


@overload
def from_spec(
    response: spec.OpenOnlineSessionResponse,
) -> OpenOnlineSessionResponse: ...


@overload
def from_spec(response: spec.PartUploadRequest) -> PartUploadRequest: ...


@overload
def from_spec(response: spec.OpenBatchSessionResponse) -> OpenBatchSessionResponse: ...


@overload
def from_spec(response: spec.StatusInfo) -> StatusInfo: ...


@overload
def from_spec(response: spec.InvoiceStatusInfo) -> InvoiceStatusInfo: ...


@overload
def from_spec(response: spec.UpoPageResponse) -> UpoPage: ...


@overload
def from_spec(response: spec.UpoResponse) -> Upo: ...


@overload
def from_spec(response: spec.SessionStatusResponse) -> SessionStatusResponse: ...


@overload
def from_spec(
    response: spec.SessionInvoiceStatusResponse,
) -> SessionInvoiceStatusResponse: ...


@overload
def from_spec(response: spec.SessionInvoicesResponse) -> SessionInvoicesResponse: ...


@overload
def from_spec(response: spec.SessionsQueryResponseItem) -> SessionSummary: ...


@overload
def from_spec(response: spec.SessionsQueryResponse) -> ListSessionsResponse: ...


def from_spec(response: BaseModel | Enum) -> object:
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel | Enum) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(response: spec.OpenOnlineSessionResponse) -> OpenOnlineSessionResponse:
    return OpenOnlineSessionResponse(
        reference_number=response.referenceNumber,
        valid_until=response.validUntil,
    )


@_from_spec.register
def _(response: spec.PartUploadRequest) -> PartUploadRequest:
    return PartUploadRequest(
        ordinal_number=response.ordinalNumber,
        method=response.method,
        url=str(response.url),
        headers=response.headers,
    )


@_from_spec.register
def _(response: spec.OpenBatchSessionResponse) -> OpenBatchSessionResponse:
    return OpenBatchSessionResponse(
        reference_number=response.referenceNumber,
        part_upload_requests=[
            from_spec(part_upload_request)
            for part_upload_request in response.partUploadRequests
        ],
    )


@_from_spec.register
def _(response: spec.StatusInfo) -> StatusInfo:
    return StatusInfo(
        code=response.code,
        description=response.description,
        details=list(response.details) if response.details is not None else None,
    )


@_from_spec.register
def _(response: spec.InvoiceStatusInfo) -> InvoiceStatusInfo:
    return InvoiceStatusInfo(
        code=response.code,
        description=response.description,
        details=list(response.details) if response.details is not None else None,
        extensions=dict(response.extensions)
        if response.extensions is not None
        else None,
    )


@_from_spec.register
def _(response: spec.UpoPageResponse) -> UpoPage:
    return UpoPage(
        reference_number=response.referenceNumber,
        download_url=response.downloadUrl,
        download_url_expiration_date=response.downloadUrlExpirationDate,
    )


@_from_spec.register
def _(response: spec.UpoResponse) -> Upo:
    return Upo(pages=[from_spec(page) for page in response.pages])


@_from_spec.register
def _(response: spec.SessionStatusResponse) -> SessionStatusResponse:
    return SessionStatusResponse(
        status=from_spec(response.status),
        date_created=response.dateCreated,
        date_updated=response.dateUpdated,
        valid_until=response.validUntil,
        upo=from_spec(response.upo) if response.upo is not None else None,
        invoice_count=response.invoiceCount,
        successful_invoice_count=response.successfulInvoiceCount,
        failed_invoice_count=response.failedInvoiceCount,
    )


@_from_spec.register
def _(
    response: spec.SessionInvoiceStatusResponse,
) -> SessionInvoiceStatusResponse:
    return SessionInvoiceStatusResponse(
        ordinal_number=response.ordinalNumber,
        invoice_number=response.invoiceNumber,
        ksef_number=response.ksefNumber,
        reference_number=response.referenceNumber,
        invoice_hash=response.invoiceHash,
        invoice_file_name=response.invoiceFileName,
        acquisition_date=response.acquisitionDate,
        invoicing_date=response.invoicingDate,
        permanent_storage_date=response.permanentStorageDate,
        upo_download_url=response.upoDownloadUrl,
        upo_download_url_expiration_date=response.upoDownloadUrlExpirationDate,
        invoicing_mode=response.invoicingMode,
        status=from_spec(response.status),
    )


@_from_spec.register
def _(response: spec.SessionInvoicesResponse) -> SessionInvoicesResponse:
    return SessionInvoicesResponse(
        continuation_token=response.continuationToken,
        invoices=[from_spec(invoice) for invoice in response.invoices],
    )


@_from_spec.register
def _(response: spec.SessionsQueryResponseItem) -> SessionSummary:
    return SessionSummary(
        reference_number=response.referenceNumber,
        status=from_spec(response.status),
        date_created=response.dateCreated,
        date_updated=response.dateUpdated,
        valid_until=response.validUntil,
        total_invoice_count=response.totalInvoiceCount,
        successful_invoice_count=response.successfulInvoiceCount,
        failed_invoice_count=response.failedInvoiceCount,
    )


@_from_spec.register
def _(response: spec.SessionsQueryResponse) -> ListSessionsResponse:
    return ListSessionsResponse(
        continuation_token=response.continuationToken,
        sessions=[from_spec(session) for session in response.sessions],
    )
