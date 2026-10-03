"""Async invoice metadata, download, and export branch client."""

import base64
from collections.abc import AsyncIterator
from typing import final

from ksef2._clients._metadata_pagination import (
    MetadataBoundary,
    next_metadata_page_request,
)
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.crypto import encrypt_symmetric_key, generate_session_key
from ksef2._domain.models.compression import CompressionType, normalize_compression_type
from ksef2._domain.models.invoices import (
    ExportHandle,
    ExportInvoicesPayload,
    InvoiceExportStatusResponse,
    InvoiceMetadata,
    InvoicesFilter,
    QueryInvoicesMetadataResponse,
)
from ksef2._domain.models.pagination import InvoiceMetadataParams
from ksef2._endpoints.async_invoices import AsyncInvoicesEndpoints
from ksef2._infra.mappers.invoices import from_spec, to_spec


@final
class AsyncInvoicesClient:
    """Async low-level invoice API used by higher-level invoice services.

    Catch ``KSeFException`` for SDK-classified failures raised by this branch,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(self, transport: AsyncMiddleware) -> None:
        """Create the client.

        Args:
            transport: Middleware chain used for requests to KSeF.
        """
        self._endpoints = AsyncInvoicesEndpoints(transport)

    async def query_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> QueryInvoicesMetadataResponse:
        """Fetch one page of invoice metadata matching the provided filters.

        Args:
            filters: Criteria selecting the invoices.
            params: Page size, page offset and sort order; defaults are used when ``None``.

        Returns:
            One page of invoice metadata. Use ``query_metadata_pages()`` or ``all_metadata()`` to iterate every page.

        Example:
            ```python
            from ksef2.models import InvoicesFilter

            page = await auth.invoices.query_metadata(
                filters=InvoicesFilter.for_buyer(date_from="2026-01-01T00:00:00+01:00"),
            )
            for invoice in page.invoices:
                print(invoice.ksef_number)
            ```
        """
        request = to_spec(filters)
        parameters = params or InvoiceMetadataParams()
        spec_resp = await self._endpoints.query_metadata(
            body=request,
            **parameters.to_query_params(),
        )
        return from_spec(spec_resp)

    async def query_metadata_pages(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> AsyncIterator[QueryInvoicesMetadataResponse]:
        """Fetch metadata pages, following KSeF page and truncation mechanics.

        Args:
            filters: Criteria selecting the invoices.
            params: Page size, page offset and sort order; defaults are used when ``None``.

        Yields:
            Each page of invoice metadata in order.

        Raises:
            KSeFMetadataPaginationError: If KSeF returns inconsistent pagination
                boundaries.
        """
        current_filters = filters
        current_params = params or InvoiceMetadataParams()
        previous_truncation_boundary: MetadataBoundary | None = None

        while True:
            response = await self.query_metadata(
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

    async def all_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> AsyncIterator[InvoiceMetadata]:
        """Iterate over all invoice metadata items matching the provided filters.

        Args:
            filters: Criteria selecting the invoices.
            params: Page size and sort order; defaults are used when ``None``.

        Yields:
            Metadata of each matching invoice, across all pages.

        Raises:
            KSeFMetadataPaginationError: If KSeF returns inconsistent pagination
                boundaries.

        Example:
            ```python
            from ksef2.models import InvoicesFilter

            filters = InvoicesFilter.for_seller(date_from="2026-01-01T00:00:00+01:00")
            async for invoice in auth.invoices.all_metadata(filters=filters):
                print(invoice.ksef_number, invoice.gross_amount)
            ```
        """
        async for page in self.query_metadata_pages(filters=filters, params=params):
            for invoice in page.invoices:
                yield invoice

    async def download_invoice(self, *, ksef_number: str) -> bytes:
        """Download raw invoice bytes by KSeF number.

        Args:
            ksef_number: KSeF number of the invoice.

        Returns:
            The invoice XML as bytes.

        Example:
            ```python
            xml_bytes = await auth.invoices.download_invoice(
                ksef_number="5265877635-20260101-0100100AB5B5-4B",
            )
            ```
        """
        return await self._endpoints.download(ksef_number=ksef_number)

    async def schedule_export(
        self,
        *,
        filters: InvoicesFilter,
        encryption_certificate: str,
        encryption_public_key_id: str | None = None,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
    ) -> ExportHandle:
        """Schedule an export and return the handle needed to decrypt it later.

        Args:
            filters: Criteria selecting the invoices to export.
            encryption_certificate: Base64 DER KSeF public-key certificate used to encrypt the export key, for example from ``client.encryption.get_certificates()``.
            encryption_public_key_id: Identifier of the public key in ``encryption_certificate``; ``None`` to omit it.
            only_metadata: Export only invoice metadata instead of full invoice XML.
            compression_type: Compression applied to the package; ``None`` for the server default.

        Returns:
            A handle holding the export reference number and the keys needed to decrypt the package.

        Raises:
            KSeFEncryptionError: If export key encryption fails.

        Example:
            ```python
            handle = await auth.invoices.schedule_export(
                filters=filters,
                encryption_certificate=certificate.certificate,
            )
            status = await auth.invoices.get_export_status(
                reference_number=handle.reference_number,
            )
            ```
        """
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
        spec_resp = await self._endpoints.export(body=spec_request)
        resp = from_spec(spec_resp)
        return ExportHandle(
            reference_number=resp.reference_number,
            aes_key=aes_key,
            iv=iv,
        )

    async def get_export_status(
        self,
        *,
        reference_number: str,
    ) -> InvoiceExportStatusResponse:
        """Fetch export status and package metadata by export reference number.

        Args:
            reference_number: Reference number of the export, from ``ExportHandle.reference_number``.

        Returns:
            The export status, with package metadata once the export is ready.
        """
        spec_resp = await self._endpoints.get_export_status(
            reference_number=reference_number,
        )
        return from_spec(spec_resp)
