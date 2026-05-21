from polyfactory import BaseFactory

from ksef2.domain.models import invoices as domain_invoices
from ksef2.domain.models.session import FormSchema
from ksef2.domain.models.invoices import ExportInvoicesPayload, SendInvoicePayload
from ksef2.infra.mappers.invoices import from_spec, to_spec
from ksef2.infra.schema.api import spec


class TestInvoicesRequestMapper:
    def test_to_spec_legacy_invoices_filter(self, inv_export_filters) -> None:
        request = inv_export_filters.build(invoice_schema=FormSchema.FA_RR1)

        output = to_spec(request)

        assert isinstance(output, spec.InvoiceQueryFilters)
        assert output.subjectType == spec.InvoiceQuerySubjectType.Subject1
        assert output.dateRange.dateType == spec.InvoiceQueryDateType.Issue
        assert output.formType == spec.InvoiceQueryFormType.FA_RR

    def test_to_export_request(self, inv_export_filters) -> None:
        request = ExportInvoicesPayload(
            filter=inv_export_filters.build(),
            encrypted_symmetric_key="enc",
            initialization_vector="iv",
            only_metadata=True,
            compression_type="tar_gz",
        )

        output = to_spec(request)

        assert isinstance(output, spec.InvoiceExportRequest)
        assert output.encryption.encryptedSymmetricKey == "enc"
        assert output.encryption.initializationVector == "iv"
        assert output.onlyMetadata is True
        assert output.filters.subjectType == spec.InvoiceQuerySubjectType.Subject1
        assert output.compressionType == spec.CompressionType.TarGz

    def test_to_send_invoice_request(self) -> None:
        output = to_spec(
            SendInvoicePayload(
                xml_bytes=b"<xml />",
                encrypted_bytes=b"encrypted",
            )
        )

        assert isinstance(output, spec.SendInvoiceRequest)
        assert output.invoiceSize == len(b"<xml />")
        assert output.encryptedInvoiceSize == len(b"encrypted")
        assert output.encryptedInvoiceContent == "ZW5jcnlwdGVk"


class TestInvoicesResponseMapper:
    def test_from_spec_send_invoice_response(
        self, inv_send_resp: BaseFactory[spec.SendInvoiceResponse]
    ) -> None:
        response = inv_send_resp.build()
        output = from_spec(response)

        assert isinstance(output, domain_invoices.SendInvoiceResponse)
        assert output.reference_number == response.referenceNumber

    def test_from_spec_query_metadata_response(
        self, inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse]
    ) -> None:
        response = inv_query_metadata_resp.build()
        output = from_spec(response)

        assert isinstance(output, domain_invoices.QueryInvoicesMetadataResponse)
        assert output.has_more == response.hasMore
        assert len(output.invoices) == len(response.invoices)

    def test_from_spec_export_response(
        self, inv_export_resp: BaseFactory[spec.ExportInvoicesResponse]
    ) -> None:
        response = inv_export_resp.build()
        output = from_spec(response)

        assert isinstance(output, domain_invoices.ExportInvoicesResponse)
        assert output.reference_number == response.referenceNumber

    def test_from_spec_export_status_response(
        self, inv_export_status_resp: BaseFactory[spec.InvoiceExportStatusResponse]
    ) -> None:
        response = inv_export_status_resp.build()
        output = from_spec(response)

        assert isinstance(output, domain_invoices.InvoiceExportStatusResponse)
        assert output.status.code == response.status.code
