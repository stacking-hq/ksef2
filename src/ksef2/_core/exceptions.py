"""Public exception hierarchy raised by the KSeF SDK."""

from typing import Any, Literal, override
from pydantic import BaseModel
from enum import IntEnum

from ksef2._domain.models.session import SessionInvoiceStatusResponse


class ExceptionCode(IntEnum):
    """KSeF error codes the SDK knows, from the KSeF API documentation.

    ``ksef_code`` on an API error is the raw number and the source of truth;
    ``exception_code`` is the same number as this enum, or ``UNKNOWN_ERROR`` for
    a code it does not list.

    Attributes:
        UNKNOWN_ERROR: Code used when KSeF returns no code or one this enum does not list.
        INVALID_DOCUMENT: The signed authentication document is invalid.
        MISSING_SIGNATURE: The authentication document has no signature.
        TOO_MANY_SIGNATURES: The authentication document has more signatures than allowed.
        INVALID_SIGNATURE: The signature of the authentication document is invalid.
        UNREADABLE_CONTENT: KSeF could not read the request content.
        INVALID_AUTH_CHALLENGE: The authentication challenge is invalid.
        INVALID_CERTIFICATE: The certificate is invalid.
        INVALID_CONTEXT_IDENTIFIER: The subject identifier does not fit the context type.
        SESSION_INVOICE_LIMIT_EXCEEDED: The session already holds the maximum number of invoices.
        INVALID_PACKAGE_PART_SIZE: A batch package part has an invalid size.
        PACKAGE_PART_LIMIT_EXCEEDED: The batch package has more parts than allowed.
        INVOICE_NOT_FOUND: No invoice exists with the given identifier.
        NOT_PROCESSED_YET: The invoice is processed but not available for download yet.
        TECHNICAL_CORRECTION_UNAVAILABLE: A technical correction is not available.
        TECHNICAL_CORRECTION_NOT_ALLOWED: The invoice status does not allow a technical correction.
        SESSION_NOT_FOUND: No session exists with the given reference number.
        QUERY_RESULT_NOT_FOUND: No export or query result exists with the given identifier.
        UPO_NOT_FOUND: No UPO matches the criteria: not issued yet, or never, for a rejected invoice.
        SESSION_STATUS_FORBIDS_OPERATION: The session status does not allow the operation.
        INVALID_EXPORT_REQUEST: The invoice export request is invalid.
        EXPORT_LIMIT_REACHED: The limit of exports running at once is reached.
        FILTER_RANGE_OUT_OF_BOUNDS: The filter range reaches outside the data KSeF keeps.
        SESSION_TEMPORARILY_UNAVAILABLE: The session is temporarily unavailable.
        EMPTY_PACKAGE: The batch package is empty.
        UPLOAD_WINDOW_EXCEEDED: The time for upload or close requests ran out.
        INVALID_CHARACTER_ENCODING: The request uses an invalid character encoding.
        NO_AUTHORIZATION: The caller is not authorized.
        NO_AUTHENTICATION: The caller is not authenticated.
        DECEASED_PERSON_AUTHENTICATION: The authentication method belongs to a deceased person.
        SCHEMA_VALIDATION_FAILED: The document does not match its XSD schema.
        INVALID_FILE_SIZE: The file size is invalid.
        INVALID_FILE_HASH: The file hash is invalid.
        VALIDATION_ERROR: KSeF rejected the request as invalid.
        SIGNATURE_AUTH_TYPE_CONFLICT: The signature conflicts with the authentication type.
        INVALID_CONTINUATION_TOKEN: The continuation token is malformed or invalid.
        UNKNOWN_KEY_ID: The encryption key identifier is unknown or points to a retired key.
        CSR_DATA_UNAVAILABLE: CSR data cannot be fetched for the authentication method used.
        ENROLLMENT_NOT_ALLOWED: A certificate request cannot be submitted with the authentication method used.
        CSR_DATA_MISMATCH: The CSR data does not match the authentication used.
        INVALID_CSR: The CSR format or its signature is invalid.
        ENROLLMENT_NOT_FOUND: No certificate request exists with the given reference number.
        ENROLLMENT_LIMIT_REACHED: The limit of certificate requests is reached.
        CERTIFICATE_LIMIT_REACHED: The limit of held certificates is reached.
        CERTIFICATE_NOT_FOUND: No certificate exists with the given serial number.
        CERTIFICATE_NOT_REVOCABLE: The certificate is already revoked, blocked or invalid.
        INVALID_KEY: The key type or length is invalid.
        INVALID_CSR_SIGNATURE_ALGORITHM: The CSR signature algorithm is invalid.
        TOKEN_PERMISSIONS_NOT_HELD: A token cannot get permissions the caller does not hold.
        TOKEN_CONTEXT_NOT_ALLOWED: A token cannot be generated for the current context type.
        OBJECT_ALREADY_EXISTS: The object being created already exists.
        COLLECTIVE_INVOICE_NOT_FOUND: No invoice exists with the given identifier.
        COLLECTIVE_IDENTIFIER_LIMIT_REACHED: The invoice already has the maximum number of collective identifiers.
        DIFFERENT_SELLERS: The invoices have different sellers.
        DUPLICATE_KSEF_NUMBER: A KSeF number is repeated in the request.
    """

    UNKNOWN_ERROR = 10000
    INVALID_DOCUMENT = 9101
    MISSING_SIGNATURE = 9102
    TOO_MANY_SIGNATURES = 9103
    INVALID_SIGNATURE = 9105
    UNREADABLE_CONTENT = 21001
    INVALID_AUTH_CHALLENGE = 21111
    INVALID_CERTIFICATE = 21115
    INVALID_CONTEXT_IDENTIFIER = 21117
    SESSION_INVOICE_LIMIT_EXCEEDED = 21155
    INVALID_PACKAGE_PART_SIZE = 21157
    PACKAGE_PART_LIMIT_EXCEEDED = 21161
    INVOICE_NOT_FOUND = 21164
    NOT_PROCESSED_YET = 21165
    TECHNICAL_CORRECTION_UNAVAILABLE = 21166
    TECHNICAL_CORRECTION_NOT_ALLOWED = 21167
    SESSION_NOT_FOUND = 21173
    QUERY_RESULT_NOT_FOUND = 21175
    UPO_NOT_FOUND = 21178
    SESSION_STATUS_FORBIDS_OPERATION = 21180
    INVALID_EXPORT_REQUEST = 21181
    EXPORT_LIMIT_REACHED = 21182
    FILTER_RANGE_OUT_OF_BOUNDS = 21183
    SESSION_TEMPORARILY_UNAVAILABLE = 21184
    EMPTY_PACKAGE = 21205
    UPLOAD_WINDOW_EXCEEDED = 21208
    INVALID_CHARACTER_ENCODING = 21217
    NO_AUTHORIZATION = 21301
    NO_AUTHENTICATION = 21304
    DECEASED_PERSON_AUTHENTICATION = 21308
    SCHEMA_VALIDATION_FAILED = 21401
    INVALID_FILE_SIZE = 21402
    INVALID_FILE_HASH = 21403
    VALIDATION_ERROR = 21405
    SIGNATURE_AUTH_TYPE_CONFLICT = 21406
    INVALID_CONTINUATION_TOKEN = 21418
    UNKNOWN_KEY_ID = 21470
    CSR_DATA_UNAVAILABLE = 25001
    ENROLLMENT_NOT_ALLOWED = 25002
    CSR_DATA_MISMATCH = 25003
    INVALID_CSR = 25004
    ENROLLMENT_NOT_FOUND = 25005
    ENROLLMENT_LIMIT_REACHED = 25006
    CERTIFICATE_LIMIT_REACHED = 25007
    CERTIFICATE_NOT_FOUND = 25008
    CERTIFICATE_NOT_REVOCABLE = 25009
    INVALID_KEY = 25010
    INVALID_CSR_SIGNATURE_ALGORITHM = 25011
    TOKEN_PERMISSIONS_NOT_HELD = 26001
    TOKEN_CONTEXT_NOT_ALLOWED = 26002
    OBJECT_ALREADY_EXISTS = 30001
    COLLECTIVE_INVOICE_NOT_FOUND = 71001
    COLLECTIVE_IDENTIFIER_LIMIT_REACHED = 71002
    DIFFERENT_SELLERS = 71004
    DUPLICATE_KSEF_NUMBER = 71005

    @staticmethod
    def from_code(code: int | None) -> "ExceptionCode":
        """Return the member for a KSeF error code, or ``UNKNOWN_ERROR`` when the enum does not list it.

        Args:
            code: Numeric code from a KSeF error response, or ``None``.

        Returns:
            The matching ``ExceptionCode``, or ``UNKNOWN_ERROR`` when ``code`` is ``None`` or not listed.
        """
        try:
            return ExceptionCode(code)
        except ValueError:
            return ExceptionCode.UNKNOWN_ERROR


class KSeFException(Exception):
    """Base exception for all KSeF SDK errors.

    Branch on the exception class, or on ``ksef_code`` for API errors, and never
    on the message text: messages are meant for people and can change.

    Args:
        message: Human-readable error message.
        hint: Next step for this occurrence; overrides the class default.
        **context: Additional structured details, stored in ``context``.

    Attributes:
        code: Stable machine-readable error code of the exception class.
        hint: What to do next, or ``None`` when the SDK does not know the cause. Shown as a ``Hint:`` line in ``str(exc)``.
        context: Structured details about the failure; always contains ``code``, and ``hint`` when there is one.
    """

    code: str = "SDK_ERROR"
    hint: str | None = None

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        **context: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ):
        super().__init__(message)
        if hint is not None:
            self.hint = hint
        self.context: dict[str, Any] = context
        self.context["code"] = self.code
        if self.hint is not None:
            self.context["hint"] = self.hint

    @override
    def __str__(self) -> str:
        message = super().__str__()
        if self.hint is None:
            return message
        return f"{message}\nHint: {self.hint}"


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
        hint: Next step for this occurrence; overrides the class default.
        **context: Additional structured details, stored in ``context``.
    """

    code: str = "VALIDATION_ERROR"


class KSeFArgumentError(KSeFValidationError, TypeError):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Raised when a call combines arguments the SDK does not allow.

    It is raised for "exactly one of" violations, such as passing both or neither
    of ``form_code`` and ``state`` to ``online_session()``. It subclasses
    ``KSeFValidationError`` so existing handlers keep catching it, and
    ``TypeError`` because the call itself is wrong.

    Args:
        message: Human-readable error message.
        hint: Next step for this occurrence; overrides the class default.
        **context: Additional structured details, stored in ``context``.
    """

    code: str = "ARGUMENT_ERROR"
    hint: str | None = (
        "Pass exactly one of the mutually exclusive arguments named in the message."
    )


class KSeFInvoiceRenderingError(KSeFException):
    """Raised when invoice rendering fails."""

    code: str = "INVOICE_RENDERING_ERROR"


class KSeFApiError(KSeFException):
    """Raised on 4xx/5xx responses from the KSeF API.

    ``str(exc)`` reads ``KSeF rejected <METHOD path> (HTTP <status>, KSeF code
    <code>): <description>``, followed by ``Details:``, ``Trace ID:`` and
    ``Hint:`` lines when KSeF or the SDK supplied them. The full response body is
    on ``response``, not in the message. Branch on the exception class or on
    ``ksef_code``, never on the message text.

    Args:
        status_code: HTTP status code of the response.
        exception_code: KSeF exception code parsed from the response, ``ExceptionCode.UNKNOWN_ERROR`` when it is absent or not listed.
        message: Human-readable error message.
        response: Parsed error response body, if available.
        ksef_code: Raw KSeF error code from the response, if there was one.
        trace_id: KSeF trace ID of the failed request, if KSeF returned one.
        details: Detail messages KSeF attached to the error.
        hint: Next step for this occurrence; overrides the class default.

    Attributes:
        status_code: HTTP status code of the response.
        exception_code: KSeF exception code as the ``ExceptionCode`` enum; ``UNKNOWN_ERROR`` for codes the enum does not list.
        ksef_code: Raw KSeF error code, or ``None`` when the response carried none. It is the source of truth; prefer it over ``exception_code``.
        trace_id: KSeF trace ID to quote when contacting KSeF support, or ``None``.
        details: Detail messages KSeF attached to the error; empty when there are none.
        response: Parsed error response body, or ``None``.
    """

    code: str = "API_ERROR"

    def __init__(
        self,
        status_code: int,
        exception_code: ExceptionCode,
        message: str,
        response: BaseModel | None = None,
        *,
        ksef_code: int | None = None,
        trace_id: str | None = None,
        details: list[str] | None = None,
        hint: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response = response
        self.exception_code = exception_code
        self.ksef_code = ksef_code
        self.trace_id = trace_id
        self.details: list[str] = list(details or [])
        super().__init__(
            message,
            hint=hint,
            status_code=status_code,
            ksef_code=ksef_code,
            trace_id=trace_id,
            details=self.details,
        )


class KSeFNotReadyError(KSeFApiError):
    """Raised when KSeF has not made a processed resource available yet.

    KSeF reports codes 21165 (the invoice is processed but not yet available for
    download) and 21178 (no UPO found). The resource usually appears shortly, so
    waiting and asking again is the normal recovery. For 21178, call ``wait()``
    on the invoice submission or the session first: KSeF also answers 21178 for
    an invoice it rejected, which never gets a UPO, and ``wait()`` then raises
    ``KSeFInvoiceRejectedError``. It subclasses ``KSeFApiError``, so existing
    handlers keep working.
    """

    code: str = "NOT_READY"
    hint: str | None = (
        "KSeF has not finished preparing this resource. Wait and request it again."
    )


class KSeFAuthError(KSeFApiError):
    """Raised on 401/403 responses.

    Args:
        status_code: HTTP status code of the response, ``401`` or ``403``.
        message: Human-readable error message.
        response: Parsed error response body, if available.
        ksef_code: Raw KSeF error code from the response, if there was one.
        trace_id: KSeF trace ID of the failed request, if KSeF returned one.
        details: Detail messages KSeF attached to the error.
        hint: Next step for this occurrence; overrides the class default.
    """

    code: str = "AUTH_ERROR"

    def __init__(
        self,
        status_code: int,
        message: str,
        response: BaseModel | None = None,
        *,
        ksef_code: int | None = None,
        trace_id: str | None = None,
        details: list[str] | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(
            status_code,
            ExceptionCode.from_code(ksef_code),
            message,
            response,
            ksef_code=ksef_code,
            trace_id=trace_id,
            details=details,
            hint=hint,
        )


class KSeFAuthenticationExpiredError(KSeFAuthError):
    """Raised when the refresh token is expired or rejected and the session cannot be renewed.

    The client could not refresh its access token, so the only way forward is
    to authenticate again. Because it subclasses ``KSeFAuthError``, existing
    handlers for authentication failures keep working.

    Args:
        message: Human-readable error message; defaults to a statement that the access token can no longer be renewed.
        status_code: HTTP status code of the rejected response, ``401`` or ``403``.
        response: Parsed error response body, if available.
        ksef_code: Raw KSeF error code from the rejected response, if there was one.
        trace_id: KSeF trace ID of the rejected request, if KSeF returned one.
        details: Detail messages KSeF attached to the rejection.
        hint: Next step for this occurrence; overrides the class default.
    """

    code: str = "AUTHENTICATION_EXPIRED"
    hint: str | None = (
        "Authenticate again with `client.authentication.with_token()` or "
        "`client.authentication.with_xades()`, or restore tokens that are still "
        "valid with `client.authentication.resume()`."
    )

    def __init__(
        self,
        message: str = (
            "The refresh token is expired or was rejected, so the access token "
            "can no longer be renewed."
        ),
        status_code: int = 401,
        response: BaseModel | None = None,
        *,
        ksef_code: int | None = None,
        trace_id: str | None = None,
        details: list[str] | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(
            status_code,
            message,
            response,
            ksef_code=ksef_code,
            trace_id=trace_id,
            details=details,
            hint=hint,
        )


class KSeFRateLimitError(KSeFApiError):
    """Raised on 429 responses. Check ``retry_after`` for seconds to wait.

    Args:
        retry_after: Seconds to wait before retrying, from the ``Retry-After`` header in either its seconds or HTTP-date form; ``None`` if absent.
        message: Human-readable error message.
        response: Parsed error response body, if available.
        ksef_code: Raw KSeF error code from the response, if there was one.
        trace_id: KSeF trace ID of the failed request, if KSeF returned one.
        details: Detail messages KSeF attached to the error.
        hint: Next step for this occurrence; defaults to waiting ``retry_after`` seconds.

    Attributes:
        retry_after: Seconds to wait before retrying, or ``None``.
    """

    code: str = "RATE_LIMIT_ERROR"

    def __init__(
        self,
        retry_after: int | None,
        message: str,
        response: BaseModel | None = None,
        *,
        ksef_code: int | None = None,
        trace_id: str | None = None,
        details: list[str] | None = None,
        hint: str | None = None,
    ) -> None:
        self.retry_after = retry_after
        if hint is None:
            hint = (
                f"Wait {retry_after} seconds before retrying."
                if retry_after is not None
                else "Wait a little before retrying, and send fewer requests."
            )
        super().__init__(
            429,
            ExceptionCode.from_code(ksef_code),
            message,
            response,
            ksef_code=ksef_code,
            trace_id=trace_id,
            details=details,
            hint=hint,
        )
        self.context["retry_after"] = retry_after


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
        hint: Next step for this occurrence.
    """

    code: str = "SESSION_ERROR"

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
    ) -> None:
        super().__init__(f"{self.code}: {message}", hint=hint)


_DUPLICATE_INVOICE_HINT = (
    "KSeF already holds this invoice (status 440). `extensions` carries "
    "`originalKsefNumber`: fetch it with `download()` and compare it with what you sent."
)


class KSeFInvoiceRejectedError(KSeFSessionError):
    """Raised when KSeF finishes processing an invoice and rejects it.

    Raised by ``InvoiceSubmission.wait()``, and by the deprecated
    ``wait_for_invoice_ready()`` and ``send_invoice_and_wait()``.
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
    hint: str | None = (
        "Read `description` and `details` for the reason, fix the invoice and send it "
        "again with `send_invoice()`."
    )

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
        super().__init__(
            message,
            hint=_DUPLICATE_INVOICE_HINT if self.invoice_status_code == 440 else None,
        )
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
    hint: str | None = (
        "The export may still finish. Call `wait()` on the export again with a larger "
        "`timeout`. After a restart, get the job back with `export(state=...)` using the "
        "state saved from `resume_state()`."
    )

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


class KSeFExportFailedError(KSeFException):
    """Raised when KSeF finishes an invoice export without producing a package.

    Raised by ``ExportJob.wait()`` when the export failed, was cancelled by the
    system or expired before it was downloaded. ``export_status_code`` is a KSeF
    export status, such as 415 or 550, and is not an HTTP status.

    Args:
        reference_number: Reference number of the export.
        status_code: KSeF export status code.
        description: Description of the status.
        details: Explanations of the failure, if KSeF gave any.

    Attributes:
        reference_number: Reference number of the export.
        export_status_code: KSeF export status code.
        description: Description of the status.
        details: Explanations of the failure; empty when none were given.
    """

    code: str = "EXPORT_FAILED"
    hint: str | None = (
        "Read `description` and `details` for the reason, then start a new export with "
        "`export()`."
    )

    def __init__(
        self,
        reference_number: str,
        status_code: int,
        description: str,
        details: list[str] | None = None,
    ) -> None:
        self.reference_number = reference_number
        self.export_status_code = status_code
        self.description = description
        self.details = details or []
        message = f"Export {reference_number} failed ({status_code}: {description})"
        if self.details:
            message += f" - {'; '.join(self.details)}"
        super().__init__(
            message,
            reference_number=reference_number,
            export_status_code=status_code,
            description=description,
            details=self.details,
        )


class KSeFPermissionOperationFailedError(KSeFException):
    """Raised when KSeF finishes a permission grant or revoke without applying it.

    Raised by ``PermissionOperation.wait()``. ``operation_status_code`` is a KSeF
    operation status, such as 400 or 420, and is not an HTTP status.

    Args:
        reference_number: Reference number of the permission operation.
        status_code: KSeF operation status code.
        description: Description of the status.

    Attributes:
        reference_number: Reference number of the permission operation.
        operation_status_code: KSeF operation status code.
        description: Description of the status.
    """

    code: str = "PERMISSION_OPERATION_FAILED"
    hint: str | None = (
        "Read `description` for the reason, fix the request and grant or revoke "
        "again. `get_operation_status()` shows the operation's final state."
    )

    def __init__(
        self,
        reference_number: str,
        status_code: int,
        description: str,
    ) -> None:
        self.reference_number = reference_number
        self.operation_status_code = status_code
        self.description = description
        super().__init__(
            f"Permission operation {reference_number} failed "
            f"({status_code}: {description})",
            reference_number=reference_number,
            operation_status_code=status_code,
            description=description,
        )


class KSeFPermissionOperationTimeoutError(KSeFException):
    """Raised when polling for a permission operation to finish exceeds the timeout.

    Args:
        reference_number: Reference number of the permission operation.
        timeout: Number of seconds waited.

    Attributes:
        reference_number: Reference number of the permission operation.
        timeout: Number of seconds waited.
    """

    code: str = "PERMISSION_OPERATION_TIMEOUT"
    hint: str | None = (
        "The operation may still be applied. Call `wait()` on the operation again "
        "with a larger `timeout`, or check it with `get_operation_status()`."
    )

    def __init__(
        self,
        reference_number: str,
        timeout: float,
    ) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Permission operation {reference_number} not finished after {timeout}s",
            reference_number=reference_number,
            timeout=timeout,
        )


class KSeFCertificateEnrollmentFailedError(KSeFException):
    """Raised when KSeF finishes a certificate enrollment without issuing a certificate.

    Raised by ``CertificateEnrollment.wait()`` when the request was rejected, hit
    an unknown error or was cancelled by the system. ``enrollment_status_code`` is
    a KSeF enrollment status, such as 400 or 550, and is not an HTTP status.

    Args:
        reference_number: Reference number of the enrollment.
        status_code: KSeF enrollment status code.
        description: Description of the status.
        details: Explanations of the failure, if KSeF gave any.

    Attributes:
        reference_number: Reference number of the enrollment.
        enrollment_status_code: KSeF enrollment status code.
        description: Description of the status.
        details: Explanations of the failure; empty when none were given.
    """

    code: str = "CERTIFICATE_ENROLLMENT_FAILED"
    hint: str | None = (
        "Read `description` and `details` for the reason, then submit a corrected "
        "request with `enroll()`. `get_limits()` shows how many enrollments and "
        "certificates are still allowed."
    )

    def __init__(
        self,
        reference_number: str,
        status_code: int,
        description: str,
        details: list[str] | None = None,
    ) -> None:
        self.reference_number = reference_number
        self.enrollment_status_code = status_code
        self.description = description
        self.details = details or []
        message = (
            f"Certificate enrollment {reference_number} failed "
            f"({status_code}: {description})"
        )
        if self.details:
            message += f" - {'; '.join(self.details)}"
        super().__init__(
            message,
            reference_number=reference_number,
            enrollment_status_code=status_code,
            description=description,
            details=self.details,
        )


class KSeFCertificateEnrollmentTimeoutError(KSeFException):
    """Raised when polling for a certificate to be issued exceeds the timeout.

    Args:
        reference_number: Reference number of the enrollment.
        timeout: Number of seconds waited.

    Attributes:
        reference_number: Reference number of the enrollment.
        timeout: Number of seconds waited.
    """

    code: str = "CERTIFICATE_ENROLLMENT_TIMEOUT"
    hint: str | None = (
        "KSeF may still issue the certificate. Call `wait()` on the enrollment "
        "again with a larger `timeout`, or check it with `get_enrollment_status()`."
    )

    def __init__(
        self,
        reference_number: str,
        timeout: float,
    ) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Certificate enrollment {reference_number} not issued after {timeout}s",
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
    hint: str | None = (
        "KSeF has not finished authenticating yet. Authenticate again with a larger "
        "`timeout` in `client.authentication.with_xades()` or "
        "`client.authentication.with_token()`."
    )

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
    hint: str | None = (
        "KSeF may still be activating the token. Call `wait()` on the token again with "
        "a larger `timeout`, or check it with `get_status()`."
    )

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
    hint: str | None = (
        "No invoice matched before the deadline. Call `wait()` again with a larger "
        "`timeout`, or check the filters passed to `search()`."
    )

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
    hint: str | None = (
        "KSeF has not made the invoice available yet. Call `download()` again "
        "with a larger `timeout`."
    )

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
    hint: str | None = (
        "KSeF may still accept the invoice. Keep waiting with "
        "`submission(reference_number).wait()` on the session, with a larger `timeout`. "
        "After a restart, rebuild the session from the state saved with `resume_state()` "
        "using `online_session(state=...)`."
    )

    def __init__(self, invoice_reference_number: str, timeout: float) -> None:
        self.invoice_reference_number = invoice_reference_number
        self.timeout = timeout
        super().__init__(
            f"Invoice {invoice_reference_number} not ready after {timeout}s",
            invoice_reference_number=invoice_reference_number,
            timeout=timeout,
        )


class KSeFOnlineSessionTimeoutError(KSeFException):
    """Raised when polling for an online session to finish processing exceeds the timeout.

    Args:
        reference_number: Reference number of the online session.
        timeout: Number of seconds waited.

    Attributes:
        reference_number: Reference number of the online session.
        timeout: Number of seconds waited.
    """

    code: str = "ONLINE_SESSION_TIMEOUT"
    hint: str | None = (
        "KSeF may still be processing the session. Call `wait()` on the session "
        "again with a larger `timeout`. After a restart, rebuild the session from the "
        "state saved with `resume_state()` using `online_session(state=...)`."
    )

    def __init__(self, reference_number: str, timeout: float) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Online session {reference_number} not ready after {timeout}s",
            reference_number=reference_number,
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
    hint: str | None = (
        "KSeF may still be processing the batch. Call `wait()` on the batch session "
        "again with a larger `timeout`. After a restart, rebuild the session from the "
        "state saved with `resume_state()` using `batch_session(state=...)`."
    )

    def __init__(self, reference_number: str, timeout: float) -> None:
        self.reference_number = reference_number
        self.timeout = timeout
        super().__init__(
            f"Batch session {reference_number} not ready after {timeout}s",
            reference_number=reference_number,
            timeout=timeout,
        )
