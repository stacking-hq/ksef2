import asyncio
from unittest.mock import MagicMock, patch

from polyfactory import BaseFactory

from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_invoices import AsyncInvoicesClient
from ksef2.core.routes import EncryptionRoutes, InvoiceRoutes
from ksef2.core.stores import CertificateStore
from ksef2.domain.models import invoices
from ksef2.domain.models.pagination import InvoiceMetadataParams
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models.session import FormSchema
from ksef2.infra.mappers.invoices import to_spec
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport


def _build_client(
    async_fake_transport: AsyncFakeTransport,
    auth_tokens: AuthTokens,
    certificate_store: CertificateStore | None = None,
) -> AsyncAuthenticatedClient:
    return AsyncAuthenticatedClient(
        transport=async_fake_transport,
        auth_tokens=auth_tokens,
        certificate_store=certificate_store or CertificateStore(),
    )


class TestAsyncInvoicesClient:
    def test_query_metadata(
        self,
        async_fake_transport: AsyncFakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        invoices_client = AsyncInvoicesClient(async_fake_transport)
        expected = inv_query_metadata_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        filters = inv_export_filters.build(invoice_schema=FormSchema.FA_RR1)
        result = asyncio.run(
            invoices_client.query_metadata(
                filters=filters,
                params=InvoiceMetadataParams(
                    page_size=20,
                    page_offset=1,
                    sort_order="asc",
                ),
            )
        )
        expected_request = to_spec(filters)

        assert isinstance(result, invoices.QueryInvoicesMetadataResponse)
        call = async_fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == InvoiceRoutes.QUERY_METADATA
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request
        assert call.params is not None
        assert call.params["pageSize"] == "20"
        assert call.params["pageOffset"] == "1"
        assert call.params["sortOrder"] == "Asc"

    @patch(
        "ksef2.clients.async_invoices.encrypt_symmetric_key", return_value=b"enc-key"
    )
    @patch(
        "ksef2.clients.async_invoices.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_schedule_export(
        self,
        _mock_generate_session_key: MagicMock,
        _mock_encrypt_symmetric_key: MagicMock,
        async_fake_transport: AsyncFakeTransport,
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_export_resp: BaseFactory[spec.ExportInvoicesResponse],
    ) -> None:
        invoices_client = AsyncInvoicesClient(async_fake_transport)
        expected = inv_export_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        filters = inv_export_filters.build()
        result = asyncio.run(
            invoices_client.schedule_export(
                filters=filters,
                encryption_certificate="ZmFrZS1jZXJ0",
                only_metadata=True,
            )
        )
        expected_request = to_spec(
            invoices.ExportInvoicesPayload(
                filter=filters,
                encrypted_symmetric_key="ZW5jLWtleQ==",
                initialization_vector="dnZ2dnZ2dnZ2dnZ2dnZ2dg==",
                only_metadata=True,
            )
        )

        assert isinstance(result, invoices.ExportHandle)
        assert result.reference_number == expected.referenceNumber
        call = async_fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == InvoiceRoutes.EXPORT
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request


class TestAsyncAuthenticatedInvoicesService:
    def test_query_metadata_uses_bearer_transport(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_query_metadata_resp: BaseFactory[spec.QueryInvoicesMetadataResponse],
    ) -> None:
        client = _build_client(async_fake_transport, domain_auth_tokens.build())
        async_fake_transport.enqueue(
            inv_query_metadata_resp.build().model_dump(mode="json")
        )

        _ = asyncio.run(
            client.invoices.query_metadata(filters=inv_export_filters.build())
        )

        call = async_fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == InvoiceRoutes.QUERY_METADATA
        assert call.headers == {"Authorization": "Bearer fake-access-token"}

    @patch(
        "ksef2.clients.async_invoices.encrypt_symmetric_key", return_value=b"enc-key"
    )
    @patch(
        "ksef2.clients.async_invoices.generate_session_key",
        return_value=(b"k" * 32, b"v" * 16),
    )
    def test_schedule_export_loads_certificates_when_store_empty(
        self,
        _mock_generate_session_key: MagicMock,
        _mock_encrypt_symmetric_key: MagicMock,
        async_fake_transport: AsyncFakeTransport,
        domain_auth_tokens: BaseFactory[AuthTokens],
        public_key_cert: BaseFactory[spec.PublicKeyCertificate],
        inv_export_filters: BaseFactory[invoices.InvoicesFilter],
        inv_export_resp: BaseFactory[spec.ExportInvoicesResponse],
    ) -> None:
        client = _build_client(async_fake_transport, domain_auth_tokens.build())
        async_fake_transport.enqueue(
            json_body=[
                public_key_cert.build(
                    usage=[spec.PublicKeyCertificateUsage.SymmetricKeyEncryption]
                ).model_dump(mode="json")
            ]
        )
        async_fake_transport.enqueue(inv_export_resp.build().model_dump(mode="json"))

        result = asyncio.run(
            client.invoices.schedule_export(filters=inv_export_filters.build())
        )

        assert isinstance(result, invoices.ExportHandle)
        assert (
            async_fake_transport.calls[0].path
            == EncryptionRoutes.PUBLIC_KEY_CERTIFICATES
        )
        assert async_fake_transport.calls[1].path == InvoiceRoutes.EXPORT
