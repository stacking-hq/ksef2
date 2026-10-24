"""Async KSeF token branch client."""

import builtins
from collections.abc import AsyncGenerator, AsyncIterator, Coroutine
from typing import cast, final, override

from typing_extensions import deprecated

from ksef2._core.polling import async_poll_until as _until
from ksef2._clients._async_handles import AsyncOperationHandle, not_after_resume
from ksef2._clients._async_pager import AsyncPager
from ksef2._clients._pagination_cursor import ContinuationCursor
from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.pagination import Page, TokenListParams
from ksef2._domain.models.tokens import (
    GeneratedTokenResumeState,
    GenerateTokenRequest,
    GenerateTokenResponse,
    QueryTokensResponse,
    TokenInfo,
    TokenPermission,
    TokenStatusResponse,
)
from ksef2._endpoints.async_tokens import AsyncTokenEndpoints
from ksef2._infra.mappers.tokens import from_spec, to_spec

async_poll_until = _until


@final
class AsyncGeneratedToken(
    AsyncOperationHandle[TokenStatusResponse, TokenStatusResponse]
):
    """Handle to a token KSeF is still activating.

    Returned by ``auth.tokens.generate()``. The one-time token is readable
    immediately, so persist it before calling ``wait()``: a polling failure does
    not contain or recover that secret. The handle exposes every field of the
    generation response, for example ``token`` and ``reference_number``, and never
    includes the token in its ``repr``.

    ``resume_state()`` saves what is needed to build the handle again after a
    restart with ``auth.tokens.generation(state)``. That state holds the
    reference number and never the one-time token, so a resumed handle has no
    ``token``.

    Raises:
        KSeFApiError: If KSeF returns an API error response.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        KSeFTransportError: If the HTTP request fails to produce a usable response.
    """

    def __init__(
        self,
        client: "AsyncTokensClient",
        reference_number: str,
        response: GenerateTokenResponse | None = None,
    ) -> None:
        """Create the handle.

        Args:
            client: Tokens client used to poll the token's status.
            reference_number: KSeF reference number of the token.
            response: Generation response returned by KSeF, carrying the one-time token. ``None`` for a handle rebuilt from resume state, which never held the token.
        """
        super().__init__(reference_number)
        self._client = client
        self._response = response

    def __getattr__(self, name: str) -> object:
        # A property that raises AttributeError falls through to here, so "response" is
        # answered here too and keeps its resume message.
        if name in GenerateTokenResponse.model_fields or name == "response":
            if self._response is None:
                raise not_after_resume(type(self).__name__, name)
            return cast(object, getattr(self._response, name))
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

    def _generation_response(self, name: str) -> GenerateTokenResponse:
        """Return the generation response, refusing to invent one after a resume."""
        if self._response is None:
            raise not_after_resume(type(self).__name__, name)
        return self._response

    def resume_state(self) -> GeneratedTokenResumeState:
        """Return the state needed to resume this token after a restart.

        Persist it with ``to_json()`` and pass it to
        ``auth.tokens.generation(state)`` later. It carries only the
        reference number: the one-time token is not part of it and cannot be
        recovered this way.

        Returns:
            The token's reference number as saveable state.
        """
        return GeneratedTokenResumeState(reference_number=self.reference_number)

    @property
    def token(self) -> str:
        """Get the one-time token value.

        Returns:
            The secret KSeF returned once at generation; store it securely.

        Raises:
            AttributeError: If the handle was rebuilt from resume state, which never holds the token.
        """
        return self._generation_response("token").token

    @property
    def response(self) -> GenerateTokenResponse:
        """Get the plain generation response.

        Returns:
            The data model KSeF returned when the token was generated.

        Raises:
            AttributeError: If the handle was rebuilt from resume state, which never held a generation response.
        """
        return self._generation_response("response")

    def to_sensitive_dict(self) -> dict[str, str]:
        """Export the one-time token for deliberately protected persistence.

        Returns:
            A dictionary with the reference number and the plain token.

        Raises:
            AttributeError: If the handle was rebuilt from resume state, which never holds the token.
        """
        return self._generation_response("token").to_sensitive_dict()

    @override
    async def get_status(self) -> TokenStatusResponse:
        """Fetch the token's current status without waiting.

        Returns:
            The token's current lifecycle status.
        """
        return await self._client.get_status(reference_number=self.reference_number)

    @override
    def _is_pending(self, status: TokenStatusResponse) -> bool:
        return status.status != "active"

    @override
    def _check_status(self, status: TokenStatusResponse) -> None:
        if status.status in ("failed", "revoked"):
            raise exceptions.KSeFTokenActivationFailedError(
                self.reference_number, status.status
            )

    @override
    def _timeout_error(self, timeout: float) -> BaseException:
        return exceptions.KSeFTokenStatusTimeoutError(
            reference_number=self.reference_number,
            timeout=timeout,
        )

    @override
    async def _finish(self, status: TokenStatusResponse) -> TokenStatusResponse:
        return status

    async def wait(
        self,
        *,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> TokenStatusResponse:
        """Poll until the token becomes active or reaches a terminal state.

        Args:
            timeout: Maximum number of seconds to wait for activation.
            poll_interval: Delay in seconds between status checks.

        Returns:
            The first status response that reports the token as active.

        Raises:
            KSeFTokenActivationFailedError: If activation ends in a terminal failure state.
            KSeFTokenStatusTimeoutError: If polling exceeds ``timeout``.
        """
        return await self._wait(timeout, poll_interval)


@final
class AsyncTokensClient:
    """Async high-level API for the KSeF token lifecycle.

    Catch ``KSeFException`` for SDK-classified failures raised by this branch,
    including ``KSeFTransportError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        KSeFTransportError: If the HTTP request fails to produce a usable response.
    """

    def __init__(self, transport: AsyncMiddleware) -> None:
        """Create the client.

        Args:
            transport: Middleware chain used for requests to KSeF.
        """
        self._endpoints = AsyncTokenEndpoints(transport)

    async def _wait_for_activation(
        self, reference_number: str, timeout: float, poll_interval: float
    ) -> TokenStatusResponse:
        handle = AsyncGeneratedToken(
            self,
            reference_number,
            GenerateTokenResponse(reference_number=reference_number, token=""),
        )
        return await handle.wait(timeout=timeout, poll_interval=poll_interval)

    @deprecated(
        "`wait_for_activation()` is deprecated and will be removed no earlier than ksef2 2.0.0; "
        "use `generate(...).wait()` instead."
    )
    def wait_for_activation(
        self,
        *,
        reference_number: str,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> Coroutine[None, None, TokenStatusResponse]:
        """Deprecated: wait until a generated token becomes active or reaches a terminal state.

        Deprecated:
            May be removed no earlier than ksef2 2.0.0. Call ``wait()`` on the handle returned by ``generate()`` instead.

        Args:
            reference_number: Reference returned by :meth:`generate`.
            timeout: Maximum number of seconds to wait for activation.
            poll_interval: Delay in seconds between status checks.

        Returns:
            The first status response that reports the token as active.

        Raises:
            KSeFTokenActivationFailedError: If activation ends in a terminal failure state.
            KSeFTokenStatusTimeoutError: If polling exceeds ``timeout``.
            KSeFTransportError: If a status request fails to produce a usable response.
        """
        return self._wait_for_activation(reference_number, timeout, poll_interval)

    async def generate(
        self,
        *,
        permissions: builtins.list[TokenPermission],
        description: str,
    ) -> AsyncGeneratedToken:
        """Create a token and return a handle exposing its one-time credential.

        Args:
            permissions: Permissions to include in the generated token.
            description: Human-readable label shown in KSeF token listings.

        Returns:
            A handle whose ``token`` is the one-time secret KSeF returns only once;
            persist it before calling the handle's ``wait()`` for activation.

        Example:
            ```python
            token = await auth.tokens.generate(
                permissions=["invoice_read"], description="reporting"
            )
            secret = token.token  # store it now, KSeF will not show it again
            await token.wait()
            ```
        """
        request = GenerateTokenRequest(
            permissions=permissions,
            description=description,
        )
        body = to_spec(request)
        spec_resp = await self._endpoints.generate_token(body=body)
        response = from_spec(spec_resp)
        return AsyncGeneratedToken(self, response.reference_number, response)

    def generation(self, state: GeneratedTokenResumeState | str) -> AsyncGeneratedToken:
        """Rebuild the handle of a token generated earlier.

        Use it after a restart to keep waiting for activation. No request is made
        until the handle is used.

        Args:
            state: State saved with ``resume_state().to_json()``, or the object itself.

        Returns:
            A handle that polls the token's status. It has no ``token``: the one-time secret is never part of the saved state.

        Raises:
            ValidationError: If ``state`` is JSON that is not a saved token state.

        Example:
            ```python
            handle = auth.tokens.generation(saved_state)
            status = await handle.wait()
            ```
        """
        restored = (
            state
            if isinstance(state, GeneratedTokenResumeState)
            else GeneratedTokenResumeState.from_json(state)
        )
        return AsyncGeneratedToken(self, restored.reference_number)

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

    def list_page(
        self,
        *,
        continuation_token: str | None = None,
        params: TokenListParams | None = None,
    ) -> Coroutine[None, None, QueryTokensResponse]:
        """Fetch one page of tokens using optional filters and continuation state.

        This is the low-level single-request form. ``list().page()`` wraps it with
        cursors and needs no continuation token of your own; ``list_all()`` remains
        the deprecated iterator.

        Args:
            continuation_token: Token identifying the next page to fetch.
            params: Optional filters and page size for the request.

        Returns:
            A single page of token results.
        """
        return self._list_page(continuation_token=continuation_token, params=params)

    @deprecated(
        "`list_all()` is deprecated and will be removed no earlier than ksef2 2.0.0; "
        "use `list()` instead."
    )
    async def list_all(
        self, *, params: TokenListParams | None = None
    ) -> AsyncIterator[QueryTokensResponse]:
        """Deprecated: iterate through all token pages until KSeF stops returning a continuation token.

        Deprecated:
            May be removed no earlier than ksef2 2.0.0. Use ``list().pages()`` instead.

        Args:
            params: Optional filters and page size applied to every request.

        Yields:
            Each page returned by the token listing endpoint.
        """
        async for page in self._list_pages(params):
            yield page

    async def get_status(
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

    @deprecated(
        "`status()` is deprecated and will be removed no earlier than ksef2 2.0.0; "
        "use `get_status()` instead."
    )
    def status(
        self,
        *,
        reference_number: str,
    ) -> Coroutine[None, None, TokenStatusResponse]:
        """Deprecated: return the current status of a token.

        Deprecated:
            May be removed no earlier than ksef2 2.0.0. Use ``get_status()`` instead.

        Args:
            reference_number: Reference number of the token.

        Returns:
            The token's current lifecycle status.
        """
        return self.get_status(reference_number=reference_number)

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
        token, call ``pages()`` for page-sized lists, ``first_page()`` for one
        request only, or ``page()`` to walk it with a resumable cursor.

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

        async def _fetch_page(cursor: str | None) -> Page[TokenInfo]:
            continuation_token = (
                None
                if cursor is None
                else ContinuationCursor.decode(
                    cursor, operation="tokens.list"
                ).continuation_token
            )
            response = await self._list_page(
                params=params, continuation_token=continuation_token
            )
            return Page[TokenInfo](
                items=response.tokens,
                next_cursor=ContinuationCursor.encode_next(
                    operation="tokens.list",
                    continuation_token=response.continuation_token,
                ),
            )

        return AsyncPager(fetch_page=_fetch_page)
