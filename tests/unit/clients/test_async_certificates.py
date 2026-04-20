import asyncio

from polyfactory import BaseFactory

from ksef2.clients.async_certificates import AsyncCertificatesClient
from ksef2.core.routes import CertificateRoutes
from ksef2.domain.models import certificates
from ksef2.infra.schema.api import spec
from tests.unit.factories.certificates import CertificateListItemFactory
from tests.unit.fakes.transport import AsyncFakeTransport


async def _collect_async_items(iterator):
    items = []
    async for item in iterator:
        items.append(item)
    return items


class TestAsyncCertificatesClient:
    def test_get_limits(
        self,
        async_fake_transport: AsyncFakeTransport,
        cert_limits_resp: BaseFactory[spec.CertificateLimitsResponse],
    ):
        client = AsyncCertificatesClient(async_fake_transport)
        expected = cert_limits_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        result = asyncio.run(client.get_limits())

        assert isinstance(result, certificates.CertificateLimitsResponse)
        assert async_fake_transport.calls[0].method == "GET"
        assert str(async_fake_transport.calls[0].path) == CertificateRoutes.LIMITS

    def test_enroll(
        self,
        async_fake_transport: AsyncFakeTransport,
        cert_enroll_resp: BaseFactory[spec.EnrollCertificateResponse],
    ):
        client = AsyncCertificatesClient(async_fake_transport)
        expected = cert_enroll_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        result = asyncio.run(
            client.enroll(
                certificate_name="Test Cert",
                certificate_type="authentication",
                csr="dGVzdA==",
            )
        )

        assert isinstance(result, certificates.CertificateEnrollmentResponse)
        assert async_fake_transport.calls[0].method == "POST"
        assert str(async_fake_transport.calls[0].path) == CertificateRoutes.ENROLLMENT

    def test_all_multiple_pages(
        self,
        async_fake_transport: AsyncFakeTransport,
        cert_query_resp: BaseFactory[spec.QueryCertificatesResponse],
    ):
        client = AsyncCertificatesClient(async_fake_transport)
        page1 = cert_query_resp.build(
            certificates=[
                CertificateListItemFactory.build(certificateSerialNumber="SN001"),
                CertificateListItemFactory.build(certificateSerialNumber="SN002"),
            ],
            hasMore=True,
        )
        page2 = cert_query_resp.build(
            certificates=[
                CertificateListItemFactory.build(certificateSerialNumber="SN003")
            ],
            hasMore=False,
        )
        async_fake_transport.enqueue(page1.model_dump(mode="json"))
        async_fake_transport.enqueue(page2.model_dump(mode="json"))

        items = asyncio.run(_collect_async_items(client.all()))

        assert len(items) == 3
        assert items[2].serial_number == "SN003"
