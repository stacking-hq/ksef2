from collections.abc import AsyncIterator
from typing import final

from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.polling import async_poll_until
from ksef2.domain.models.pagination import TokenListParams
from ksef2.domain.models.tokens import (
    GenerateTokenRequest,
    GenerateTokenResponse,
    QueryTokensResponse,
    TokenPermission,
    TokenStatusResponse,
)
from ksef2.endpoints.async_tokens import AsyncTokenEndpoints
from ksef2.infra.mappers.tokens import from_spec, to_spec


@final
class AsyncTokensClient:
    """Async high-level API for the KSeF token lifecycle."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._endpoints = AsyncTokenEndpoints(transport)

    async def _poll_until_active(
        self,
        *,
        reference_number: str,
        poll_interval: float,
        max_attempts: int,
    ) -> TokenStatusResponse:
        """Poll token status until it becomes active or reaches a terminal state."""
        reference_number_local = reference_number

        async def _poll() -> TokenStatusResponse:
            result = await self.status(reference_number=reference_number_local)
            if result.status in ("failed", "revoked"):
                raise exceptions.KSeFApiError(
                    0,
                    exceptions.ExceptionCode.UNKNOWN_ERROR,
                    f"Token activation failed: status={result.status}",
                )
            return result

        return await async_poll_until(
            operation=_poll,
            retry_predicate=lambda result: result.status != "active",
            poll_interval=poll_interval,
            max_attempts=max_attempts,
            timeout_error_factory=lambda: exceptions.KSeFTokenStatusTimeoutError(
                reference_number=reference_number_local,
                attempts=max_attempts,
                poll_interval=poll_interval,
            ),
        )

    async def generate(
        self,
        *,
        permissions: list[TokenPermission],
        description: str,
        poll_interval: float = 1.0,
        max_poll_attempts: int = 60,
    ) -> GenerateTokenResponse:
        """Create a token and wait until KSeF marks it as active.

        Args:
            permissions: Permissions to include in the generated token.
            description: Human-readable label shown in KSeF token listings.
            poll_interval: Delay in seconds between status checks.
            max_poll_attempts: Maximum number of status requests before timing out.

        Returns:
            The token payload returned immediately after creation.

        Raises:
            KSeFApiError: If activation ends in a terminal failure state or polling
                exceeds ``max_poll_attempts``.
            KSeFTokenStatusTimeoutError: If polling exceeds
                ``max_poll_attempts``.
        """
        request = GenerateTokenRequest(
            permissions=permissions,
            description=description,
        )
        body = to_spec(request)
        spec_resp = await self._endpoints.generate_token(body=body)
        result = from_spec(spec_resp)

        _ = await self._poll_until_active(
            reference_number=result.reference_number,
            poll_interval=poll_interval,
            max_attempts=max_poll_attempts,
        )
        return result

    async def list_page(
        self,
        *,
        continuation_token: str | None = None,
        params: TokenListParams | None = None,
    ) -> QueryTokensResponse:
        """Fetch one page of tokens using optional filters and continuation state.

        Args:
            continuation_token: Token identifying the next page to fetch.
            params: Optional filters and page size for the request.

        Returns:
            A single page of token results.
        """
        parameters = params or TokenListParams()
        spec_resp = await self._endpoints.list_tokens(
            continuation_token=continuation_token, **parameters.to_query_params()
        )
        return from_spec(spec_resp)

    async def list_all(
        self, *, params: TokenListParams | None = None
    ) -> AsyncIterator[QueryTokensResponse]:
        """Iterate through all token pages until KSeF stops returning a continuation token.

        Args:
            params: Optional filters and page size applied to every request.

        Yields:
            Each page returned by the token listing endpoint.
        """
        parameters = params or TokenListParams()
        response = await self.list_page(params=parameters)
        yield response

        while ct := response.continuation_token:
            response = await self.list_page(params=parameters, continuation_token=ct)
            yield response

    async def status(
        self,
        *,
        reference_number: str,
    ) -> TokenStatusResponse:
        """Return the current status of a token."""
        spec_resp = await self._endpoints.token_status(
            reference_number=reference_number
        )
        return from_spec(spec_resp)

    async def revoke(
        self,
        *,
        reference_number: str,
    ) -> None:
        """Revoke a token."""
        await self._endpoints.revoke_token(reference_number=reference_number)
