import base64
from collections.abc import Iterator
from typing import final

from ksef2.clients._metadata_pagination import (
    MetadataBoundary,
    next_metadata_page_request,
)
from ksef2.core.crypto import encrypt_symmetric_key, generate_session_key
from ksef2.core.protocols import Middleware
from ksef2.domain.models.compression import CompressionType, normalize_compression_type
from ksef2.domain.models.invoices import (
    ExportHandle,
    ExportInvoicesPayload,
    InvoiceExportStatusResponse,
    InvoiceMetadata,
    InvoicesFilter,
    QueryInvoicesMetadataResponse,
)
from ksef2.domain.models.pagination import InvoiceMetadataParams
from ksef2.endpoints.invoices import InvoicesEndpoints
from ksef2.infra.mappers.invoices import from_spec, to_spec


@final
class InvoicesClient:
    """Low-level invoice API used by higher-level invoice services."""

    def __init__(self, transport: Middleware) -> None:
        self._endpoints = InvoicesEndpoints(transport)

    def query_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> QueryInvoicesMetadataResponse:
        """Fetch one page of invoice metadata matching the provided filters."""
        request = to_spec(filters)
        parameters = params or InvoiceMetadataParams()
        spec_resp = self._endpoints.query_metadata(
            body=request,
            **parameters.to_query_params(),
        )
        return from_spec(spec_resp)

    def query_metadata_pages(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> Iterator[QueryInvoicesMetadataResponse]:
        """Fetch metadata pages, following KSeF page and truncation mechanics."""
        current_filters = filters
        current_params = params or InvoiceMetadataParams()
        previous_truncation_boundary: MetadataBoundary | None = None

        while True:
            response = self.query_metadata(
                filters=current_filters,
                params=current_params,
            )
            yield response

            next_request = next_metadata_page_request(
                filters=current_filters,
                params=current_params,
                response=response,
                previous_truncation_boundary=previous_truncation_boundary,
            )
            if next_request is None:
                break

            (
                current_filters,
                current_params,
                previous_truncation_boundary,
            ) = next_request

    def all_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> Iterator[InvoiceMetadata]:
        """Iterate over all invoice metadata items matching the provided filters."""
        for page in self.query_metadata_pages(filters=filters, params=params):
            yield from page.invoices

    def download_invoice(self, *, ksef_number: str) -> bytes:
        """Download raw invoice bytes by KSeF number."""
        return self._endpoints.download(ksef_number=ksef_number)

    def schedule_export(
        self,
        *,
        filters: InvoicesFilter,
        encryption_certificate: str,
        encryption_public_key_id: str | None = None,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
    ) -> ExportHandle:
        """Schedule an export and return the handle needed to decrypt it later."""
        aes_key, iv = generate_session_key()
        encrypted_key = encrypt_symmetric_key(
            key=aes_key,
            cert_b64=encryption_certificate,
        )
        spec_request = to_spec(
            ExportInvoicesPayload(
                filter=filters,
                encrypted_symmetric_key=base64.b64encode(encrypted_key).decode(),
                initialization_vector=base64.b64encode(iv).decode(),
                public_key_id=encryption_public_key_id,
                only_metadata=only_metadata,
                compression_type=(
                    normalize_compression_type(compression_type)
                    if compression_type is not None
                    else None
                ),
            )
        )
        spec_resp = self._endpoints.export(body=spec_request)
        resp = from_spec(spec_resp)
        return ExportHandle(
            reference_number=resp.reference_number,
            aes_key=aes_key,
            iv=iv,
        )

    def get_export_status(
        self,
        *,
        reference_number: str,
    ) -> InvoiceExportStatusResponse:
        """Fetch export status and package metadata by export reference number."""
        spec_resp = self._endpoints.get_export_status(
            reference_number=reference_number,
        )
        return from_spec(spec_resp)
