"""Domain models for public encryption certificates exposed by KSeF."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from ksef2.domain.models.base import KSeFBaseModel

type CertUsageValue = Literal["ksef_token_encryption", "symmetric_key_encryption"]

type CertUsage = CertUsageValue


class CertUsageEnum(StrEnum):
    KSEF_TOKEN_ENCRYPTION = "ksef_token_encryption"
    SYMMETRIC_KEY_ENCRYPTION = "symmetric_key_encryption"


def normalize_cert_usage(value: CertUsage | CertUsageEnum | str) -> CertUsage:
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
    certificate_id: str | None = None
    public_key_id: str | None = None
    valid_from: datetime
    valid_to: datetime
    usage: list[CertUsage]
