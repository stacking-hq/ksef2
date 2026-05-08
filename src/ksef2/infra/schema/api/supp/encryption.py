from pydantic import AwareDatetime, ConfigDict

from ksef2.infra.schema.api.spec.models import PublicKeyCertificateUsage
from ksef2.infra.schema.api.supp.base import BaseSupp


class PublicKeyCertificate(BaseSupp):
    """Supplementary response with raw Base64 string instead of Base64Str decoding."""

    model_config = ConfigDict(extra="ignore")

    certificate: str
    certificateId: str | None = None
    publicKeyId: str | None = None
    validFrom: AwareDatetime
    validTo: AwareDatetime
    usage: list[PublicKeyCertificateUsage]
