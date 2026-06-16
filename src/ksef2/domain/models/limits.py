"""Domain models for effective and overrideable KSeF limits."""

from ksef2.domain.models import KSeFBaseModel


class SessionLimits(KSeFBaseModel):
    """Invoice count and payload size limits for one session type."""

    max_invoice_size_mb: int
    max_invoice_with_attachment_size_mb: int
    max_invoices: int


class ContextLimits(KSeFBaseModel):
    """Limits applied separately to online and batch sessions."""

    online_session: SessionLimits
    batch_session: SessionLimits


class SubjectCertificateLimits(KSeFBaseModel):
    """Certificate issuance limit override for the current subject."""

    max_certificates: int | None = None


class SubjectEnrollmentLimits(KSeFBaseModel):
    """Certificate enrollment limit override for the current subject."""

    max_enrollments: int | None = None


class SubjectLimits(KSeFBaseModel):
    """Subject-level limits for certificate enrollment and issuance."""

    certificate: SubjectCertificateLimits | None = None
    enrollment: SubjectEnrollmentLimits | None = None


class RateLimitValues(KSeFBaseModel):
    """Per-second, per-minute, and per-hour caps for one API category."""

    per_second: int
    per_minute: int
    per_hour: int


class ApiRateLimits(KSeFBaseModel):
    """Rate limits grouped by API operation family."""

    online_session: RateLimitValues
    batch_session: RateLimitValues
    invoice_send: RateLimitValues
    invoice_status: RateLimitValues
    session_list: RateLimitValues
    session_invoice_list: RateLimitValues
    session_misc: RateLimitValues
    invoice_metadata: RateLimitValues
    invoice_export: RateLimitValues
    invoice_export_status: RateLimitValues
    invoice_download: RateLimitValues
    other: RateLimitValues
