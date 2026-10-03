"""Public exception hierarchy raised by the KSeF SDK."""

from typing import Any, Literal
from pydantic import BaseModel
from enum import IntEnum

from ksef2._domain.models.session import SessionInvoiceStatusResponse


class ExceptionCode(IntEnum):
    """Enumeration of all possible exception codes.

    Attributes:
        UNKNOWN_ERROR: Code used when KSeF returns no code or an unrecognized one.
        OBJECT_ALREADY_EXISTS: The object being created already exists.
        VALIDATION_ERROR: KSeF rejected the request as invalid.
        UPO_NOT_FOUND: The requested UPO does not exist.
        NOT_PROCESSED_YET: The resource is not processed yet; retry later.
    """

    UNKNOWN_ERROR = 10000
    OBJECT_ALREADY_EXISTS = 30001
    VALIDATION_ERROR = 21405
    UPO_NOT_FOUND = 21178
    NOT_PROCESSED_YET = 21165

    @staticmethod
    def from_code(code: int | None) -> "ExceptionCode":
        """Return a known exception code or ``UNKNOWN_ERROR`` for unknown values.

        Args:
            code: Numeric code from a KSeF error response, or ``None``.

        Returns:
            The matching ``ExceptionCode``, or ``UNKNOWN_ERROR`` when ``code`` is ``None`` or not recognized.
        """
        try:
            return ExceptionCode(code)
        except ValueError:
            return ExceptionCode.UNKNOWN_ERROR


class KSeFException(Exception):
    """Base exception for all KSeF SDK errors.

    Args:
        message: Human-readable error message.
        **context: Additional structured details, stored in ``context``.

    Attributes:
        code: Stable machine-readable error code of the exception class.
        context: Structured details about the failure; always contains ``code``.
    """

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
    """Raised when validation fails.

    Args:
        message: Human-readable error message.
        **context: Additional structured details, stored in ``context``.
    """

    code: str = "VALIDATION_ERROR"

    def __init__(self, message: str, **context: Any):
        super().__init__(message, **context)
        self.context["code"] = self.code


class KSeFInvoiceRenderingError(KSeFException):
    """Raised when invoice rendering fails."""

    code: str = "INVOICE_RENDERING_ERROR"


class KSeFApiError(KSeFException):
    """Raised on 4xx/5xx responses from the KSeF API.

    Args:
        status_code: HTTP status code of the response.
        exception_code: KSeF exception code parsed from the response.
        message: Human-readable error message.
        response: Parsed error response body, if available.

    Attributes:
        status_code: HTTP status code of the response.
        exception_code: KSeF exception code parsed from the response.
        response: Parsed error response body, or ``None``.
    """

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
    """Raised on 401/403 responses.

    Args:
        status_code: HTTP status code of the response, ``401`` or ``403``.
        message: Human-readable error message.
        response: Parsed error response body, if available.
    """

    code: str = "AUTH_ERROR"

    def __init__(
        self,
        status_code: int,
        message: str,
        response: BaseModel | None = None,
    ) -> None:
        super().__init__(status_code, ExceptionCode.UNKNOWN_ERROR, message, response)


class KSeFRateLimitError(KSeFApiError):
    """Raised on 429 responses. Check ``retry_after`` for seconds to wait.

    Args:
        retry_after: Seconds to wait before retrying, from the ``Retry-After`` header; ``None`` if absent.
        message: Human-readable error message.
        response: Parsed error response body, if available.

    Attributes:
        retry_after: Seconds to wait before retrying, or ``None``.
    """

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
    """Raised when a presigned external-storage transfer fails.

    Args:
        operation: Direction of the failed transfer, ``upload`` or ``download``.
        host: Host of the presigned URL.
        reference_number: KSeF reference number the transfer belongs to.
        part_ordinal: One-based number of the part being transferred.
        status_code: HTTP status code returned by external storage; ``None`` if no response was received.
        outcome_ambiguous: Whether the transfer may have succeeded despite the failure.

    Attributes:
        operation: Direction of the failed transfer.
        host: Host of the presigned URL.
        reference_number: KSeF reference number the transfer belongs to.
        part_ordinal: One-based number of the part being transferred.
        status_code: HTTP status code returned by external storage, or ``None``.
        outcome_ambiguous: Whether the transfer may have succeeded despite the failure.
    """

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
    """External batch upload failure with explicitly accessible recovery state.

    Args:
        transfer_error: The underlying external transfer failure.
        recovery_state: Sensitive batch state kept for deliberate recovery; read it with ``recovery_state()``.
    """

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

        Returns:
            The batch state captured when the upload failed.
        """
        return self._recovery_state


class KSeFEncryptionError(KSeFException):
    """Raised when encryption or decryption operations fail.

    Args:
        message: Description of the encryption failure.
    """

    code: str = "ENCRYPTION_ERROR"

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(f"{self.code}: {message}")


class KSeFSessionError(KSeFException):
    """Raised on session-state violations (e.g. sending invoice on closed session).

    ``KSeFInvoiceRejectedError`` derives from this class so existing handlers
    keep working, which means handling ``KSeFSessionError`` also catches
    invoices that KSeF rejected. Handle the subclass first when only a
    session-state violation needs recovery.

    Args:
        message: Description of the session-state violation.
    """

    code: str = "SESSION_ERROR"

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(f"{self.code}: {message}")


class KSeFInvoiceRejectedError(KSeFSessionError):
    """Raised when KSeF finishes processing an invoice and rejects it.

    Raised by ``wait_for_invoice_ready()`` and ``send_invoice_and_wait()``.
    ``invoice_status_code`` is a KSeF invoice status, such as 440 or 450, and is
    not an HTTP status.

    The full status response is kept, so callers can act on what KSeF said:
    ``details`` explains a semantic rejection (for example 450), and
    ``extensions`` carries structured data such as ``originalKsefNumber`` for a
    duplicate (440).

    Args:
        invoice_reference_number: Reference number of the rejected invoice within the session.
        status: Full processing status returned by KSeF.

    Attributes:
        invoice_reference_number: Reference number of the rejected invoice within the session.
        status: Full processing status returned by KSeF.
        invoice_status_code: KSeF invoice status code, for example 440 or 450.
        description: Description of the status.
        details: Explanations of the rejection; empty when none were given.
        extensions: Structured status data; empty when none were given.
    """

    code: str = "INVOICE_REJECTED"

    def __init__(
        self,
        invoice_reference_number: str,
        status: SessionInvoiceStatusResponse,
    ) -> None:
        self.invoice_reference_number = invoice_reference_number
        self.status = status
        self.invoice_status_code = status.status.code
        self.description = status.status.description
        self.details = status.status.details or []
        self.extensions = status.status.extensions or {}

        message = (
            "Invoice processing failed: "
            f"{invoice_reference_number} "
            f"({self.invoice_status_code}: {self.description})"
        )
        if self.details:
            message += f" - {'; '.join(self.details)}"
        super().__init__(message)
        self.context.update(
            invoice_reference_number=invoice_reference_number,
            invoice_status_code=self.invoice_status_code,
            description=self.description,
            details=self.details,
            extensions=self.extensions,
        )


class NoCertificateAvailableError(KSeFException):
    """Raised when no certificate is available for signing.

    Args:
        message: Description of what is missing.
    """

    code: str = "NO_CERTIFICATE_AVAILABLE"

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(f"{self.code}: {message}")


class KSeFExportTimeoutError(KSeFException):
    """Raised when polling for an export package exceeds the timeout.

    Args:
        reference_number: Reference number of the export.
        timeout: Number of seconds waited.

    Attributes:
        reference_number: Reference number of the export.
        timeout: Number of seconds waited.
    """

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
    """Raised when polling for authentication completion exceeds the timeout.

    Args:
        reference_number: Reference number of the authentication operation.
        timeout: Number of seconds waited.

    Attributes:
        reference_number: Reference number of the authentication operation.
        timeout: Number of seconds waited.
    """

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
    """Raised when a one-shot authentication token redemption loses its response.

    Attributes:
        outcome_ambiguous: Always ``True``; the redemption may have succeeded.
    """

    code: str = "AUTH_TOKEN_REDEMPTION_ERROR"

    def __init__(self) -> None:
        self.outcome_ambiguous = True
        super().__init__(
            "Authentication token redemption may have succeeded, but its response "
            "was lost. Do not retry the one-shot redemption automatically.",
            outcome_ambiguous=True,
        )


class KSeFTokenStatusTimeoutError(KSeFException):
    """Raised when polling for a token status change exceeds the timeout.

    Args:
        reference_number: Reference number of the token.
        timeout: Number of seconds waited.

    Attributes:
        reference_number: Reference number of the token.
        timeout: Number of seconds waited.
    """

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
    """Raised when polling for invoices to appear exceeds the timeout.

    Args:
        timeout: Number of seconds waited.

    Attributes:
        timeout: Number of seconds waited.
    """

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
    """Raised when polling for an invoice download exceeds the timeout.

    Args:
        ksef_number: KSeF number of the invoice.
        timeout: Number of seconds waited.

    Attributes:
        ksef_number: KSeF number of the invoice.
        timeout: Number of seconds waited.
    """

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
    """Raised when polling for a session invoice to finish processing exceeds the timeout.

    Args:
        invoice_reference_number: Reference number of the invoice within the session.
        timeout: Number of seconds waited.

    Attributes:
        invoice_reference_number: Reference number of the invoice within the session.
        timeout: Number of seconds waited.
    """

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
    """Raised when polling for a batch session to finish processing exceeds the timeout.

    Args:
        reference_number: Reference number of the batch session.
        timeout: Number of seconds waited.

    Attributes:
        reference_number: Reference number of the batch session.
        timeout: Number of seconds waited.
    """

    code: str = "BATCH_SESSION_TIMEOUT"

    def __init__(self, reference_number: str, timeout: float) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Batch session {reference_number} not ready after {timeout}s",
            reference_number=reference_number,
            timeout=timeout,
        )
