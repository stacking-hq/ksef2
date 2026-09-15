from ksef2.domain.models import limits as domain_limits
from ksef2.infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture


@register_fixture(name="domain_limit_session")
class DomainSessionLimitsFactory(ModelFactory[domain_limits.SessionLimits]):
    max_invoice_size_mb: int = 5
    max_invoice_with_attachment_size_mb: int = 10
    max_invoices: int = 100


class DomainCollectiveIdentifierLimitsFactory(
    ModelFactory[domain_limits.CollectiveIdentifierLimits]
):
    max_invoices: int = 500


@register_fixture(name="domain_limit_context")
class DomainContextLimitsFactory(ModelFactory[domain_limits.ContextLimits]):
    online_session: domain_limits.SessionLimits = DomainSessionLimitsFactory.build()
    batch_session: domain_limits.SessionLimits = DomainSessionLimitsFactory.build()
    collective_identifier: domain_limits.CollectiveIdentifierLimits = (
        DomainCollectiveIdentifierLimitsFactory.build()
    )


@register_fixture(name="domain_limit_subject_certificate")
class DomainSubjectCertificateLimitsFactory(
    ModelFactory[domain_limits.SubjectCertificateLimits]
): ...


@register_fixture(name="domain_limit_subject_enrollment")
class DomainSubjectEnrollmentLimitsFactory(
    ModelFactory[domain_limits.SubjectEnrollmentLimits]
): ...


@register_fixture(name="domain_limit_subject")
class DomainSubjectLimitsFactory(ModelFactory[domain_limits.SubjectLimits]):
    certificate: domain_limits.SubjectCertificateLimits | None = (
        DomainSubjectCertificateLimitsFactory.build()
    )
    enrollment: domain_limits.SubjectEnrollmentLimits | None = (
        DomainSubjectEnrollmentLimitsFactory.build()
    )


@register_fixture(name="domain_limit_values")
class DomainRateLimitValuesFactory(ModelFactory[domain_limits.RateLimitValues]):
    per_second: int = 10
    per_minute: int = 100
    per_hour: int = 1000


@register_fixture(name="domain_limit_rate")
class DomainApiRateLimitsFactory(ModelFactory[domain_limits.ApiRateLimits]):
    online_session: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    online_session_close: domain_limits.RateLimitValues = (
        DomainRateLimitValuesFactory.build()
    )
    batch_session: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    batch_session_close: domain_limits.RateLimitValues = (
        DomainRateLimitValuesFactory.build()
    )
    invoice_send: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    invoice_status: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    session_list: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    session_invoice_list: domain_limits.RateLimitValues = (
        DomainRateLimitValuesFactory.build()
    )
    session_misc: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    invoice_metadata: domain_limits.RateLimitValues = (
        DomainRateLimitValuesFactory.build()
    )
    invoice_export: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    invoice_export_status: domain_limits.RateLimitValues = (
        DomainRateLimitValuesFactory.build()
    )
    invoice_download: domain_limits.RateLimitValues = (
        DomainRateLimitValuesFactory.build()
    )
    collective_identifier: domain_limits.RateLimitValues = (
        DomainRateLimitValuesFactory.build()
    )
    other: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    anonymous: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()
    global_: domain_limits.RateLimitValues = DomainRateLimitValuesFactory.build()


@register_fixture(name="limit_context_resp")
class EffectiveContextLimitsFactory(ModelFactory[spec.EffectiveContextLimits]): ...


@register_fixture(name="limit_subject_resp")
class EffectiveSubjectLimitsFactory(ModelFactory[spec.EffectiveSubjectLimits]): ...


@register_fixture(name="limit_rate_resp")
class EffectiveApiRateLimitsFactory(ModelFactory[spec.EffectiveApiRateLimits]):
    onlineSessionClose = spec.EffectiveApiRateLimitValues(
        perSecond=10, perMinute=100, perHour=1000
    )
    batchSessionClose = spec.EffectiveApiRateLimitValues(
        perSecond=10, perMinute=100, perHour=1000
    )
    anonymous = spec.EffectiveApiRateLimitValues(
        perSecond=10, perMinute=100, perHour=1000
    )
    global_ = spec.EffectiveApiRateLimitValues(
        perSecond=10, perMinute=100, perHour=1000
    )


@register_fixture(name="limit_set_session_req")
class SetSessionLimitsRequestFactory(ModelFactory[spec.SetSessionLimitsRequest]): ...


@register_fixture(name="limit_set_subject_req")
class SetSubjectLimitsRequestFactory(ModelFactory[spec.SetSubjectLimitsRequest]): ...


@register_fixture(name="limit_set_rate_req")
class SetRateLimitsRequestFactory(ModelFactory[spec.SetRateLimitsRequest]): ...
