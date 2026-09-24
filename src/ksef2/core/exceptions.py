"""Public exception hierarchy raised by the KSeF SDK."""

from typing import Any, Literal
from pydantic import BaseModel
from enum import IntEnum

from ksef2.domain.models.session import SessionInvoiceStatusResponse


class ExceptionCode(IntEnum):
    """Enumeration of all possible exception codes."""

    UNKNOWN_ERROR = 10000
    OBJECT_ALREADY_EXISTS = 30001
    VALIDATION_ERROR = 21405
    UPO_NOT_FOUND = 21178
    NOT_PROCESSED_YET = 21165

    @staticmethod
    def from_code(code: int | None) -> "ExceptionCode":
        """Return a known exception code or ``UNKNOWN_ERROR`` for unknown values."""
        try:
            return ExceptionCode(code)
        except ValueError:
            return ExceptionCode.UNKNOWN_ERROR


class KSeFException(Exception):
    """Base exception for all KSeF SDK errors."""

    code: str = "SDK_ERROR"

    def __init__(self, message: str, **context: Any):
        super().__init__(message)
        self.context: dict[str, Any] = context
        self.context["code"] = self.code


class KSeFClientClosedError(KSeFException):
    """Raised when an SDK client is used after it has been closed."""

    code: str = "CLIENT_CLOSED"


class KSeFUnsupportedEnvironmentError(KSeFException):
    """Raised when an operation is not available in the selected environment."""

    code: str = "UNSUPPORTED_ENVIRONMENT"


class KSeFValidationError(KSeFException):
    """Raised when validation fails."""

    code: str = "VALIDATION_ERROR"

    def __init__(self, message: str, **context: Any):
        super().__init__(message, **context)
        self.context["code"] = self.code


class KSeFInvoiceRenderingError(KSeFException):
    """Raised when invoice rendering fails."""

    code: str = "INVOICE_RENDERING_ERROR"


class KSeFApiError(KSeFException):
    """Raised on 4xx/5xx responses from the KSeF API."""

    code: str = "API_ERROR"

    def __init__(
        self,
        status_code: int,
        exception_code: ExceptionCode,
        message: str,
        response: BaseModel | None = None,
    ) -> None:
        self.status_code = status_code
        self.response = response
        self.exception_code = exception_code

        msg = (
            f"{self.code}/{status_code}: {message}\n"
            f"Response: {response.model_dump_json(indent=2) if response else '<none>'}"
        )

        super().__init__(msg)


class KSeFAuthError(KSeFApiError):
    """Raised on 401/403 responses."""

    code: str = "AUTH_ERROR"

    def __init__(
        self,
        status_code: int,
        message: str,
        response: BaseModel | None = None,
    ) -> None:
        super().__init__(status_code, ExceptionCode.UNKNOWN_ERROR, message, response)


class KSeFRateLimitError(KSeFApiError):
    """Raised on 429 responses. Check ``retry_after`` for seconds to wait."""

    code: str = "RATE_LIMIT_ERROR"

    def __init__(
        self,
        retry_after: int | None,
        message: str,
        response: BaseModel | None = None,
    ) -> None:
        self.retry_after = retry_after
        self.response = response
        super().__init__(429, ExceptionCode.UNKNOWN_ERROR, message, response)


class KSeFExternalTransferError(KSeFException):
    """Raised when a presigned external-storage transfer fails."""

    code: str = "EXTERNAL_TRANSFER_ERROR"

    def __init__(
        self,
        *,
        operation: Literal["upload", "download"],
        host: str,
        reference_number: str,
        part_ordinal: int,
        status_code: int | None = None,
        outcome_ambiguous: bool = False,
    ) -> None:
        self.operation: Literal["upload", "download"] = operation
        self.host = host
        self.reference_number = reference_number
        self.part_ordinal = part_ordinal
        self.status_code = status_code
        self.outcome_ambiguous = outcome_ambiguous

        status = (
            f"status {status_code}"
            if status_code is not None
            else "no response received"
        )
        super().__init__(
            f"External storage {operation} failed for host {host} "
            f"({status}, reference {reference_number}, part {part_ordinal}).",
            operation=operation,
            host=host,
            reference_number=reference_number,
            part_ordinal=part_ordinal,
            status_code=status_code,
            outcome_ambiguous=outcome_ambiguous,
        )


class KSeFBatchUploadError[RecoveryStateT](KSeFExternalTransferError):
    """External batch upload failure with explicitly accessible recovery state."""

    code: str = "BATCH_UPLOAD_ERROR"

    def __init__(
        self,
        *,
        transfer_error: KSeFExternalTransferError,
        recovery_state: RecoveryStateT,
    ) -> None:
        self._recovery_state = recovery_state
        super().__init__(
            operation=transfer_error.operation,
            host=transfer_error.host,
            reference_number=transfer_error.reference_number,
            part_ordinal=transfer_error.part_ordinal,
            status_code=transfer_error.status_code,
            outcome_ambiguous=transfer_error.outcome_ambiguous,
        )

    def recovery_state(self) -> RecoveryStateT:
        """Return sensitive state for deliberate recovery of the failed batch.

        The state contains encryption material and presigned upload URLs. Protect it
        as credential material and do not include it in logs or generic error dumps.
        """
        return self._recovery_state


class KSeFEncryptionError(KSeFException):
    """Raised when encryption or decryption operations fail."""

    code: str = "ENCRYPTION_ERROR"

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(f"{self.code}: {message}")


class KSeFSessionError(KSeFException):
    """Raised on session-state violations (e.g. sending invoice on closed session)."""

    code: str = "SESSION_ERROR"

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(f"{self.code}: {message}")


class KSeFInvoiceRejectedError(KSeFSessionError):
    """Raised when KSeF finishes processing an invoice and rejects it.

    The full status response is kept, so callers can act on what KSeF said:
    ``details`` explains a semantic rejection (for example 450), and
    ``extensions`` carries structured data such as ``originalKsefNumber`` for a
    duplicate (440).
    """

    code: str = "INVOICE_REJECTED"

    def __init__(
        self,
        invoice_reference_number: str,
        status: SessionInvoiceStatusResponse,
    ) -> None:
        self.invoice_reference_number = invoice_reference_number
        self.status = status
        self.status_code = status.status.code
        self.description = status.status.description
        self.details = status.status.details or []
        self.extensions = status.status.extensions or {}

        message = (
            "Invoice processing failed: "
            f"{invoice_reference_number} ({self.status_code}: {self.description})"
        )
        if self.details:
            message += f" - {'; '.join(self.details)}"
        super().__init__(message)
        self.context.update(
            invoice_reference_number=invoice_reference_number,
            status_code=self.status_code,
            details=self.details,
            extensions=self.extensions,
        )


class NoCertificateAvailableError(KSeFException):
    """Raised when no certificate is available for signing."""

    code: str = "NO_CERTIFICATE_AVAILABLE"

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(f"{self.code}: {message}")


class KSeFExportTimeoutError(KSeFException):
    """Raised when polling for an export package exceeds the timeout."""

    code: str = "EXPORT_TIMEOUT"

    def __init__(
        self,
        reference_number: str,
        timeout: float,
    ) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Export package {reference_number} not ready after {timeout}s",
            reference_number=reference_number,
            timeout=timeout,
        )


class KSeFAuthPollingTimeoutError(KSeFException):
    """Raised when polling for authentication completion exceeds the timeout."""

    code: str = "AUTH_POLLING_TIMEOUT"

    def __init__(
        self,
        reference_number: str,
        timeout: float,
    ) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Authentication {reference_number} not ready after {timeout}s",
            reference_number=reference_number,
            timeout=timeout,
        )


class KSeFAuthTokenRedemptionError(KSeFException):
    """Raised when a one-shot authentication token redemption loses its response."""

    code: str = "AUTH_TOKEN_REDEMPTION_ERROR"

    def __init__(self) -> None:
        self.outcome_ambiguous = True
        super().__init__(
            "Authentication token redemption may have succeeded, but its response "
            "was lost. Do not retry the one-shot redemption automatically.",
            outcome_ambiguous=True,
        )


class KSeFTokenStatusTimeoutError(KSeFException):
    """Raised when polling for a token status change exceeds the timeout."""

    code: str = "TOKEN_STATUS_TIMEOUT"

    def __init__(
        self,
        reference_number: str,
        timeout: float,
    ) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Token {reference_number} not active after {timeout}s",
            reference_number=reference_number,
            timeout=timeout,
        )


class KSeFInvoiceQueryTimeoutError(KSeFException):
    """Raised when polling for invoices to appear exceeds the timeout."""

    code: str = "INVOICE_QUERY_TIMEOUT"

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        super().__init__(
            f"No invoices found after polling for {timeout}s",
            timeout=timeout,
        )


class KSeFMetadataPaginationError(KSeFException):
    """Raised when metadata pagination cannot continue safely."""

    code: str = "METADATA_PAGINATION_ERROR"


class KSeFInvoiceDownloadTimeoutError(KSeFException):
    """Raised when polling for an invoice download exceeds the timeout."""

    code: str = "INVOICE_DOWNLOAD_TIMEOUT"

    def __init__(self, ksef_number: str, timeout: float) -> None:
        self.ksef_number = ksef_number
        self.timeout = timeout
        super().__init__(
            f"Invoice {ksef_number} not available for download after {timeout}s",
            ksef_number=ksef_number,
            timeout=timeout,
        )


class KSeFInvoiceProcessingTimeoutError(KSeFException):
    """Raised when polling for a session invoice to finish processing exceeds the timeout."""

    code: str = "INVOICE_PROCESSING_TIMEOUT"

    def __init__(self, invoice_reference_number: str, timeout: float) -> None:
        self.invoice_reference_number = invoice_reference_number
        self.timeout = timeout
        super().__init__(
            f"Invoice {invoice_reference_number} not ready after {timeout}s",
            invoice_reference_number=invoice_reference_number,
            timeout=timeout,
        )


class KSeFBatchSessionTimeoutError(KSeFException):
    """Raised when polling for a batch session to finish processing exceeds the timeout."""

    code: str = "BATCH_SESSION_TIMEOUT"

    def __init__(self, reference_number: str, timeout: float) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Batch session {reference_number} not ready after {timeout}s",
            reference_number=reference_number,
            timeout=timeout,
        )
