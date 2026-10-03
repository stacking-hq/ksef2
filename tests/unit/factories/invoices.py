from datetime import datetime, timedelta, timezone

from ksef2._domain.models.invoices import (
    ExportHandle,
    InvoicePackage,
    InvoicesFilter,
    PackagePart,
)
from ksef2._infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

_NOW = datetime.now(timezone.utc)
_EARLIER = _NOW - timedelta(days=7)

"""
Request/Response Factories for spec models
"""


@register_fixture(name="inv_query_metadata_req")
class QueryInvoicesMetadataRequestFactory(
    ModelFactory[spec.QueryInvoicesMetadataRequest]
): ...


@register_fixture(name="inv_query_metadata_resp")
class QueryInvoicesMetadataResponseFactory(
    ModelFactory[spec.QueryInvoicesMetadataResponse]
): ...


@register_fixture(name="inv_export_req")
class InvoiceExportRequestFactory(ModelFactory[spec.InvoiceExportRequest]): ...


@register_fixture(name="inv_export_resp")
class ExportInvoicesResponseFactory(ModelFactory[spec.ExportInvoicesResponse]): ...


@register_fixture(name="inv_export_status_resp")
class InvoiceExportStatusResponseFactory(
    ModelFactory[spec.InvoiceExportStatusResponse]
): ...


@register_fixture(name="inv_send_req")
class SendInvoiceRequestFactory(ModelFactory[spec.SendInvoiceRequest]): ...


@register_fixture(name="inv_send_resp")
class SendInvoiceResponseFactory(ModelFactory[spec.SendInvoiceResponse]): ...


@register_fixture(name="inv_session_status_resp")
class SessionStatusResponseFactory(ModelFactory[spec.SessionStatusResponse]): ...


@register_fixture(name="inv_session_invoices_resp")
class SessionInvoicesResponseFactory(ModelFactory[spec.SessionInvoicesResponse]): ...


@register_fixture(name="inv_session_invoice_status_resp")
class SessionInvoiceStatusResponseFactory(
    ModelFactory[spec.SessionInvoiceStatusResponse]
): ...


"""Factories for public API models
"""


@register_fixture(name="inv_export_filters")
class InvoicesFilterFactory(ModelFactory[InvoicesFilter]):
    role = "seller"
    date_type = "issue_date"
    date_from = _EARLIER
    date_to = _NOW
    currency_codes = None
    amount_type = "brutto"
    amount_min = 10.0
    amount_max = 100.0
    seller_nip = "1234567890"
    buyer_nip = None
    buyer_vat_ue = None
    buyer_other_id = None
    invoice_number = None
    ksef_number = None
    invoice_schema = None
    invoice_types = None
    has_attachment = False
    invoicing_mode = "online"
    is_self_invoicing = False


@register_fixture(name="inv_package_part")
class PackagePartFactory(ModelFactory[PackagePart]): ...


@register_fixture(name="inv_package")
class InvoicePackageFactory(ModelFactory[InvoicePackage]): ...


class ExportHandleFactory(ModelFactory[ExportHandle]): ...
