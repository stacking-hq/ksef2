"""Async high-level invoice workflow service."""

import asyncio
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
)
from pathlib import Path
from typing import final, override

from typing_extensions import deprecated

from ksef2._clients._async_handles import AsyncOperationHandle
from ksef2._clients._async_pager import AsyncPager
from ksef2._clients.async_invoices import AsyncInvoicesClient
from ksef2._clients.exported_invoices import ExportedInvoices
from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.async_external_transfer import AsyncExternalTransferClient
from ksef2._core.crypto import decrypt_aes_cbc
from ksef2._core.polling import async_poll_until
from ksef2._core.stores import CertificateStoreProtocol
from ksef2._domain.models.compression import CompressionType
from ksef2._domain.models.invoices import (
    ExportHandle,
    InvoiceExportStatusResponse,
    InvoiceMetadata,
    InvoicePackage,
    InvoicesFilter,
    PackagePart,
    QueryInvoicesMetadataResponse,
)
from ksef2._domain.models.pagination import InvoiceMetadataParams
from ksef2._logging import get_logger
from ksef2._services.export_parts import safe_part_filename

logger = get_logger(__name__)


@final
class AsyncExportJob(
    AsyncOperationHandle[InvoiceExportStatusResponse, ExportedInvoices]
):
    """Handle to a scheduled invoice export.

    Returned by ``auth.invoices.export()``. ``wait()`` polls until KSeF has built
    the package, then downloads, decrypts and joins its parts into an
    ``ExportedInvoices`` result. The handle holds the keys needed to decrypt the
    package, so keep it in memory only.

    Raises:
        KSeFApiError: If KSeF returns an API error response.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(
        self,
        reference_number: str,
        *,
        get_status: Callable[[], Awaitable[InvoiceExportStatusResponse]],
        download_parts: Callable[[InvoicePackage], Awaitable[list[bytes]]],
    ) -> None:
        """Create the handle.

        Args:
            reference_number: Reference number of the export.
            get_status: Coroutine function returning the current export status.
            download_parts: Coroutine function that downloads and decrypts every part of a package, in order.
        """
        super().__init__(reference_number)
        self._get_status = get_status
        self._download_parts = download_parts

    @override
    async def get_status(self) -> InvoiceExportStatusResponse:
        """Fetch the export's current status without waiting.

        Returns:
            The export status, with package metadata once the export is ready.
        """
        return await self._get_status()

    @override
    def _is_pending(self, status: InvoiceExportStatusResponse) -> bool:
        return status.status.code < 200

    @override
    def _check_status(self, status: InvoiceExportStatusResponse) -> None:
        if status.status.code >= 210:
            raise exceptions.KSeFExportFailedError(
                reference_number=self.reference_number,
                status_code=status.status.code,
                description=status.status.description,
                details=status.status.details,
            )

    @override
    def _timeout_error(self, timeout: float) -> BaseException:
        return exceptions.KSeFExportTimeoutError(
            reference_number=self.reference_number,
            timeout=timeout,
        )

    @override
    async def _finish(self, status: InvoiceExportStatusResponse) -> ExportedInvoices:
        package = status.package
        parts = await self._download_parts(package) if package else []
        return ExportedInvoices(parts, package=package)

    async def wait(
        self,
        *,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> ExportedInvoices:
        """Poll until the export is ready, then download and decrypt the package.

        Args:
            timeout: Maximum number of seconds to wait for the export to become ready.
            poll_interval: Delay in seconds between export status checks.

        Returns:
            The decrypted package: iterate ``invoices()``, read ``metadata`` or ``save()`` it to disk.

        Raises:
            KSeFExportFailedError: If KSeF reports that the export failed, was cancelled or expired.
            KSeFExportTimeoutError: If polling exceeds ``timeout``.
            KSeFEncryptionError: If a downloaded package part cannot be decrypted.
            KSeFExternalTransferError: If external storage rejects a part download or
                its outcome cannot be determined.
        """
        return await self._wait(timeout, poll_interval)


@final
class AsyncInvoicesService:
    """Async invoice workflows with encryption, polling, and export helpers.

    Catch ``KSeFException`` for SDK-classified failures raised by this service,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(
        self,
        transport: AsyncMiddleware,
        download_transport: AsyncMiddleware,
        certificate_store: CertificateStoreProtocol,
        *,
        client: AsyncInvoicesClient | None = None,
        ensure_encryption_certificates_loaded: Callable[[], Awaitable[None]]
        | None = None,
    ) -> None:
        """Create the service.

        Args:
            transport: Middleware chain used for authenticated API requests.
            download_transport: Middleware used to download export parts from external storage.
            certificate_store: Store holding the KSeF public-key certificates used to encrypt export keys.
            client: Invoices client to delegate to; one is created from ``transport`` when ``None``.
            ensure_encryption_certificates_loaded: Coroutine function that loads the encryption certificates into ``certificate_store`` before they are needed; no-op when ``None``.
        """
        self._transport = transport
        self._external_transfers = AsyncExternalTransferClient(download_transport)
        self._certificate_store = certificate_store
        self._client = client or AsyncInvoicesClient(transport)
        self._ensure_encryption_certificates_loaded = (
            ensure_encryption_certificates_loaded or self._noop
        )

    async def _noop(self) -> None:
        return None

    def search(
        self,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> AsyncPager[InvoiceMetadata]:
        """Search invoice metadata, following KSeF page and truncation mechanics.

        Nothing is requested until the result is consumed. Iterate it for every
        matching invoice, call ``pages()`` for page-sized lists, ``first_page()``
        for one request only, or ``wait()`` to poll until KSeF has indexed at
        least one matching invoice.

        Args:
            filters: Criteria selecting the invoices.
            params: Page size and sort order; defaults are used when ``None``.

        Returns:
            A paging object over the metadata of matching invoices.

        Raises:
            KSeFMetadataPaginationError: If KSeF returns inconsistent pagination
                boundaries while paging.

        Example:
            ```python
            from ksef2.models import InvoicesFilter

            filters = InvoicesFilter.for_seller(date_from="2026-01-01T00:00:00+01:00")
            async for invoice in auth.invoices.search(filters):
                print(invoice.ksef_number, invoice.gross_amount)
            ```
        """

        async def _pages() -> AsyncGenerator[list[InvoiceMetadata], None]:
            async for page in self._client.query_metadata_pages(
                filters=filters,
                params=params,
            ):
                yield list(page.invoices)

        return AsyncPager(
            _pages,
            timeout_error=lambda timeout: exceptions.KSeFInvoiceQueryTimeoutError(
                timeout=timeout
            ),
        )

    async def download(
        self,
        ksef_number: str,
        *,
        timeout: float | None = None,
        poll_interval: float = 2.0,
    ) -> bytes:
        """Download one processed invoice by KSeF number.

        Args:
            ksef_number: KSeF number of the invoice.
            timeout: Seconds to keep polling while KSeF has not made the invoice available yet; ``None`` tries once.
            poll_interval: Delay in seconds between download attempts when ``timeout`` is set.

        Returns:
            The invoice XML as bytes.

        Raises:
            KSeFApiError: If KSeF rejects the download, for example because the invoice is not processed yet and ``timeout`` is ``None``.
            KSeFInvoiceDownloadTimeoutError: If ``timeout`` is set and polling exceeds it.

        Example:
            ```python
            xml = await auth.invoices.download(ksef_number, timeout=60)
            ```
        """
        if timeout is None:
            return await self._client.download_invoice(ksef_number=ksef_number)
        return await self._poll_download(
            ksef_number=ksef_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def export(
        self,
        filters: InvoicesFilter,
        *,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
    ) -> AsyncExportJob:
        """Schedule an encrypted invoice export.

        Args:
            filters: Criteria selecting the invoices to export.
            only_metadata: Export only invoice metadata instead of full invoice XML.
            compression_type: Compression applied to the package; ``None`` for the server default.

        Returns:
            A handle to the export. Call its ``wait()`` to download the decrypted package.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If export key encryption fails.

        Example:
            ```python
            job = await auth.invoices.export(filters)
            package = await job.wait()
            package.save("out/")
            ```
        """
        handle = await self._schedule_export(
            filters=filters,
            only_metadata=only_metadata,
            compression_type=compression_type,
        )

        async def _download_parts(package: InvoicePackage) -> list[bytes]:
            return await self._download_package_parts(package=package, export=handle)

        return AsyncExportJob(
            handle.reference_number,
            get_status=lambda: self._client.get_export_status(
                reference_number=handle.reference_number
            ),
            download_parts=_download_parts,
        )

    @deprecated(
        "`query_metadata()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `search()` instead."
    )
    def query_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> Coroutine[None, None, QueryInvoicesMetadataResponse]:
        """Deprecated: fetch one invoice metadata page matching the provided filters.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``search()`` instead; ``first_page()`` fetches one page.

        Args:
            filters: Criteria selecting the invoices.
            params: Page size, page offset and sort order; defaults are used when ``None``.

        Returns:
            One page of invoice metadata.
        """
        return self._client.query_metadata(filters=filters, params=params)

    @deprecated(
        "`query_metadata_pages()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `search()` instead."
    )
    async def query_metadata_pages(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> AsyncIterator[QueryInvoicesMetadataResponse]:
        """Deprecated: fetch metadata pages, following KSeF page and truncation mechanics.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``search().pages()`` instead.

        Args:
            filters: Criteria selecting the invoices.
            params: Page size, page offset and sort order; defaults are used when ``None``.

        Yields:
            Each page of invoice metadata in order.

        Raises:
            KSeFMetadataPaginationError: If KSeF returns inconsistent pagination
                boundaries.
        """
        async for page in self._client.query_metadata_pages(
            filters=filters,
            params=params,
        ):
            yield page

    @deprecated(
        "`all_metadata()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `search()` instead."
    )
    async def all_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> AsyncIterator[InvoiceMetadata]:
        """Deprecated: iterate over all invoice metadata items matching the provided filters.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``search()`` instead.

        Args:
            filters: Criteria selecting the invoices.
            params: Page size and sort order; defaults are used when ``None``.

        Yields:
            Metadata of each matching invoice, across all pages.

        Raises:
            KSeFMetadataPaginationError: If KSeF returns inconsistent pagination
                boundaries.
        """
        async for invoice in self._client.all_metadata(filters=filters, params=params):
            yield invoice

    @deprecated(
        "`download_invoice()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `download()` instead."
    )
    def download_invoice(self, *, ksef_number: str) -> Coroutine[None, None, bytes]:
        """Deprecated: download one processed invoice by KSeF number.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``download()`` instead.

        Args:
            ksef_number: KSeF number of the invoice.

        Returns:
            The invoice XML as bytes.
        """
        return self._client.download_invoice(ksef_number=ksef_number)

    @deprecated(
        "`wait_for_invoice_download()` is deprecated and will be removed in "
        "ksef2 1.10.0; use `download()` instead."
    )
    def wait_for_invoice_download(
        self,
        *,
        ksef_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> Coroutine[None, None, bytes]:
        """Deprecated: poll until KSeF makes a processed invoice available for download.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``download(ksef_number, timeout=...)`` instead.

        Args:
            ksef_number: KSeF number of the invoice.
            timeout: Maximum number of seconds to wait before giving up.
            poll_interval: Delay in seconds between download attempts.

        Returns:
            The invoice XML as bytes.

        Raises:
            KSeFInvoiceDownloadTimeoutError: If polling exceeds ``timeout``.
        """
        return self._poll_download(
            ksef_number=ksef_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def _poll_download(
        self,
        *,
        ksef_number: str,
        timeout: float,
        poll_interval: float,
    ) -> bytes:
        async def _poll() -> bytes | None:
            try:
                return await self._client.download_invoice(ksef_number=ksef_number)
            except exceptions.KSeFApiError as exc:
                if (
                    exc.status_code == 400
                    and exc.exception_code == exceptions.ExceptionCode.NOT_PROCESSED_YET
                ):
                    return None
                raise

        result = await async_poll_until(
            operation=_poll,
            retry_predicate=lambda invoice: invoice is None,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFInvoiceDownloadTimeoutError(
                ksef_number=ksef_number,
                timeout=timeout,
            ),
        )
        assert result is not None
        return result

    @deprecated(
        "`schedule_export()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `export()` instead."
    )
    def schedule_export(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
    ) -> Coroutine[None, None, ExportHandle]:
        """Deprecated: schedule an encrypted invoice export.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``export()`` instead.

        Args:
            filters: Criteria selecting the invoices to export.
            only_metadata: Export only invoice metadata instead of full invoice XML.
            compression_type: Compression applied to the package; ``None`` for the server default.

        Returns:
            A handle holding the export reference number and the keys needed to decrypt the package.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If export key encryption fails.
        """
        return self._schedule_export(
            filters=filters,
            only_metadata=only_metadata,
            compression_type=compression_type,
        )

    async def _schedule_export(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool,
        compression_type: CompressionType | str | None,
    ) -> ExportHandle:
        await self._ensure_encryption_certificates_loaded()
        cert = self._certificate_store.get_valid("symmetric_key_encryption")
        return await self._client.schedule_export(
            filters=filters,
            encryption_certificate=cert.certificate,
            encryption_public_key_id=cert.public_key_id,
            only_metadata=only_metadata,
            compression_type=compression_type,
        )

    @deprecated(
        "`get_export_status()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `export()` instead."
    )
    def get_export_status(
        self,
        *,
        reference_number: str,
    ) -> Coroutine[None, None, InvoiceExportStatusResponse]:
        """Deprecated: fetch the current status for a scheduled invoice export.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``export()`` and ``ExportJob.get_status()`` instead.

        Args:
            reference_number: Reference number of the export, from ``ExportHandle.reference_number``.

        Returns:
            The export status, with package metadata once the export is ready.
        """
        return self._client.get_export_status(reference_number=reference_number)

    @deprecated(
        "`fetch_package()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `export().wait()` instead."
    )
    def fetch_package(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
        target_directory: Path | str = ".",
    ) -> Coroutine[None, None, list[Path]]:
        """Deprecated: download and decrypt all parts of an export package to disk.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``export().wait()`` and ``ExportedInvoices.save()`` instead.

        Args:
            package: Package metadata from the export status.
            export: Handle returned when the export was scheduled; supplies the decryption keys.
            target_directory: Directory to write the decrypted parts to. Defaults to the current directory.

        Returns:
            The paths of the written part files.

        Raises:
            KSeFEncryptionError: If a downloaded package part cannot be decrypted.
            ValueError: If a package part name is unsafe for local filesystem output.
            OSError: If the target directory or output file cannot be written.
            KSeFExternalTransferError: If external storage rejects a part download or
                its outcome cannot be determined.
        """
        return self._fetch_package(
            package=package, export=export, target_directory=target_directory
        )

    async def _fetch_package(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
        target_directory: Path | str = ".",
    ) -> list[Path]:
        target_path = Path(target_directory)
        await asyncio.to_thread(target_path.mkdir, parents=True, exist_ok=True)

        saved_files: list[Path] = []

        for part in sorted(package.parts, key=lambda part: part.ordinal_number):
            zip_data = await self._download_part(part=part, export=export)

            output_filename = safe_part_filename(part.part_name)
            output_file = target_path / output_filename
            await asyncio.to_thread(output_file.write_bytes, zip_data)

            logger.info(
                "Saved decrypted export package part",
                output_file=str(output_file),
                part_name=part.part_name,
            )
            saved_files.append(output_file)

        return saved_files

    @deprecated(
        "`fetch_package_bytes()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `export().wait()` instead."
    )
    def fetch_package_bytes(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
    ) -> Coroutine[None, None, list[bytes]]:
        """Deprecated: download and decrypt all parts of an export package in memory.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``export().wait()`` and ``ExportedInvoices.archive`` instead.

        Args:
            package: Package metadata from the export status.
            export: Handle returned when the export was scheduled; supplies the decryption keys.

        Returns:
            The decrypted package parts, in order.

        Raises:
            KSeFEncryptionError: If a downloaded package part cannot be decrypted.
            KSeFExternalTransferError: If external storage rejects a part download or
                its outcome cannot be determined.
        """
        return self._download_package_parts(package=package, export=export)

    async def _download_package_parts(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
    ) -> list[bytes]:
        return [
            await self._download_part(part=part, export=export)
            for part in sorted(package.parts, key=lambda part: part.ordinal_number)
        ]

    async def _download_part(self, *, part: PackagePart, export: ExportHandle) -> bytes:
        logger.info(  # pyright: ignore[reportAny]
            "Downloading export package part",
            part_name=part.part_name,
            part_ordinal=part.ordinal_number,
            reference_number=export.reference_number,
        )
        encrypted_part = await self._external_transfers.download_part(
            url=str(part.url),
            reference_number=export.reference_number,
            part_ordinal=part.ordinal_number,
        )
        return await asyncio.to_thread(
            decrypt_aes_cbc,
            encrypted_part,
            key=export.aes_key,
            iv=export.iv,
        )

    @deprecated(
        "`wait_for_invoices()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `search().wait()` instead."
    )
    def wait_for_invoices(
        self,
        *,
        filters: InvoicesFilter,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> Coroutine[None, None, QueryInvoicesMetadataResponse]:
        """Deprecated: poll invoice metadata until at least one invoice matches the filters.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``search(filters).wait()`` instead.

        Args:
            filters: Criteria selecting the invoices.
            timeout: Maximum number of seconds to wait before giving up.
            poll_interval: Delay in seconds between queries.

        Returns:
            The first metadata page that contains at least one invoice.

        Raises:
            KSeFInvoiceQueryTimeoutError: If polling exceeds ``timeout``.
        """
        return async_poll_until(
            operation=lambda: self._client.query_metadata(filters=filters),
            retry_predicate=lambda result: not result.invoices,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFInvoiceQueryTimeoutError(
                timeout=timeout
            ),
        )

    @deprecated(
        "`wait_for_export_package()` is deprecated and will be removed in "
        "ksef2 1.10.0; use `export().wait()` instead."
    )
    def wait_for_export_package(
        self,
        *,
        reference_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> Coroutine[None, None, InvoicePackage]:
        """Deprecated: poll export status until KSeF exposes a downloadable package.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``export().wait()`` instead.

        Args:
            reference_number: Reference number of the export, from ``ExportHandle.reference_number``.
            timeout: Maximum number of seconds to wait before giving up.
            poll_interval: Delay in seconds between export status checks.

        Returns:
            The package metadata once the export is ready.

        Raises:
            KSeFExportTimeoutError: If polling exceeds ``timeout``.
        """
        return self._wait_for_export_package(
            reference_number=reference_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def _wait_for_export_package(
        self,
        *,
        reference_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> InvoicePackage:
        status = await async_poll_until(
            operation=lambda: self._client.get_export_status(
                reference_number=reference_number
            ),
            retry_predicate=lambda status: (
                not (status.package and status.package.parts)
            ),
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFExportTimeoutError(
                reference_number=reference_number,
                timeout=timeout,
            ),
        )
        assert status.package is not None
        return status.package

    @deprecated(
        "`export_and_download()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `export().wait()` instead."
    )
    def export_and_download(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> Coroutine[None, None, list[bytes]]:
        """Deprecated: schedule an export, wait for it, and download the decrypted package.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``export().wait()`` instead; ``ExportedInvoices.archive`` is the joined ZIP.

        Args:
            filters: Criteria selecting the invoices to export.
            only_metadata: Export only invoice metadata instead of full invoice XML.
            compression_type: Compression applied to the package; ``None`` for the server default.
            timeout: Maximum number of seconds to wait for the export to become ready.
            poll_interval: Delay in seconds between export status checks.

        Returns:
            The decrypted package parts, in order. Concatenate them to obtain the package archive.

        Raises:
            NoCertificateAvailableError: If no valid symmetric-key certificate is
                available.
            KSeFEncryptionError: If export key encryption or package decryption fails.
            KSeFExportTimeoutError: If polling exceeds ``timeout``.
            KSeFExternalTransferError: If external storage rejects a part download or
                its outcome cannot be determined.
        """
        return self._export_and_download(
            filters=filters,
            only_metadata=only_metadata,
            compression_type=compression_type,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def _export_and_download(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> list[bytes]:
        handle = await self._schedule_export(
            filters=filters,
            only_metadata=only_metadata,
            compression_type=compression_type,
        )
        status = await async_poll_until(
            operation=lambda: self._client.get_export_status(
                reference_number=handle.reference_number
            ),
            retry_predicate=lambda status: (
                not (status.package and status.package.parts)
            ),
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFExportTimeoutError(
                reference_number=handle.reference_number,
                timeout=timeout,
            ),
        )
        assert status.package is not None
        return await self._download_package_parts(package=status.package, export=handle)
