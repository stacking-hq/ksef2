"""Supplementary models for certificate operations.

These models shadow generated schema models that use Base64Str fields so the
SDK can pass already-base64-encoded request data without double decoding.
"""

from datetime import datetime

from ksef2._infra.schema.api.spec.models import KsefCertificateType
from ksef2._infra.schema.api.supp.base import BaseSupp


class EnrollCertificateRequest(BaseSupp):
    """Request to start certificate enrollment."""

    certificateName: str
    certificateType: KsefCertificateType
    csr: str
    validFrom: datetime | None = None
