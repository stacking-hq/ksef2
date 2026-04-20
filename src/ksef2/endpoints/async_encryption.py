"""Async encryption endpoints for public key certificates."""

from typing import final

from ksef2.core import routes
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.infra.schema.api import spec


@final
class AsyncEncryptionEndpoints(AsyncBaseEndpoints):
    async def fetch_public_certificates(self) -> list[spec.PublicKeyCertificate]:
        return self._parse_list(
            await self._transport.get(routes.EncryptionRoutes.PUBLIC_KEY_CERTIFICATES),
            spec.PublicKeyCertificate,
        )
