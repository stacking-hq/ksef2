from polyfactory import BaseFactory

from ksef2.domain.models.encryption import PublicKeyCertificate
from ksef2.infra.mappers.encryption import from_spec, to_spec, usage_from_spec
from ksef2.infra.schema.api import spec


class TestEncryptionResponseMapper:
    def test_map_usage_ksef_token_encryption(self):
        assert (
            usage_from_spec(spec.PublicKeyCertificateUsage.KsefTokenEncryption)
            == "ksef_token_encryption"
        )

    def test_map_usage_symmetric_key_encryption(self):
        assert (
            usage_from_spec(spec.PublicKeyCertificateUsage.SymmetricKeyEncryption)
            == "symmetric_key_encryption"
        )

    def test_map_public_key_certificate(
        self, public_key_cert: BaseFactory[spec.PublicKeyCertificate]
    ):
        mapped_input = public_key_cert.build()
        output = from_spec(mapped_input)

        assert isinstance(output, PublicKeyCertificate)
        assert output.certificate == mapped_input.certificate
        assert output.certificate_id == mapped_input.certificateId
        assert output.public_key_id == mapped_input.publicKeyId
        assert output.valid_from == mapped_input.validFrom
        assert output.valid_to == mapped_input.validTo
        assert output.usage == ["ksef_token_encryption"]

    def test_map_public_key_certificate_ignores_future_response_fields(
        self, public_key_cert: BaseFactory[spec.PublicKeyCertificate]
    ):
        payload = public_key_cert.build().model_dump(mode="json")
        payload["futureField"] = "ignored"

        parsed = spec.PublicKeyCertificate.model_validate(payload)
        output = from_spec(parsed)

        assert isinstance(output, PublicKeyCertificate)
        assert output.public_key_id == parsed.publicKeyId

    def test_map_public_key_certificate_multiple_usages(
        self, public_key_cert: BaseFactory[spec.PublicKeyCertificate]
    ):
        mapped_input = public_key_cert.build(
            usage=[
                spec.PublicKeyCertificateUsage.KsefTokenEncryption,
                spec.PublicKeyCertificateUsage.SymmetricKeyEncryption,
            ]
        )
        output = from_spec(mapped_input)

        assert isinstance(output, PublicKeyCertificate)
        assert len(output.usage) == 2
        assert output.usage[0] == "ksef_token_encryption"
        assert output.usage[1] == "symmetric_key_encryption"

    def test_map_public_key_certificate_empty_usage(
        self, public_key_cert: BaseFactory[spec.PublicKeyCertificate]
    ):
        mapped_input = public_key_cert.build(usage=[])
        output = from_spec(mapped_input)

        assert isinstance(output, PublicKeyCertificate)
        assert output.usage == []


class TestEncryptionRequestMapper:
    def test_to_spec_usage_ksef_token_encryption(self):
        assert (
            to_spec("ksef_token_encryption")
            == spec.PublicKeyCertificateUsage.KsefTokenEncryption
        )

    def test_to_spec_usage_symmetric_key_encryption(self):
        assert (
            to_spec("symmetric_key_encryption")
            == spec.PublicKeyCertificateUsage.SymmetricKeyEncryption
        )

    def test_to_spec_unknown_string_raises(self):
        import pytest

        with pytest.raises(NotImplementedError, match="No mapper for string value"):
            _ = to_spec("unknown_usage")
