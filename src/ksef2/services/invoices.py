from collections.abc import Callable, Iterator
from pathlib import Path
from typing import final

from ksef2.clients.invoices import InvoicesClient
from ksef2.core import exceptions
from ksef2.core.crypto import decrypt_aes_cbc
from ksef2.core.middlewares.auth import BearerTokenMiddleware
from ksef2.core.polling import poll_until
from ksef2.core.protocols import Middleware
from ksef2.core.stores import CertificateStore
from ksef2.logging import get_logger
from ksef2.domain.models.compression import CompressionType
from ksef2.domain.models.invoices import (
    ExportHandle,
    InvoiceExportStatusResponse,
    InvoiceMetadata,
    InvoicePackage,
    InvoicesFilter,
    QueryInvoicesMetadataResponse,
)
from ksef2.domain.models.pagination import InvoiceMetadataParams

logger = get_logger(__name__)


@final
class InvoicesService:
    def __init__(
        self,
        transport: Middleware,
        certificate_store: CertificateStore,
        *,
        client: InvoicesClient | None = None,
        ensure_encryption_certificates_loaded: Callable[[], None] | None = None,
    ) -> None:
        self._transport = transport
        self._download_transport = (
            transport._next
            if isinstance(transport, BearerTokenMiddleware)
            else transport
        )
        self._certificate_store = certificate_store
        self._client = client or InvoicesClient(transport)
        self._ensure_encryption_certificates_loaded = (
            ensure_encryption_certificates_loaded or (lambda: None)
        )

    def query_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> QueryInvoicesMetadataResponse:
        return self._client.query_metadata(
            filters=filters,
            params=params,
        )

    def query_metadata_pages(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> Iterator[QueryInvoicesMetadataResponse]:
        return self._client.query_metadata_pages(filters=filters, params=params)

    def all_metadata(
        self,
        *,
        filters: InvoicesFilter,
        params: InvoiceMetadataParams | None = None,
    ) -> Iterator[InvoiceMetadata]:
        return self._client.all_metadata(filters=filters, params=params)

    def download_invoice(self, *, ksef_number: str) -> bytes:
        return self._client.download_invoice(
            ksef_number=ksef_number,
        )

    def wait_for_invoice_download(
        self,
        *,
        ksef_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> bytes:
        """Poll until KSeF makes a processed invoice available for download."""

        def _poll() -> bytes | None:
            try:
                return self.download_invoice(ksef_number=ksef_number)
            except exceptions.KSeFApiError as exc:
                if (
                    exc.status_code == 400
                    and exc.exception_code == exceptions.ExceptionCode.NOT_PROCESSED_YET
                ):
                    return None
                raise

        result = poll_until(
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

    def schedule_export(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
    ) -> ExportHandle:
        self._ensure_encryption_certificates_loaded()
        cert = self._certificate_store.get_valid("symmetric_key_encryption")
        return self._client.schedule_export(
            filters=filters,
            encryption_certificate=cert.certificate,
            encryption_public_key_id=cert.public_key_id,
            only_metadata=only_metadata,
            compression_type=compression_type,
        )

    def get_export_status(
        self,
        *,
        reference_number: str,
    ) -> InvoiceExportStatusResponse:
        return self._client.get_export_status(
            reference_number=reference_number,
        )

    def fetch_package(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
        target_directory: Path | str = Path("."),
    ) -> list[Path]:
        """Download and decrypt all parts of an export package to disk."""
        target_path = Path(target_directory)
        target_path.mkdir(parents=True, exist_ok=True)

        saved_files: list[Path] = []

        for part in package.parts:
            logger.info(
                "Downloading export package part",
                part_name=part.part_name,
                package_part_url=str(part.url),
            )

            resp = self._download_transport.get(str(part.url))
            _ = resp.raise_for_status()

            zip_data = decrypt_aes_cbc(resp.content, key=export.aes_key, iv=export.iv)

            output_filename = part.part_name.replace(".aes", "")
            output_file = target_path / output_filename

            with open(output_file, "wb") as f:
                _ = f.write(zip_data)

            logger.info(
                "Saved decrypted export package part",
                output_file=str(output_file),
                part_name=part.part_name,
            )
            saved_files.append(output_file)

        return saved_files

    def fetch_package_bytes(
        self,
        *,
        package: InvoicePackage,
        export: ExportHandle,
    ) -> list[bytes]:
        """Download and decrypt all parts of an export package in memory."""
        result: list[bytes] = []
        for part in package.parts:
            logger.info(
                "Downloading export package part",
                part_name=part.part_name,
                package_part_url=str(part.url),
            )
            resp = self._download_transport.get(str(part.url))
            _ = resp.raise_for_status()
            result.append(
                decrypt_aes_cbc(resp.content, key=export.aes_key, iv=export.iv)
            )
        return result

    def wait_for_invoices(
        self,
        *,
        filters: InvoicesFilter,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> QueryInvoicesMetadataResponse:
        return poll_until(
            operation=lambda: self.query_metadata(filters=filters),
            retry_predicate=lambda result: not result.invoices,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFInvoiceQueryTimeoutError(
                timeout=timeout
            ),
        )

    def wait_for_export_package(
        self,
        *,
        reference_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> InvoicePackage:
        status = poll_until(
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
        assert status.package is not None  # guaranteed by retry condition
        return status.package

    def export_and_download(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
        compression_type: CompressionType | str | None = None,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> list[bytes]:
        """Schedule an export, wait for it, and download the decrypted package."""
        handle = self.schedule_export(
            filters=filters,
            only_metadata=only_metadata,
            compression_type=compression_type,
        )
        package = self.wait_for_export_package(
            reference_number=handle.reference_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )
        return self.fetch_package_bytes(
            package=package,
            export=handle,
        )
