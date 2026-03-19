from collections.abc import Callable
from pathlib import Path
from typing import final

from tenacity import RetryError, retry, retry_if_result, stop_after_delay, wait_fixed

from ksef2.clients.invoices import InvoicesClient
from ksef2.core import exceptions
from ksef2.core.crypto import decrypt_aes_cbc
from ksef2.core.middlewares.auth import BearerTokenMiddleware
from ksef2.core.protocols import Middleware
from ksef2.core.stores import CertificateStore
from ksef2.logging import get_logger
from ksef2.domain.models.invoices import (
    ExportHandle,
    InvoiceExportStatusResponse,
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

    def download_invoice(self, *, ksef_number: str) -> bytes:
        return self._client.download_invoice(
            ksef_number=ksef_number,
        )

    def schedule_export(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
    ) -> ExportHandle:
        self._ensure_encryption_certificates_loaded()
        cert = self._certificate_store.get_valid("symmetric_key_encryption")
        return self._client.schedule_export(
            filters=filters,
            encryption_certificate=cert.certificate,
            only_metadata=only_metadata,
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

        retry_predicate: Callable[[QueryInvoicesMetadataResponse], bool] = lambda s: (
            not s.invoices
        )

        @retry(
            stop=stop_after_delay(timeout),
            wait=wait_fixed(poll_interval),
            retry=retry_if_result(retry_predicate),
            reraise=True,
        )
        def _poll() -> QueryInvoicesMetadataResponse:
            return self.query_metadata(filters=filters)

        try:
            return _poll()
        except RetryError:
            raise exceptions.KSeFInvoiceQueryTimeoutError(timeout=timeout)

    def wait_for_export_package(
        self,
        *,
        reference_number: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> InvoicePackage:

        retry_predicate: Callable[[InvoiceExportStatusResponse], bool] = lambda s: (
            not (s.package and s.package.parts)
        )

        @retry(
            stop=stop_after_delay(timeout),
            wait=wait_fixed(poll_interval),
            retry=retry_if_result(retry_predicate),
            reraise=True,
        )
        def _poll() -> InvoiceExportStatusResponse:
            return self.get_export_status(reference_number=reference_number)

        try:
            status = _poll()
        except RetryError:
            raise exceptions.KSeFExportTimeoutError(
                reference_number=reference_number,
                timeout=timeout,
            )
        assert status.package is not None  # guaranteed by retry condition
        return status.package

    def export_and_download(
        self,
        *,
        filters: InvoicesFilter,
        only_metadata: bool = False,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> list[bytes]:
        """Schedule an export, wait for it, and download the decrypted package."""
        handle = self.schedule_export(
            filters=filters,
            only_metadata=only_metadata,
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
