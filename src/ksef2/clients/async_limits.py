"""Async limits branch client."""

from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.limits import ApiRateLimits, ContextLimits, SubjectLimits
from ksef2.endpoints.async_limits import AsyncLimitEndpoints
from ksef2.infra.mappers.limits import from_spec, to_spec


@final
class AsyncLimitsClient:
    """Async read and override KSeF context, subject, and API rate limits.

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
        self._endpoints = AsyncLimitEndpoints(transport)

    async def get_context_limits(self) -> ContextLimits:
        """Return the effective limits for online and batch sessions."""
        return from_spec(await self._endpoints.get_context_limits())

    async def get_subject_limits(self) -> SubjectLimits:
        """Return the effective limits for certificate enrollments and issuance."""
        return from_spec(await self._endpoints.get_subject_limits())

    async def get_api_rate_limits(self) -> ApiRateLimits:
        """Return the effective per-endpoint API rate limits."""
        return from_spec(await self._endpoints.get_api_rate_limits())

    async def set_session_limits(self, *, limits: ContextLimits) -> None:
        """Override session limits for the current subject."""
        await self._endpoints.set_session_limits(body=to_spec(limits))

    async def reset_session_limits(self) -> None:
        """Reset session limits to their default values."""
        await self._endpoints.reset_session_limits()

    async def set_subject_limits(self, *, limits: SubjectLimits) -> None:
        """Override subject-level certificate and enrollment limits."""
        await self._endpoints.set_subject_limits(body=to_spec(limits))

    async def reset_subject_limits(self) -> None:
        """Reset subject-level limits to their default values."""
        await self._endpoints.reset_subject_limits()

    async def set_api_rate_limits(self, *, limits: ApiRateLimits) -> None:
        """Override API rate limits for the current subject."""
        await self._endpoints.set_api_rate_limits(body=to_spec(limits))

    async def reset_api_rate_limits(self) -> None:
        """Reset API rate limits to their default values."""
        await self._endpoints.reset_api_rate_limits()

    async def set_production_rate_limits(self) -> None:
        """Copy production rate-limit defaults into the current environment."""
        await self._endpoints.set_production_rate_limits()
