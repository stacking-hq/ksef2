import asyncio

from polyfactory import BaseFactory

from ksef2.clients.async_limits import AsyncLimitsClient
from ksef2.core.routes import LimitRoutes
from ksef2.domain.models.limits import ApiRateLimits, ContextLimits, SubjectLimits
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import AsyncFakeTransport


class TestAsyncLimitsClient:
    def test_get_context_limits(
        self,
        async_fake_transport: AsyncFakeTransport,
        limit_context_resp: BaseFactory[spec.EffectiveContextLimits],
    ) -> None:
        client = AsyncLimitsClient(async_fake_transport)
        response = limit_context_resp.build()
        async_fake_transport.enqueue(response.model_dump(mode="json"))

        result = asyncio.run(client.get_context_limits())

        assert isinstance(result, ContextLimits)
        assert async_fake_transport.calls[0].path == LimitRoutes.GET_CONTEXT_LIMITS

    def test_get_subject_limits(
        self,
        async_fake_transport: AsyncFakeTransport,
        limit_subject_resp: BaseFactory[spec.EffectiveSubjectLimits],
    ) -> None:
        client = AsyncLimitsClient(async_fake_transport)
        response = limit_subject_resp.build()
        async_fake_transport.enqueue(response.model_dump(mode="json"))

        result = asyncio.run(client.get_subject_limits())

        assert isinstance(result, SubjectLimits)

    def test_get_api_rate_limits(
        self,
        async_fake_transport: AsyncFakeTransport,
        limit_rate_resp: BaseFactory[spec.EffectiveApiRateLimits],
    ) -> None:
        client = AsyncLimitsClient(async_fake_transport)
        response = limit_rate_resp.build()
        async_fake_transport.enqueue(response.model_dump(mode="json"))

        result = asyncio.run(client.get_api_rate_limits())

        assert isinstance(result, ApiRateLimits)
