"""Mappings from generated encryption schema models to domain models."""

from typing import assert_never

from ksef2.domain.models.encryption import (
    CertUsage,
    PublicKeyCertificate,
)
from ksef2.infra.schema.api import spec


def usage_from_spec(response: spec.PublicKeyCertificateUsage) -> CertUsage:
    """Convert a generated public certificate usage into its domain value."""
    match response:
        case spec.PublicKeyCertificateUsage.KsefTokenEncryption:
            return "ksef_token_encryption"
        case spec.PublicKeyCertificateUsage.SymmetricKeyEncryption:
            return "symmetric_key_encryption"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def from_spec(
    response: spec.PublicKeyCertificate,
) -> PublicKeyCertificate:
    """Convert a generated public key certificate into its domain model."""
    return PublicKeyCertificate(
        certificate=response.certificate,
        certificate_id=response.certificateId,
        public_key_id=response.publicKeyId,
        valid_from=response.validFrom,
        valid_to=response.validTo,
        usage=[usage_from_spec(usage) for usage in response.usage],
    )
