from collections.abc import AsyncIterator
from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.auth import AuthenticationSessionsResponse
from ksef2.endpoints.async_auth import AsyncAuthEndpoints
from ksef2.infra.mappers.auth import from_spec


@final
class AsyncSessionManagementClient:
    """Async manage authentication sessions opened through the auth API."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._auth_ep = AsyncAuthEndpoints(transport)

    async def query(
        self,
        *,
        page_size: int | None = None,
        continuation_token: str | None = None,
    ) -> AuthenticationSessionsResponse:
        return from_spec(
            await self._auth_ep.list_sessions(
                continuation_token=continuation_token,
                pageSize=page_size,
            )
        )

    async def all(
        self,
        *,
        page_size: int | None = None,
    ) -> AsyncIterator[AuthenticationSessionsResponse]:
        response = await self.query(page_size=page_size)
        yield response

        while ct := response.continuation_token:
            response = await self.query(page_size=page_size, continuation_token=ct)
            yield response

    async def terminate_current(self) -> None:
        await self._auth_ep.terminate_current_session()

    async def close(self, *, reference_number: str) -> None:
        await self._auth_ep.terminate_auth_session(reference_number=reference_number)
