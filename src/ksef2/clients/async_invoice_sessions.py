from collections.abc import AsyncIterator
from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.pagination import ListSessionsQuery
from ksef2.domain.models.session import (
    ListSessionsResponse,
    SessionStatus,
    SessionStatusEnum,
    normalize_session_status,
    normalize_session_type,
)
from ksef2.endpoints.async_session import AsyncSessionEndpoints
from ksef2.infra.mappers.sessions import from_spec


@final
class AsyncInvoiceSessionsClient:
    """Async browse historical online and batch invoice sessions."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._endpoints = AsyncSessionEndpoints(transport)

    async def query(
        self,
        *,
        session_type: str,
        continuation_token: str | None = None,
        params: ListSessionsQuery | None = None,
        statuses: list[SessionStatus | SessionStatusEnum] | None = None,
    ) -> ListSessionsResponse:
        parameters = params or ListSessionsQuery(
            session_type=normalize_session_type(session_type),
        )
        if statuses is not None:
            parameters = parameters.model_copy(
                update={
                    "statuses": [
                        normalize_session_status(status) for status in statuses
                    ]
                }
            )

        return from_spec(
            await self._endpoints.list_sessions(
                continuation_token=continuation_token,
                **parameters.to_query_params(),
            )
        )

    async def all(
        self,
        *,
        session_type: str,
        params: ListSessionsQuery | None = None,
    ) -> AsyncIterator[ListSessionsResponse]:
        parameters = params or ListSessionsQuery(
            session_type=normalize_session_type(session_type),
        )

        response = await self.query(
            session_type=session_type,
            params=parameters,
        )
        yield response

        while continuation_token := response.continuation_token:
            response = await self.query(
                session_type=session_type,
                continuation_token=continuation_token,
                params=parameters,
            )
            yield response
