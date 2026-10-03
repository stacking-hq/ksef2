"""Mappings from limit domain models to generated API schema models."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2._domain.models.limits import (
    ApiRateLimits,
    ContextLimits,
    RateLimitValues,
    SubjectLimits,
)
from ksef2._infra.schema.api import spec


@overload
def to_spec(request: ContextLimits) -> spec.SetSessionLimitsRequest: ...


@overload
def to_spec(request: SubjectLimits) -> spec.SetSubjectLimitsRequest: ...


@overload
def to_spec(request: ApiRateLimits) -> spec.SetRateLimitsRequest: ...


def to_spec(request: BaseModel) -> object:
    """Convert a limit override model into the schema payload expected by KSeF."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: ContextLimits) -> spec.SetSessionLimitsRequest:
    return spec.SetSessionLimitsRequest(
        onlineSession=spec.OnlineSessionContextLimitsOverride(
            maxInvoices=request.online_session.max_invoices,
            maxInvoiceSizeInMB=request.online_session.max_invoice_size_mb,
            maxInvoiceWithAttachmentSizeInMB=request.online_session.max_invoice_with_attachment_size_mb,
        ),
        batchSession=spec.BatchSessionContextLimitsOverride(
            maxInvoices=request.batch_session.max_invoices,
            maxInvoiceSizeInMB=request.batch_session.max_invoice_size_mb,
            maxInvoiceWithAttachmentSizeInMB=request.batch_session.max_invoice_with_attachment_size_mb,
        ),
        collectiveIdentifier=spec.CollectiveIdentifierContextLimitsOverride(
            maxInvoices=request.collective_identifier.max_invoices,
        ),
    )


@_to_spec.register
def _(request: SubjectLimits) -> spec.SetSubjectLimitsRequest:
    return spec.SetSubjectLimitsRequest(
        subjectIdentifierType=spec.SubjectIdentifierType.Nip,
        certificate=(
            spec.CertificateSubjectLimitsOverride(
                maxCertificates=request.certificate.max_certificates,
            )
            if request.certificate is not None
            else None
        ),
        enrollment=(
            spec.EnrollmentSubjectLimitsOverride(
                maxEnrollments=request.enrollment.max_enrollments,
            )
            if request.enrollment is not None
            else None
        ),
    )


def _map_rate_limit_values(values: RateLimitValues) -> spec.ApiRateLimitValuesOverride:
    return spec.ApiRateLimitValuesOverride(
        perSecond=values.per_second,
        perMinute=values.per_minute,
        perHour=values.per_hour,
    )


@_to_spec.register
def _(request: ApiRateLimits) -> spec.SetRateLimitsRequest:
    return spec.SetRateLimitsRequest(
        rateLimits=spec.ApiRateLimitsOverride(
            onlineSession=_map_rate_limit_values(request.online_session),
            batchSession=_map_rate_limit_values(request.batch_session),
            invoiceSend=_map_rate_limit_values(request.invoice_send),
            invoiceStatus=_map_rate_limit_values(request.invoice_status),
            sessionList=_map_rate_limit_values(request.session_list),
            sessionInvoiceList=_map_rate_limit_values(request.session_invoice_list),
            sessionMisc=_map_rate_limit_values(request.session_misc),
            invoiceMetadata=_map_rate_limit_values(request.invoice_metadata),
            invoiceExport=_map_rate_limit_values(request.invoice_export),
            invoiceExportStatus=_map_rate_limit_values(request.invoice_export_status),
            invoiceDownload=_map_rate_limit_values(request.invoice_download),
            collectiveIdentifier=_map_rate_limit_values(request.collective_identifier),
            other=_map_rate_limit_values(request.other),
        )
    )
