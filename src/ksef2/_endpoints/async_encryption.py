"""Async encryption endpoints for public key certificates."""

from typing import final

from ksef2._core import routes
from ksef2._endpoints.async_base import AsyncBaseEndpoints
from ksef2._infra.schema.api import spec


@final
class AsyncEncryptionEndpoints(AsyncBaseEndpoints):
    """Raw endpoints for KSeF public-key certificates."""

    async def fetch_public_certificates(self) -> list[spec.PublicKeyCertificate]:
        """Fetch public certificates used for token and session-key encryption.

        Returns:
            The parsed KSeF response (``list[spec.PublicKeyCertificate]``).
        """
        return self._parse_list(
            await self._transport.get(routes.EncryptionRoutes.PUBLIC_KEY_CERTIFICATES),
            spec.PublicKeyCertificate,
        )
