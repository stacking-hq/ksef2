from typing import NotRequired, TypedDict, Unpack, final

from pydantic import TypeAdapter

from ksef2.core import routes
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.infra.schema.api import spec
from ksef2.infra.schema.api.supp.invoices import (
    InvoiceExportRequest,
    SendInvoiceRequest,
)

InvoiceMetadataQueryParams = TypedDict(
    "InvoiceMetadataQueryParams",
    {
        "sortOrder": NotRequired[str | None],
        "pageOffset": NotRequired[int | None],
        "pageSize": NotRequired[int | None],
    },
)
SessionInvoiceListQueryParams = TypedDict(
    "SessionInvoiceListQueryParams",
    {
        "pageSize": int,
    },
)


@final
class AsyncInvoicesEndpoints(AsyncBaseEndpoints):
    _METADATA_PARAMS = TypeAdapter(InvoiceMetadataQueryParams)
    _SESSION_LIST_PARAMS = TypeAdapter(SessionInvoiceListQueryParams)

    async def query_metadata(
        self,
        body: spec.InvoiceQueryFilters,
        **params: Unpack[InvoiceMetadataQueryParams],
    ) -> spec.QueryInvoicesMetadataResponse:
        return self._parse(
            await self._transport.post(
                path=routes.InvoiceRoutes.QUERY_METADATA,
                params=self.build_params(params, self._METADATA_PARAMS),
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.QueryInvoicesMetadataResponse,
        )

    async def export(self, body: InvoiceExportRequest) -> spec.ExportInvoicesResponse:
        return self._parse(
            await self._transport.post(
                path=routes.InvoiceRoutes.EXPORT,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.ExportInvoicesResponse,
        )

    async def get_export_status(
        self,
        reference_number: str,
    ) -> spec.InvoiceExportStatusResponse:
        return self._parse(
            await self._transport.get(
                path=routes.InvoiceRoutes.EXPORT_STATUS.format(
                    referenceNumber=reference_number
                ),
            ),
            spec.InvoiceExportStatusResponse,
        )

    async def download(self, ksef_number: str) -> bytes:
        return (
            await self._transport.get(
                path=routes.InvoiceRoutes.DOWNLOAD.format(ksefNumber=ksef_number),
            )
        ).content

    async def send(
        self,
        reference_number: str,
        body: SendInvoiceRequest,
    ) -> spec.SendInvoiceResponse:
        return self._parse(
            await self._transport.post(
                path=routes.InvoiceRoutes.SEND.format(referenceNumber=reference_number),
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.SendInvoiceResponse,
        )

    async def get_session_status(
        self,
        reference_number: str,
    ) -> spec.SessionStatusResponse:
        return self._parse(
            await self._transport.get(
                path=routes.InvoiceRoutes.SESSION_STATUS.format(
                    referenceNumber=reference_number
                ),
            ),
            spec.SessionStatusResponse,
        )

    async def list_session_invoices(
        self,
        reference_number: str,
        continuation_token: str | None = None,
        **params: Unpack[SessionInvoiceListQueryParams],
    ) -> spec.SessionInvoicesResponse:
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )

        return self._parse(
            await self._transport.get(
                path=routes.InvoiceRoutes.LIST_SESSION_INVOICES.format(
                    referenceNumber=reference_number
                ),
                params=self.build_params(params, self._SESSION_LIST_PARAMS),
                headers=headers,
            ),
            spec.SessionInvoicesResponse,
        )

    async def list_failed_session_invoices(
        self,
        reference_number: str,
        continuation_token: str | None = None,
        **params: Unpack[SessionInvoiceListQueryParams],
    ) -> spec.SessionInvoicesResponse:
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )

        return self._parse(
            await self._transport.get(
                path=routes.InvoiceRoutes.LIST_FAILED_SESSION_INVOICES.format(
                    referenceNumber=reference_number
                ),
                params=self.build_params(params, self._SESSION_LIST_PARAMS),
                headers=headers,
            ),
            spec.SessionInvoicesResponse,
        )

    async def get_session_invoice_status(
        self,
        reference_number: str,
        invoice_reference_number: str,
    ) -> spec.SessionInvoiceStatusResponse:
        return self._parse(
            await self._transport.get(
                path=routes.InvoiceRoutes.SESSION_INVOICE_STATUS.format(
                    referenceNumber=reference_number,
                    invoiceReferenceNumber=invoice_reference_number,
                ),
            ),
            spec.SessionInvoiceStatusResponse,
        )

    async def get_invoice_upo_by_ksef(
        self,
        reference_number: str,
        ksef_number: str,
    ) -> bytes:
        return (
            await self._transport.get(
                path=routes.InvoiceRoutes.INVOICE_UPO_BY_KSEF.format(
                    referenceNumber=reference_number,
                    ksefNumber=ksef_number,
                ),
            )
        ).content

    async def get_invoice_upo_by_reference(
        self,
        reference_number: str,
        invoice_reference_number: str,
    ) -> bytes:
        return (
            await self._transport.get(
                path=routes.InvoiceRoutes.INVOICE_UPO_BY_REFERENCE.format(
                    referenceNumber=reference_number,
                    invoiceReferenceNumber=invoice_reference_number,
                ),
            )
        ).content
