from datetime import datetime, timezone

from ksef2.domain.models import encryption
from ksef2.infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from tests.unit.helpers import VALID_BASE64, VALID_CERTIFICATE_ID, VALID_PUBLIC_KEY_ID


# --- factories for spec models ---


@register_fixture(name="public_key_cert")
class PublicKeyCertificateFactory(ModelFactory[spec.PublicKeyCertificate]):
    certificate: str = VALID_BASE64
    certificateId: str = VALID_CERTIFICATE_ID
    publicKeyId: str = VALID_PUBLIC_KEY_ID
    validFrom: datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)
    validTo: datetime = datetime(2027, 1, 1, tzinfo=timezone.utc)
    usage: list[spec.PublicKeyCertificateUsage] = [
        spec.PublicKeyCertificateUsage.KsefTokenEncryption
    ]


# --- factories for domain models ---


@register_fixture(name="domain_public_key_cert")
class DomainPublicKeyCertificateFactory(ModelFactory[encryption.PublicKeyCertificate]):
    certificate: str = VALID_BASE64
    certificate_id: str = VALID_CERTIFICATE_ID
    public_key_id: str = VALID_PUBLIC_KEY_ID
    valid_from: datetime = datetime(2025, 1, 1, tzinfo=timezone.utc)
    valid_to: datetime = datetime(2027, 1, 1, tzinfo=timezone.utc)
    usage: list[str] = ["ksef_token_encryption"]
