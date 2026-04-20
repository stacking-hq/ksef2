from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.encryption import CertUsage, PublicKeyCertificate
from ksef2.endpoints.async_encryption import AsyncEncryptionEndpoints
from ksef2.infra.mappers.encryption import from_spec, to_spec


@final
class AsyncEncryptionClient:
    """Async access to public encryption certificates published by KSeF."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._endpoints = AsyncEncryptionEndpoints(transport)

    async def get_certificates(
        self,
        *,
        usage: list[CertUsage] | None = None,
    ) -> list[PublicKeyCertificate]:
        certificates = [
            from_spec(cert)
            for cert in await self._endpoints.fetch_public_certificates()
        ]

        if usage is None:
            return certificates

        requested = {to_spec(value) for value in usage}
        return [
            cert
            for cert in certificates
            if any(to_spec(cert_usage) in requested for cert_usage in cert.usage)
        ]
