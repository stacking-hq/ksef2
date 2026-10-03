"""Mappings from encryption domain values to generated API schema values."""

from typing import assert_never

from ksef2._domain.models.encryption import (
    CertUsage,
    CertUsageEnum,
    normalize_cert_usage,
)
from ksef2._infra.schema.api import spec


def to_spec(request: CertUsage | CertUsageEnum | str) -> spec.PublicKeyCertificateUsage:
    """Convert a public certificate usage into its generated schema counterpart."""
    try:
        normalized_usage = normalize_cert_usage(request)
    except ValueError as exc:
        raise NotImplementedError(f"No mapper for string value: {request!r}") from exc

    match normalized_usage:
        case "ksef_token_encryption":
            return spec.PublicKeyCertificateUsage.KsefTokenEncryption
        case "symmetric_key_encryption":
            return spec.PublicKeyCertificateUsage.SymmetricKeyEncryption
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)
