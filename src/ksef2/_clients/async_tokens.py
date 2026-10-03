"""Async KSeF token branch client."""

from collections.abc import AsyncGenerator, AsyncIterator, Coroutine
from typing import final

from typing_extensions import deprecated

from ksef2._clients._async_pager import AsyncPager
from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.polling import async_poll_until
from ksef2._domain.models.pagination import TokenListParams
from ksef2._domain.models.tokens import (
    GenerateTokenRequest,
    GenerateTokenResponse,
    QueryTokensResponse,
    TokenInfo,
    TokenPermission,
    TokenStatusResponse,
)
from ksef2._endpoints.async_tokens import AsyncTokenEndpoints
from ksef2._infra.mappers.tokens import from_spec, to_spec


@final
class AsyncTokensClient:
    """Async high-level API for the KSeF token lifecycle.

    Catch ``KSeFException`` for SDK-classified failures raised by this branch,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(self, transport: AsyncMiddleware) -> None:
        """Create the client.

        Args:
            transport: Middleware chain used for requests to KSeF.
        """
        self._endpoints = AsyncTokenEndpoints(transport)

    async def wait_for_activation(
        self,
        *,
        reference_number: str,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> TokenStatusResponse:
        """Wait until a generated token becomes active or reaches a terminal state.

        Call this explicitly after persisting the one-time credential returned by
        :meth:`generate`. A polling failure does not contain or recover that secret.

        Args:
            reference_number: Reference returned by :meth:`generate`.
            timeout: Maximum number of seconds to wait for activation.
            poll_interval: Delay in seconds between status checks.

        Returns:
            The first status response that reports the token as active.

        Raises:
            KSeFApiError: If activation ends in a terminal failure state.
            KSeFTokenStatusTimeoutError: If polling exceeds ``timeout``.
            httpx.HTTPError: If a status request fails at the transport boundary.
        """
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
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFTokenStatusTimeoutError(
                reference_number=reference_number_local,
                timeout=timeout,
            ),
        )

    async def generate(
        self,
        *,
        permissions: list[TokenPermission],
        description: str,
    ) -> GenerateTokenResponse:
        """Create a token and immediately return its one-time credential.

        Args:
            permissions: Permissions to include in the generated token.
            description: Human-readable label shown in KSeF token listings.

        Returns:
            The token payload returned once by KSeF. Persist its secret before
            calling :meth:`wait_for_activation`.
        """
        request = GenerateTokenRequest(
            permissions=permissions,
            description=description,
        )
        body = to_spec(request)
        spec_resp = await self._endpoints.generate_token(body=body)
        return from_spec(spec_resp)

    async def _list_page(
        self,
        *,
        continuation_token: str | None = None,
        params: TokenListParams | None = None,
    ) -> QueryTokensResponse:
        parameters = params or TokenListParams()
        spec_resp = await self._endpoints.list_tokens(
            continuation_token=continuation_token, **parameters.to_query_params()
        )
        return from_spec(spec_resp)

    async def _list_pages(
        self, params: TokenListParams | None
    ) -> AsyncGenerator[QueryTokensResponse, None]:
        parameters = params or TokenListParams()
        response = await self._list_page(params=parameters)
        yield response

        while ct := response.continuation_token:
            response = await self._list_page(params=parameters, continuation_token=ct)
            yield response

    @deprecated(
        "`list_page()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    def list_page(
        self,
        *,
        continuation_token: str | None = None,
        params: TokenListParams | None = None,
    ) -> Coroutine[None, None, QueryTokensResponse]:
        """Deprecated: fetch one page of tokens using optional filters and continuation state.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list()`` instead; ``first_page()`` fetches one page.

        Args:
            continuation_token: Token identifying the next page to fetch.
            params: Optional filters and page size for the request.

        Returns:
            A single page of token results.
        """
        return self._list_page(continuation_token=continuation_token, params=params)

    @deprecated(
        "`list_all()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list()` instead."
    )
    async def list_all(
        self, *, params: TokenListParams | None = None
    ) -> AsyncIterator[QueryTokensResponse]:
        """Deprecated: iterate through all token pages until KSeF stops returning a continuation token.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list().pages()`` instead.

        Args:
            params: Optional filters and page size applied to every request.

        Yields:
            Each page returned by the token listing endpoint.
        """
        async for page in self._list_pages(params):
            yield page

    async def status(
        self,
        *,
        reference_number: str,
    ) -> TokenStatusResponse:
        """Return the current status of a token.

        Args:
            reference_number: Reference number of the token.

        Returns:
            The token's current lifecycle status.
        """
        spec_resp = await self._endpoints.token_status(
            reference_number=reference_number
        )
        return from_spec(spec_resp)

    async def revoke(
        self,
        *,
        reference_number: str,
    ) -> None:
        """Revoke a token.

        Args:
            reference_number: Reference number of the token to revoke.
        """
        await self._endpoints.revoke_token(reference_number=reference_number)

    def list(self, *, params: TokenListParams | None = None) -> AsyncPager[TokenInfo]:
        """List the tokens of the authenticated context.

        Nothing is requested until the result is consumed. Iterate it for every
        token, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            params: Optional filters and page size applied to every request.

        Returns:
            A paging object over the tokens matching ``params``.

        Example:
            ```python
            async for token in auth.tokens.list():
                print(token.reference_number, token.status)
            ```
        """

        async def _pages() -> AsyncGenerator[list[TokenInfo], None]:
            async for page in self._list_pages(params):
                yield page.tokens

        return AsyncPager(_pages)
