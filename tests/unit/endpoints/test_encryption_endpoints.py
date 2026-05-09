import pytest

from ksef2.core import exceptions
from ksef2.core.routes import EncryptionRoutes
from ksef2.endpoints.encryption import EncryptionEndpoints
from tests.unit.fakes import transport

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


class TestEncryptionEndpoints:
    @pytest.fixture
    def encryption_eps(
        self, fake_transport: transport.FakeTransport
    ) -> EncryptionEndpoints:
        return EncryptionEndpoints(fake_transport)

    @pytest.fixture
    def handled_encryption_eps(
        self, fake_transport: transport.FakeTransport
    ) -> EncryptionEndpoints:
        return EncryptionEndpoints(KSeFExceptionMiddleware(fake_transport))

    def test_fetch_public_certificates(
        self,
        encryption_eps: EncryptionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        expected_data = [
            {
                "certificate": "dGVzdC1jZXJ0aWZpY2F0ZS1kYXRh",
                "validFrom": "2025-01-01T00:00:00Z",
                "validTo": "2026-01-01T00:00:00Z",
                "usage": ["SymmetricKeyEncryption"],
            }
        ]

        fake_transport.enqueue(expected_data)
        result = encryption_eps.fetch_public_certificates()

        assert len(result) == 1
        assert result[0].certificate == "dGVzdC1jZXJ0aWZpY2F0ZS1kYXRh"
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == EncryptionRoutes.PUBLIC_KEY_CERTIFICATES
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_fetch_public_certificates_response_validation(
        self,
        encryption_eps: EncryptionEndpoints,
        fake_transport: transport.FakeTransport,
        public_key_cert,
    ):
        response_data = [
            public_key_cert.build().model_dump(mode="json")
            | {"invalid_field": "invalid"}
        ]

        fake_transport.enqueue(response_data)
        _ = encryption_eps.fetch_public_certificates()

        assert fake_transport.responses == []

    def test_fetch_public_certificates_transport_error(
        self,
        handled_encryption_eps: EncryptionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        valid_data = [
            {
                "certificate": "dGVzdC1jZXJ0aWZpY2F0ZS1kYXRh",
                "validFrom": "2025-01-01T00:00:00Z",
                "validTo": "2026-01-01T00:00:00Z",
                "usage": ["SymmetricKeyEncryption"],
            }
        ]

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=valid_data,
                status_code=code,
            )

            with pytest.raises(exc):
                _ = handled_encryption_eps.fetch_public_certificates()

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == EncryptionRoutes.PUBLIC_KEY_CERTIFICATES
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []
