"""Async session management endpoints."""

from typing import Unpack, final

from pydantic import TypeAdapter

from ksef2._core import routes
from ksef2._domain.types import ListSessionsQueryParams
from ksef2._endpoints.async_base import AsyncBaseEndpoints
from ksef2._infra.schema.api import spec
from ksef2._infra.schema.api.supp.batch import OpenBatchSessionRequest
from ksef2._infra.schema.api.supp.session import OpenOnlineSessionRequest

_LIST_SESSIONS_PARAMS = TypeAdapter(ListSessionsQueryParams)


@final
class AsyncSessionEndpoints(AsyncBaseEndpoints):
    """Raw async session endpoints backed by generated schema models."""

    async def open_online(
        self, body: OpenOnlineSessionRequest
    ) -> spec.OpenOnlineSessionResponse:
        """Open an online session using a schema-native request payload.

        Args:
            body: Request payload (``OpenOnlineSessionRequest``).

        Returns:
            The parsed KSeF response (``spec.OpenOnlineSessionResponse``).
        """
        return self._parse(
            await self._transport.post(
                path=routes.SessionRoutes.OPEN_ONLINE,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.OpenOnlineSessionResponse,
        )

    async def terminate_online(self, reference_number: str) -> None:
        """Terminate an online session.

        Args:
            reference_number: Reference number of the session.
        """
        _ = await self._transport.post(
            path=routes.SessionRoutes.TERMINATE_ONLINE.format(
                referenceNumber=reference_number
            ),
        )

    async def open_batch(
        self, body: OpenBatchSessionRequest
    ) -> spec.OpenBatchSessionResponse:
        """Open a batch session using a schema-native request payload.

        Args:
            body: Request payload (``OpenBatchSessionRequest``).

        Returns:
            The parsed KSeF response (``spec.OpenBatchSessionResponse``).
        """
        return self._parse(
            await self._transport.post(
                path=routes.SessionRoutes.OPEN_BATCH,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.OpenBatchSessionResponse,
        )

    async def close_batch(self, reference_number: str) -> None:
        """Close a batch session after all parts have been uploaded.

        Args:
            reference_number: Reference number of the session.
        """
        _ = await self._transport.post(
            path=routes.SessionRoutes.CLOSE_BATCH.format(
                referenceNumber=reference_number
            ),
        )

    async def get_session_upo(
        self,
        reference_number: str,
        upo_reference_number: str,
    ) -> bytes:
        """Download the session UPO document as raw bytes.

        Args:
            reference_number: Reference number of the session.
            upo_reference_number: Reference number of the UPO.

        Returns:
            The raw response body.
        """
        return (
            await self._transport.get(
                path=routes.SessionRoutes.GET_SESSION_UPO.format(
                    referenceNumber=reference_number,
                    upoReferenceNumber=upo_reference_number,
                ),
            )
        ).content

    async def list_sessions(
        self,
        continuation_token: str | None = None,
        **params: Unpack[ListSessionsQueryParams],
    ) -> spec.SessionsQueryResponse:
        """Fetch one page of sessions using query filters and continuation state.

        Args:
            continuation_token: Token from the previous page's response; ``None`` requests the first page.
            **params: Optional query parameters (``ListSessionsQueryParams``).

        Returns:
            The parsed KSeF response (``spec.SessionsQueryResponse``).
        """
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )

        return self._parse(
            await self._transport.get(
                path=routes.SessionRoutes.LIST_SESSIONS,
                params=self.build_params(params, _LIST_SESSIONS_PARAMS),
                headers=headers,
            ),
            spec.SessionsQueryResponse,
        )
