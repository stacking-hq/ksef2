from polyfactory import BaseFactory

from ksef2.clients.certificates import CertificatesClient
from ksef2.core.routes import CertificateRoutes
from ksef2.domain.models import certificates
from ksef2.infra.mappers.certificates import to_spec
from ksef2.infra.schema.api import spec
from tests.unit.factories.certificates import (
    CertificateListItemFactory,
)
from tests.unit.fakes.transport import FakeTransport


class TestCertificatesClient:
    def test_initialization(self, certificates_client: CertificatesClient):
        assert certificates_client is not None

    def test_get_limits(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_limits_resp: BaseFactory[spec.CertificateLimitsResponse],
    ):
        expected = cert_limits_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.get_limits()

        assert isinstance(result, certificates.CertificateLimitsResponse)
        assert result.can_request == expected.canRequest
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == CertificateRoutes.LIMITS

    def test_get_enrollment_data(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_enrollment_data_resp: BaseFactory[spec.CertificateEnrollmentDataResponse],
    ):
        expected = cert_enrollment_data_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.get_enrollment_data()

        assert isinstance(result, certificates.CertificateEnrollmentData)
        assert result.common_name == expected.commonName
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == CertificateRoutes.ENROLLMENT_DATA

    def test_enroll(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_enroll_resp: BaseFactory[spec.EnrollCertificateResponse],
    ):
        expected = cert_enroll_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.enroll(
            certificate_name="Test Cert",
            certificate_type="authentication",
            csr="dGVzdA==",
        )
        expected_request = to_spec(
            certificates.EnrollCertificateRequest(
                certificate_name="Test Cert",
                certificate_type="authentication",
                csr="dGVzdA==",
            )
        )

        assert isinstance(result, certificates.CertificateEnrollmentResponse)
        assert result.reference_number == expected.referenceNumber
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.ENROLLMENT
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request

    def test_enroll_with_valid_from(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_enroll_resp: BaseFactory[spec.EnrollCertificateResponse],
    ):
        expected = cert_enroll_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.enroll(
            certificate_name="Test Cert",
            certificate_type="offline",
            csr="dGVzdA==",
            valid_from="2025-06-01T12:00:00+00:00",
        )
        expected_request = to_spec(
            certificates.EnrollCertificateRequest(
                certificate_name="Test Cert",
                certificate_type="offline",
                csr="dGVzdA==",
                valid_from="2025-06-01T12:00:00+00:00",
            )
        )

        assert isinstance(result, certificates.CertificateEnrollmentResponse)
        call = fake_transport.calls[0]
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request
        assert actual_request.validFrom is not None

    def test_get_enrollment_status(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_enrollment_status_resp: BaseFactory[
            spec.CertificateEnrollmentStatusResponse
        ],
    ):
        expected = cert_enrollment_status_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.get_enrollment_status(
            reference_number="ref-123",
        )

        assert isinstance(result, certificates.CertificateEnrollmentStatusResponse)
        assert result.request_date == expected.requestDate
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert "ref-123" in str(call.path)

    def test_retrieve(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_retrieve_resp: BaseFactory[spec.RetrieveCertificatesResponse],
    ):
        expected = cert_retrieve_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.retrieve(
            certificate_serial_numbers=["SN123", "SN456"],
        )
        expected_request = to_spec(
            certificates.RetrieveCertificatesRequest(
                certificate_serial_numbers=["SN123", "SN456"],
            )
        )

        assert isinstance(result, certificates.RetrievedCertificatesList)
        assert len(result.certificates) == len(expected.certificates)
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.RETRIEVE
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request

    def test_revoke(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
    ):
        fake_transport.enqueue()  # status 200 by default

        certificates_client.revoke(
            certificate_serial_number="SN123",
            reason="superseded",
        )

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert "SN123" in str(call.path)

    def test_revoke_without_reason(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
    ):
        fake_transport.enqueue()  # status 200 by default

        certificates_client.revoke(
            certificate_serial_number="SN123",
        )

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.json is None

    def test_query(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_query_resp: BaseFactory[spec.QueryCertificatesResponse],
    ):
        expected = cert_query_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.query()

        assert isinstance(result, certificates.CertificatesInfoList)
        assert len(result.certificates) == len(expected.certificates)
        assert result.has_more == expected.hasMore
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.QUERY

    def test_query_with_filters(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_query_resp: BaseFactory[spec.QueryCertificatesResponse],
    ):
        expected = cert_query_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = certificates_client.query(
            name="Test",
            certificate_serial_number="SN123",
            certificate_type="authentication",
            status="active",
        )
        expected_request = to_spec(
            certificates.QueryCertificatesRequest(
                name="Test",
                certificate_serial_number="SN123",
                certificate_type="authentication",
                status="active",
            )
        )

        assert isinstance(result, certificates.CertificatesInfoList)
        call = fake_transport.calls[0]
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request

    def test_all_single_page(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_query_resp: BaseFactory[spec.QueryCertificatesResponse],
    ):
        expected = cert_query_resp.build(
            certificates=[CertificateListItemFactory.build()],
            hasMore=False,
        )
        fake_transport.enqueue(expected.model_dump(mode="json"))

        items = list(certificates_client.all())

        assert len(items) == 1
        assert len(fake_transport.calls) == 1

    def test_all_multiple_pages(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_query_resp: BaseFactory[spec.QueryCertificatesResponse],
    ):
        page1 = cert_query_resp.build(
            certificates=[
                CertificateListItemFactory.build(certificateSerialNumber="SN001"),
                CertificateListItemFactory.build(certificateSerialNumber="SN002"),
            ],
            hasMore=True,
        )
        page2 = cert_query_resp.build(
            certificates=[
                CertificateListItemFactory.build(certificateSerialNumber="SN003"),
            ],
            hasMore=False,
        )
        fake_transport.enqueue(page1.model_dump(mode="json"))
        fake_transport.enqueue(page2.model_dump(mode="json"))

        items = list(certificates_client.all())

        assert len(items) == 3
        assert items[0].serial_number == "SN001"
        assert items[1].serial_number == "SN002"
        assert items[2].serial_number == "SN003"
        assert len(fake_transport.calls) == 2

    def test_all_empty(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_query_resp: BaseFactory[spec.QueryCertificatesResponse],
    ):
        expected = cert_query_resp.build(certificates=[], hasMore=False)
        fake_transport.enqueue(expected.model_dump(mode="json"))

        items = list(certificates_client.all())

        assert len(items) == 0
        assert len(fake_transport.calls) == 1

    def test_all_with_filters(
        self,
        certificates_client: CertificatesClient,
        fake_transport: FakeTransport,
        cert_query_resp: BaseFactory[spec.QueryCertificatesResponse],
    ):
        expected = cert_query_resp.build(
            certificates=[CertificateListItemFactory.build()],
            hasMore=False,
        )
        fake_transport.enqueue(expected.model_dump(mode="json"))

        items = list(
            certificates_client.all(
                status="active",
                certificate_type="authentication",
            )
        )
        expected_request = to_spec(
            certificates.QueryCertificatesRequest(
                status="active",
                certificate_type="authentication",
            )
        )

        assert len(items) == 1
        call = fake_transport.calls[0]
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request
