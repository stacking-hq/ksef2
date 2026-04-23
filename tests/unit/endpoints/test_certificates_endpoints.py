from typing import cast, Callable

import pytest

from polyfactory.factories import BaseFactory
from pydantic import BaseModel

from ksef2.core import exceptions
from ksef2.core.routes import CertificateRoutes
from ksef2.endpoints.certificates import CertificatesEndpoints
from tests.unit.fakes import transport
from tests.unit.factories.certificates import (
    EnrollCertificateRequestFactory,
    EnrollCertificateResponseFactory,
    CertificateEnrollmentStatusResponseFactory,
    RetrieveCertificatesRequestFactory,
    RetrieveCertificatesResponseFactory,
    RevokeCertificateRequestFactory,
    QueryCertificatesRequestFactory,
    QueryCertificatesResponseFactory,
)

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


class InvalidContent(BaseModel):
    invalid_field: str


@pytest.fixture
def req_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


@pytest.fixture
def resp_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


class TestCertificateEndpoints:
    @pytest.fixture
    def cert_eps(
        self, fake_transport: transport.FakeTransport
    ) -> CertificatesEndpoints:
        return CertificatesEndpoints(fake_transport)

    @pytest.fixture
    def handled_cert_eps(
        self, fake_transport: transport.FakeTransport
    ) -> CertificatesEndpoints:
        return CertificatesEndpoints(KSeFExceptionMiddleware(fake_transport))

    @pytest.mark.parametrize(
        ["target_path", "method", "resp_factory"],
        [
            (
                CertificateRoutes.LIMITS,
                CertificatesEndpoints.get_limits,
                "cert_limits_resp",
            ),
            (
                CertificateRoutes.ENROLLMENT_DATA,
                CertificatesEndpoints.get_enrollment_data,
                "cert_enrollment_data_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_happy_path_get(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[], BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        expected = resp_factory.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = cast(BaseModel, getattr(cert_eps, method.__name__)())

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert target_path == call.path
        assert call.json is None
        assert call.content is None
        assert call.headers is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method", "resp_factory"],
        [
            (
                CertificateRoutes.LIMITS,
                CertificatesEndpoints.get_limits,
                "cert_limits_resp",
            ),
            (
                CertificateRoutes.ENROLLMENT_DATA,
                CertificatesEndpoints.get_enrollment_data,
                "cert_enrollment_data_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_response_validation_get(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[], BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        response_dump = InvalidContent(invalid_field="invalid").model_dump()

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(response_dump)
            _ = getattr(cert_eps, method.__name__)()

        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method", "resp_factory"],
        [
            (
                CertificateRoutes.LIMITS,
                CertificatesEndpoints.get_limits,
                "cert_limits_resp",
            ),
            (
                CertificateRoutes.ENROLLMENT_DATA,
                CertificatesEndpoints.get_enrollment_data,
                "cert_enrollment_data_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_transport_error_get(
        self,
        handled_cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[], BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        response = resp_factory.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                status_code=code,
                json_body=response.model_dump(mode="json"),
            )

            with pytest.raises(exc):
                _ = getattr(handled_cert_eps, method.__name__)()

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert target_path == call.path
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    def test_enroll(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_enroll_req: EnrollCertificateRequestFactory,
        cert_enroll_resp: EnrollCertificateResponseFactory,
    ):
        request = cert_enroll_req.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = cert_enroll_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = cert_eps.enroll(request)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.ENROLLMENT
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_enroll_response_validation(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_enroll_req: EnrollCertificateRequestFactory,
    ):
        request = cert_enroll_req.build()
        invalid_response = InvalidContent(invalid_field="invalid")

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(invalid_response.model_dump(mode="json"))
            _ = cert_eps.enroll(request)

        assert fake_transport.responses == []

    def test_enroll_transport_error(
        self,
        handled_cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_enroll_req: EnrollCertificateRequestFactory,
        cert_enroll_resp: EnrollCertificateResponseFactory,
    ):
        request = cert_enroll_req.build()
        response = cert_enroll_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                status_code=code,
                json_body=response.model_dump(mode="json"),
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_cert_eps.enroll(request))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == CertificateRoutes.ENROLLMENT
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.headers is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_get_enrollment_status(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_enrollment_status_resp: CertificateEnrollmentStatusResponseFactory,
    ):
        expected = cert_enrollment_status_resp.build()
        expected_dump = expected.model_dump(mode="json")
        reference_number = "20250625-CERT-2C3E6C8000-B675CF5D68-07"

        fake_transport.enqueue(expected_dump)
        response = cert_eps.get_enrollment_status(reference_number)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == CertificateRoutes.ENROLLMENT_STATUS.format(
            referenceNumber=reference_number
        )
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_get_enrollment_status_response_validation(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        invalid_response = InvalidContent(invalid_field="invalid")

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(invalid_response.model_dump(mode="json"))
            _ = cert_eps.get_enrollment_status("dummy-ref")

        assert fake_transport.responses == []

    def test_get_enrollment_status_transport_error(
        self,
        handled_cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_enrollment_status_resp: CertificateEnrollmentStatusResponseFactory,
    ):
        response = cert_enrollment_status_resp.build()
        reference_number = "20250625-CERT-2C3E6C8000-B675CF5D68-07"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel,
                    handled_cert_eps.get_enrollment_status(reference_number),
                )

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == CertificateRoutes.ENROLLMENT_STATUS.format(
                referenceNumber=reference_number
            )
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    def test_retrieve(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_retrieve_req: RetrieveCertificatesRequestFactory,
        cert_retrieve_resp: RetrieveCertificatesResponseFactory,
    ):
        request = cert_retrieve_req.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = cert_retrieve_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = cert_eps.retrieve(request)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.RETRIEVE
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_retrieve_response_validation(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_retrieve_req: RetrieveCertificatesRequestFactory,
    ):
        request = cert_retrieve_req.build()
        invalid_response = InvalidContent(invalid_field="invalid")

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(invalid_response.model_dump(mode="json"))
            _ = cert_eps.retrieve(request)

        assert fake_transport.responses == []

    def test_retrieve_transport_error(
        self,
        handled_cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_retrieve_req: RetrieveCertificatesRequestFactory,
        cert_retrieve_resp: RetrieveCertificatesResponseFactory,
    ):
        request = cert_retrieve_req.build()
        response = cert_retrieve_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                status_code=code,
                json_body=response.model_dump(mode="json"),
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_cert_eps.retrieve(request))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == CertificateRoutes.RETRIEVE
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.headers is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_revoke(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_revoke_req: RevokeCertificateRequestFactory,
    ):
        request = cert_revoke_req.build()
        certificate_serial_number = "ABC123DEF4567890"

        fake_transport.enqueue(json_body={})
        cert_eps.revoke(certificate_serial_number, request)

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.REVOKE.format(
            certificateSerialNumber=certificate_serial_number
        )
        assert call.json is not None
        assert call.json == request.model_dump(mode="json")
        assert call.content is None
        assert fake_transport.responses == []

    def test_revoke_without_body(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        certificate_serial_number = "ABC123DEF4567890"

        fake_transport.enqueue(json_body={})
        cert_eps.revoke(certificate_serial_number)

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.REVOKE.format(
            certificateSerialNumber=certificate_serial_number
        )
        assert call.json is None
        assert fake_transport.responses == []

    def test_revoke_transport_error(
        self,
        handled_cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        certificate_serial_number = "ABC123DEF4567890"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code, json_body={})

            with pytest.raises(exc):
                handled_cert_eps.revoke(certificate_serial_number)

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == CertificateRoutes.REVOKE.format(
                certificateSerialNumber=certificate_serial_number
            )
            assert call.headers is None
            assert call.content is None

            assert fake_transport.responses == []

    def test_query(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_query_req: QueryCertificatesRequestFactory,
        cert_query_resp: QueryCertificatesResponseFactory,
    ):
        request = cert_query_req.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = cert_query_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = cert_eps.query(request, pageSize=10, pageOffset=0)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == CertificateRoutes.QUERY
        assert call.json is not None
        assert call.json == request_dump
        assert call.params is not None
        assert call.params.get("pageSize") == "10"
        assert call.params.get("pageOffset") == "0"
        assert call.content is None
        assert call.headers is None
        assert fake_transport.responses == []

    def test_query_response_validation(
        self,
        cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_query_req: QueryCertificatesRequestFactory,
    ):
        request = cert_query_req.build()
        invalid_response = InvalidContent(invalid_field="invalid")

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(invalid_response.model_dump(mode="json"))
            _ = cert_eps.query(request)

        assert fake_transport.responses == []

    def test_query_transport_error(
        self,
        handled_cert_eps: CertificatesEndpoints,
        fake_transport: transport.FakeTransport,
        cert_query_req: QueryCertificatesRequestFactory,
        cert_query_resp: QueryCertificatesResponseFactory,
    ):
        request = cert_query_req.build()
        response = cert_query_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                status_code=code,
                json_body=response.model_dump(mode="json"),
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_cert_eps.query(request))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == CertificateRoutes.QUERY
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.headers is None

            assert fake_transport.responses == []
