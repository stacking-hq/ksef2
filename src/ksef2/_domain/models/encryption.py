"""Domain models for public encryption certificates exposed by KSeF."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from ksef2._domain.models.base import KSeFBaseModel

type CertUsageValue = Literal["ksef_token_encryption", "symmetric_key_encryption"]

type CertUsage = CertUsageValue


class CertUsageEnum(StrEnum):
    """Runtime enum for KSeF public-certificate usages."""

    KSEF_TOKEN_ENCRYPTION = "ksef_token_encryption"
    SYMMETRIC_KEY_ENCRYPTION = "symmetric_key_encryption"


def normalize_cert_usage(value: CertUsage | CertUsageEnum | str) -> CertUsage:
    """Normalize public certificate usage values to SDK literals.

    Raises:
        ValueError: If ``value`` is not a supported certificate usage.
    """
    if isinstance(value, CertUsageEnum):
        return value.value

    if value in CertUsageEnum._value2member_map_:
        return value  # pyright: ignore[reportReturnType]

    raise ValueError(
        f"Invalid certificate usage: {value}. Valid certificate usages are: "
        f"{', '.join(member.value for member in CertUsageEnum)}"
    )


class PublicKeyCertificate(KSeFBaseModel):
    """Public certificate that can encrypt tokens or session keys for KSeF."""

    certificate: str
    """DER-encoded X.509 certificate, Base64-encoded."""
    certificate_id: str | None = None
    """Identifier of the certificate; ``None`` if not reported."""
    public_key_id: str | None = None
    """Identifier to pass as ``public_key_id`` when encrypting with this key; ``None`` if not reported."""
    valid_from: datetime
    """Start of the certificate validity period."""
    valid_to: datetime
    """End of the certificate validity period."""
    usage: list[CertUsage]
    """What the key may be used for, such as token or session-key encryption."""
