"""Async token endpoints for managing access tokens."""

from typing import NotRequired, TypedDict, Unpack, final

from pydantic import AwareDatetime, TypeAdapter

from ksef2._core import routes
from ksef2._domain.types import ListTokensQueryParams
from ksef2._endpoints.async_base import AsyncBaseEndpoints
from ksef2._infra.schema.api import spec


class _ListTokensRev2QueryParams(TypedDict):
    """Wire-format filters for the revision 2 token listing."""

    status: NotRequired[list[spec.TokenStatusFilterRev2] | None]
    description: NotRequired[str | None]
    authorIdentifier: NotRequired[str | None]
    authorIdentifierType: NotRequired[spec.TokenAuthorIdentifierTypeFilterRev2 | None]
    validFrom: NotRequired[AwareDatetime | None]
    validTo: NotRequired[AwareDatetime | None]
    pageSize: NotRequired[int | None]


_LIST_TOKENS_REV2_PARAMS = TypeAdapter(_ListTokensRev2QueryParams)
_LIST_TOKENS_PARAMS = TypeAdapter(ListTokensQueryParams)


@final
class AsyncTokenEndpoints(AsyncBaseEndpoints):
    """Raw token endpoints backed by generated schema models."""

    async def generate_token(
        self, body: spec.GenerateTokenRequest
    ) -> spec.GenerateTokenResponse:
        """Create a token using schema-native request and response models.

        Args:
            body: Request payload expected by the generated API schema.

        Returns:
            The token creation response returned by KSeF.
        """
        return self._parse(
            await self._transport.post(
                path=routes.TokenRoutes.GENERATE_TOKEN,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.GenerateTokenResponse,
        )

    async def generate_token_rev2(
        self, body: spec.GenerateTokenRequestRev2
    ) -> spec.GenerateTokenResponseRev2:
        """Create a revision 2 token with optional validity dates.

        Args:
            body: Request payload expected by the generated API schema.

        Returns:
            The token creation response returned by KSeF.
        """
        return self._parse(
            await self._transport.post(
                path=routes.TokenRoutes.GENERATE_TOKEN_REV2,
                json=body.model_dump(mode="json", by_alias=True, exclude_none=True),
            ),
            spec.GenerateTokenResponseRev2,
        )

    async def list_tokens(
        self,
        continuation_token: str | None = None,
        **params: Unpack[ListTokensQueryParams],
    ) -> spec.QueryTokensResponse:
        """Fetch one page of tokens.

        Args:
            continuation_token: Pagination token sent in the
                ``x-continuation-token`` header to request the next page.
            **params: Optional query parameters supported by ``GET /tokens``.

        Returns:
            One page of token results from the API.
        """
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )

        return self._parse(
            await self._transport.get(
                path=routes.TokenRoutes.LIST_TOKENS,
                params=self.build_params(params, _LIST_TOKENS_PARAMS),
                headers=headers,
            ),
            spec.QueryTokensResponse,
        )

    async def list_tokens_rev2(
        self,
        continuation_token: str | None = None,
        **params: Unpack[_ListTokensRev2QueryParams],
    ) -> spec.QueryTokensResponseRev2:
        """Fetch one page of tokens.

        Args:
            continuation_token: Pagination token sent in the
                ``x-continuation-token`` header to request the next page.
            **params: Optional query parameters supported by ``GET /tokens/rev2``.

        Returns:
            One page of token results from the API.
        """
        headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )

        return self._parse(
            await self._transport.get(
                path=routes.TokenRoutes.LIST_TOKENS_REV2,
                params=self.build_params(params, _LIST_TOKENS_REV2_PARAMS),
                headers=headers,
            ),
            spec.QueryTokensResponseRev2,
        )

    async def token_status(self, reference_number: str) -> spec.TokenStatusResponse:
        """Fetch the current activation status for a token reference.

        Args:
            reference_number: Reference number of the token.

        Returns:
            The parsed KSeF response (``spec.TokenStatusResponse``).
        """
        return self._parse(
            await self._transport.get(
                path=routes.TokenRoutes.TOKEN_STATUS.format(
                    referenceNumber=reference_number
                ),
            ),
            spec.TokenStatusResponse,
        )

    async def token_status_rev2(
        self, reference_number: str
    ) -> spec.TokenStatusResponseRev2:
        """Fetch revision 2 token status, validity dates, and approval state.

        Args:
            reference_number: Reference number of the token.

        Returns:
            The parsed KSeF response (``spec.TokenStatusResponseRev2``).
        """
        return self._parse(
            await self._transport.get(
                path=routes.TokenRoutes.TOKEN_STATUS_REV2.format(
                    referenceNumber=reference_number
                ),
            ),
            spec.TokenStatusResponseRev2,
        )

    async def approve_token(self, reference_number: str) -> None:
        """Approve a revision 2 token that is awaiting approval.

        Args:
            reference_number: Reference number of the token.
        """
        _ = await self._transport.post(
            path=routes.TokenRoutes.APPROVE_TOKEN.format(
                referenceNumber=reference_number
            ),
        )

    async def revoke_token(self, reference_number: str) -> None:
        """Revoke a token by its reference number.

        Args:
            reference_number: Reference number of the token.
        """
        _ = await self._transport.delete(
            path=routes.TokenRoutes.REVOKE_TOKEN.format(
                referenceNumber=reference_number
            ),
        )
