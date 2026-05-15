import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import final

from ksef2.clients.async_invoices import AsyncInvoicesClient
from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.crypto import decrypt_aes_cbc
from ksef2.core.polling import async_poll_until
from ksef2.core.stores import CertificateStore
from ksef2.domain.models.invoices import (
    ExportHandle,
    InvoiceExportStatusResponse,
    InvoiceMetadata,
    InvoicePackage,
    InvoicesFilter,
    QueryInvoicesMetadataResponse,
)
from ksef2.domain.models.pagination import InvoiceMetadataParams
from ksef2.logging import get_logger

logger = get_logger(__name__)


@final
class AsyncInvoicesService:
    def __init__(
        self,
        transport: AsyncMiddleware,
        download_transport: AsyncMiddleware,
        certificate_store: CertificateStore,
        *,
        client: AsyncInvoicesClient | None = None,
        ensure_encryption_certificates_loaded: Callable[[], Awaitable[None]]
        | None = None,
    ) -> None:
        self._transport = transport
        self._download_transport = download_transport
        self._certificate_store = certificate_store
        self._client = client or AsyncInvoicesClient(transport)
        self._ensure_encryption_certificates_loaded = (
            ensure_encryption_certificates_loaded or self._noop
        )

    async def _noop(self) -> None:
        return None

    async def query_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> QueryInvoicesMetadataResponse:
        return await self._client.query_metadata(filters=filters, params=params)

    async def query_metadata_pages(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> AsyncIterator[QueryInvoicesMetadataResponse]:
        async for page in self._client.query_metadata_pages(
            filters=filters,
            params=params,
        ):
            yield page

    async def all_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> AsyncIterator[InvoiceMetadata]:
        async for invoice in self._client.all_metadata(filters=filters, params=params):
            yield invoice

    async def download_invoice(self, *, ksef_number: str) -> bytes:
        return await self._client.download_invoice(ksef_number=ksef_number)

    async def wait_for_invoice_download(
        self,
        *,
        ksef_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> bytes:
        """Poll until KSeF makes a processed invoice available for download."""

        async def _poll() -> bytes | None:
            try:
                return await self.download_invoice(ksef_number=ksef_number)
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

    async def schedule_export(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
    ) -> ExportHandle:
        await self._ensure_encryption_certificates_loaded()
        cert = self._certificate_store.get_valid("symmetric_key_encryption")
        return await self._client.schedule_export(
            filters=filters,
            encryption_certificate=cert.certificate,
            encryption_public_key_id=cert.public_key_id,
            only_metadata=only_metadata,
        )

    async def get_export_status(
        self,
        *,
        reference_number: str,
    ) -> InvoiceExportStatusResponse:
        return await self._client.get_export_status(reference_number=reference_number)

    async def fetch_package(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
        target_directory: Path | str = Path("."),
    ) -> list[Path]:
        target_path = Path(target_directory)
        await asyncio.to_thread(target_path.mkdir, parents=True, exist_ok=True)

        saved_files: list[Path] = []

        for part in package.parts:
            logger.info(
                "Downloading export package part",
                part_name=part.part_name,
                package_part_url=str(part.url),
            )
            resp = await self._download_transport.get(str(part.url))
            _ = resp.raise_for_status()

            zip_data = await asyncio.to_thread(
                decrypt_aes_cbc,
                resp.content,
                key=export.aes_key,
                iv=export.iv,
            )

            sanitized_part_name = Path(part.part_name.replace("\\", "/")).name
            output_filename = sanitized_part_name.removesuffix(".aes")
            if (
                "\x00" in output_filename
                or output_filename.startswith(".")
                or output_filename in {"", ".", ".."}
            ):
                raise ValueError(
                    f"Invalid export package part name: {part.part_name!r}"
                )
            output_file = target_path / output_filename
            await asyncio.to_thread(output_file.write_bytes, zip_data)

            logger.info(
                "Saved decrypted export package part",
                output_file=str(output_file),
                part_name=part.part_name,
            )
            saved_files.append(output_file)

        return saved_files

    async def fetch_package_bytes(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
    ) -> list[bytes]:
        result: list[bytes] = []
        for part in package.parts:
            logger.info(
                "Downloading export package part",
                part_name=part.part_name,
                package_part_url=str(part.url),
            )
            resp = await self._download_transport.get(str(part.url))
            _ = resp.raise_for_status()
            result.append(
                await asyncio.to_thread(
                    decrypt_aes_cbc,
                    resp.content,
                    key=export.aes_key,
                    iv=export.iv,
                )
            )
        return result

    async def wait_for_invoices(
        self,
        *,
        filters: InvoicesFilter,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> QueryInvoicesMetadataResponse:
        return await async_poll_until(
            operation=lambda: self.query_metadata(filters=filters),
            retry_predicate=lambda result: not result.invoices,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFInvoiceQueryTimeoutError(
                timeout=timeout
            ),
        )

    async def wait_for_export_package(
        self,
        *,
        reference_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> InvoicePackage:
        status = await async_poll_until(
            operation=lambda: self.get_export_status(reference_number=reference_number),
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

    async def export_and_download(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> list[bytes]:
        handle = await self.schedule_export(
            filters=filters,
            only_metadata=only_metadata,
        )
        package = await self.wait_for_export_package(
            reference_number=handle.reference_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )
        return await self.fetch_package_bytes(package=package, export=handle)
