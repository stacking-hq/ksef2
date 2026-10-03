"""Domain models for effective and overrideable KSeF limits."""

from ksef2._domain.models.base import KSeFBaseModel


class SessionLimits(KSeFBaseModel):
    """Invoice count and payload size limits for one session type."""

    max_invoice_size_mb: int
    """Maximum size of one invoice without attachment, in megabytes."""
    max_invoice_with_attachment_size_mb: int
    """Maximum size of one invoice with an attachment, in megabytes."""
    max_invoices: int
    """Maximum number of invoices in one session."""


class CollectiveIdentifierLimits(KSeFBaseModel):
    """Invoice count limit for one collective identifier."""

    max_invoices: int
    """Maximum number of invoices in one collective identifier."""


class ContextLimits(KSeFBaseModel):
    """Limits applied to sessions and collective identifiers."""

    online_session: SessionLimits
    """Limits for online sessions."""
    batch_session: SessionLimits
    """Limits for batch sessions."""
    collective_identifier: CollectiveIdentifierLimits
    """Limits for collective identifiers."""


class SubjectCertificateLimits(KSeFBaseModel):
    """Certificate issuance limit override for the current subject."""

    max_certificates: int | None = None
    """Maximum number of certificates; ``None`` when no override is set."""


class SubjectEnrollmentLimits(KSeFBaseModel):
    """Certificate enrollment limit override for the current subject."""

    max_enrollments: int | None = None
    """Maximum number of enrollment requests; ``None`` when no override is set."""


class SubjectLimits(KSeFBaseModel):
    """Subject-level limits for certificate enrollment and issuance."""

    certificate: SubjectCertificateLimits | None = None
    """Certificate issuance limit override; ``None`` when no override is set."""
    enrollment: SubjectEnrollmentLimits | None = None
    """Certificate enrollment limit override; ``None`` when no override is set."""


class RateLimitValues(KSeFBaseModel):
    """Per-second, per-minute, and per-hour caps for one API category."""

    per_second: int
    """Maximum requests per second."""
    per_minute: int
    """Maximum requests per minute."""
    per_hour: int
    """Maximum requests per hour."""


class ApiRateLimits(KSeFBaseModel):
    """Rate limits grouped by API operation family."""

    online_session: RateLimitValues
    """Limits for opening online sessions."""
    online_session_close: RateLimitValues
    """Limits for closing online sessions."""
    batch_session: RateLimitValues
    """Limits for opening batch sessions."""
    batch_session_close: RateLimitValues
    """Limits for closing batch sessions."""
    invoice_send: RateLimitValues
    """Limits for sending invoices."""
    invoice_status: RateLimitValues
    """Limits for reading invoice status."""
    session_list: RateLimitValues
    """Limits for listing sessions."""
    session_invoice_list: RateLimitValues
    """Limits for listing invoices of a session."""
    session_misc: RateLimitValues
    """Limits for other session operations."""
    invoice_metadata: RateLimitValues
    """Limits for querying invoice metadata."""
    invoice_export: RateLimitValues
    """Limits for starting invoice exports."""
    invoice_export_status: RateLimitValues
    """Limits for reading export status."""
    invoice_download: RateLimitValues
    """Limits for downloading invoices."""
    collective_identifier: RateLimitValues
    """Limits for collective identifier operations."""
    other: RateLimitValues
    """Limits for operations not covered by another category."""
    anonymous: RateLimitValues
    """Limits for unauthenticated requests."""
    global_: RateLimitValues
    """Overall limits across all operations."""
