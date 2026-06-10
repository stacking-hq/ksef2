"""Async limits endpoints for managing KSeF limits."""

from typing import final

from ksef2.core import routes
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.infra.schema.api import spec


@final
class AsyncLimitEndpoints(AsyncBaseEndpoints):
    """Raw endpoints for reading and overriding effective limits."""

    async def get_context_limits(self) -> spec.EffectiveContextLimits:
        """Fetch the effective session limits."""
        return self._parse(
            await self._transport.get(
                path=routes.LimitRoutes.GET_CONTEXT_LIMITS,
            ),
            spec.EffectiveContextLimits,
        )

    async def get_subject_limits(self) -> spec.EffectiveSubjectLimits:
        """Fetch the effective subject-level limits."""
        return self._parse(
            await self._transport.get(
                path=routes.LimitRoutes.GET_SUBJECT_LIMITS,
            ),
            spec.EffectiveSubjectLimits,
        )

    async def get_api_rate_limits(self) -> spec.EffectiveApiRateLimits:
        """Fetch the effective API rate limits."""
        return self._parse(
            await self._transport.get(
                path=routes.LimitRoutes.GET_API_RATE_LIMITS,
            ),
            spec.EffectiveApiRateLimits,
        )

    async def set_session_limits(self, body: spec.SetSessionLimitsRequest) -> None:
        """Override session limits."""
        _ = await self._transport.post(
            path=routes.LimitRoutes.SET_SESSION_LIMITS,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def reset_session_limits(self) -> None:
        """Reset session limits to defaults."""
        _ = await self._transport.delete(
            path=routes.LimitRoutes.RESET_SESSION_LIMITS,
        )

    async def set_subject_limits(self, body: spec.SetSubjectLimitsRequest) -> None:
        """Override subject-level limits."""
        _ = await self._transport.post(
            path=routes.LimitRoutes.SET_SUBJECT_LIMITS,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def reset_subject_limits(self) -> None:
        """Reset subject-level limits to defaults."""
        _ = await self._transport.delete(
            path=routes.LimitRoutes.RESET_SUBJECT_LIMITS,
        )

    async def set_api_rate_limits(self, body: spec.SetRateLimitsRequest) -> None:
        """Override API rate limits."""
        _ = await self._transport.post(
            path=routes.LimitRoutes.SET_API_RATE_LIMITS,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def reset_api_rate_limits(self) -> None:
        """Reset API rate limits to defaults."""
        _ = await self._transport.delete(
            path=routes.LimitRoutes.RESET_API_RATE_LIMITS,
        )

    async def set_production_rate_limits(self) -> None:
        """Apply production defaults to the current environment."""
        _ = await self._transport.post(
            path=routes.LimitRoutes.SET_PRODUCTION_RATE_LIMITS,
        )
