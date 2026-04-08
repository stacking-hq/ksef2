from polyfactory import BaseFactory

from ksef2.domain.models.limits import ApiRateLimits, ContextLimits, SubjectLimits
from ksef2.infra.mappers.limits import from_spec, to_spec
from ksef2.infra.schema.api import spec


class TestLimitRequestMappers:
    def test_to_spec_context_limits(
        self,
        domain_limit_context: BaseFactory[ContextLimits],
    ) -> None:
        request = domain_limit_context.build()

        result = to_spec(request)

        assert isinstance(result, spec.SetSessionLimitsRequest)
        assert result.onlineSession.maxInvoices == request.online_session.max_invoices
        assert result.batchSession.maxInvoiceSizeInMB == (
            request.batch_session.max_invoice_size_mb
        )

    def test_to_spec_subject_limits(
        self,
        domain_limit_subject: BaseFactory[SubjectLimits],
    ) -> None:
        request = domain_limit_subject.build()

        result = to_spec(request)

        assert isinstance(result, spec.SetSubjectLimitsRequest)
        assert result.certificate is not None
        assert request.certificate is not None
        assert (
            result.certificate.maxCertificates == request.certificate.max_certificates
        )
        assert result.enrollment is not None
        assert request.enrollment is not None
        assert result.enrollment.maxEnrollments == request.enrollment.max_enrollments

    def test_to_spec_api_rate_limits(
        self,
        domain_limit_rate: BaseFactory[ApiRateLimits],
    ) -> None:
        request = domain_limit_rate.build()

        result = to_spec(request)

        assert isinstance(result, spec.SetRateLimitsRequest)
        assert (
            result.rateLimits.onlineSession.perSecond
            == request.online_session.per_second
        )
        assert result.rateLimits.other.perHour == request.other.per_hour


class TestLimitResponseMappers:
    def test_from_spec_context_limits(
        self,
        limit_context_resp: BaseFactory[spec.EffectiveContextLimits],
    ) -> None:
        response = limit_context_resp.build()

        result = from_spec(response)

        assert isinstance(result, ContextLimits)
        assert result.online_session.max_invoices == response.onlineSession.maxInvoices
        assert result.batch_session.max_invoice_size_mb == (
            response.batchSession.maxInvoiceSizeInMB
        )

    def test_from_spec_subject_limits(
        self,
        limit_subject_resp: BaseFactory[spec.EffectiveSubjectLimits],
    ) -> None:
        response = limit_subject_resp.build(
            certificate=spec.CertificateEffectiveSubjectLimits(maxCertificates=7),
            enrollment=spec.EnrollmentEffectiveSubjectLimits(maxEnrollments=11),
        )

        result = from_spec(response)

        assert isinstance(result, SubjectLimits)
        assert result.certificate is not None
        assert response.certificate is not None
        assert (
            result.certificate.max_certificates == response.certificate.maxCertificates
        )
        assert result.enrollment is not None
        assert response.enrollment is not None
        assert result.enrollment.max_enrollments == response.enrollment.maxEnrollments

    def test_from_spec_api_rate_limits(
        self,
        limit_rate_resp: BaseFactory[spec.EffectiveApiRateLimits],
    ) -> None:
        response = limit_rate_resp.build()

        result = from_spec(response)

        assert isinstance(result, ApiRateLimits)
        assert result.invoice_send.per_minute == response.invoiceSend.perMinute
        assert result.other.per_hour == response.other.perHour
