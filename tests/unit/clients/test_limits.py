from polyfactory import BaseFactory

from ksef2.clients.limits import LimitsClient
from ksef2.core.routes import LimitRoutes
from ksef2.domain.models.limits import ApiRateLimits, ContextLimits, SubjectLimits
from ksef2.infra.mappers.limits import to_spec
from ksef2.infra.schema.api import spec
from tests.unit.fakes.transport import FakeTransport


class TestLimitsClient:
    def test_get_context_limits(
        self,
        limits_client: LimitsClient,
        fake_transport: FakeTransport,
        limit_context_resp: BaseFactory[spec.EffectiveContextLimits],
    ) -> None:
        response = limit_context_resp.build()
        fake_transport.enqueue(response.model_dump(mode="json", by_alias=True))

        result = limits_client.get_context_limits()

        assert isinstance(result, ContextLimits)
        assert fake_transport.calls[0].method == "GET"
        assert fake_transport.calls[0].path == LimitRoutes.GET_CONTEXT_LIMITS

    def test_get_subject_limits(
        self,
        limits_client: LimitsClient,
        fake_transport: FakeTransport,
        limit_subject_resp: BaseFactory[spec.EffectiveSubjectLimits],
    ) -> None:
        response = limit_subject_resp.build()
        fake_transport.enqueue(response.model_dump(mode="json", by_alias=True))

        result = limits_client.get_subject_limits()

        assert isinstance(result, SubjectLimits)
        assert fake_transport.calls[0].method == "GET"
        assert fake_transport.calls[0].path == LimitRoutes.GET_SUBJECT_LIMITS

    def test_get_api_rate_limits(
        self,
        limits_client: LimitsClient,
        fake_transport: FakeTransport,
        limit_rate_resp: BaseFactory[spec.EffectiveApiRateLimits],
    ) -> None:
        response = limit_rate_resp.build()
        fake_transport.enqueue(response.model_dump(mode="json", by_alias=True))

        result = limits_client.get_api_rate_limits()

        assert isinstance(result, ApiRateLimits)
        assert fake_transport.calls[0].method == "GET"
        assert fake_transport.calls[0].path == LimitRoutes.GET_API_RATE_LIMITS

    def test_set_session_limits(
        self,
        limits_client: LimitsClient,
        fake_transport: FakeTransport,
        domain_limit_context: BaseFactory[ContextLimits],
    ) -> None:
        limits = domain_limit_context.build()
        fake_transport.enqueue({})

        limits_client.set_session_limits(limits=limits)

        assert fake_transport.calls[0].method == "POST"
        assert fake_transport.calls[0].path == LimitRoutes.SET_SESSION_LIMITS
        assert fake_transport.calls[0].json == to_spec(limits).model_dump(mode="json")

    def test_set_subject_limits(
        self,
        limits_client: LimitsClient,
        fake_transport: FakeTransport,
        domain_limit_subject: BaseFactory[SubjectLimits],
    ) -> None:
        limits = domain_limit_subject.build()
        fake_transport.enqueue({})

        limits_client.set_subject_limits(limits=limits)

        assert fake_transport.calls[0].method == "POST"
        assert fake_transport.calls[0].path == LimitRoutes.SET_SUBJECT_LIMITS
        assert fake_transport.calls[0].json == to_spec(limits).model_dump(mode="json")

    def test_set_api_rate_limits(
        self,
        limits_client: LimitsClient,
        fake_transport: FakeTransport,
        domain_limit_rate: BaseFactory[ApiRateLimits],
    ) -> None:
        limits = domain_limit_rate.build()
        fake_transport.enqueue({})

        limits_client.set_api_rate_limits(limits=limits)

        assert fake_transport.calls[0].method == "POST"
        assert fake_transport.calls[0].path == LimitRoutes.SET_API_RATE_LIMITS
        assert fake_transport.calls[0].json == to_spec(limits).model_dump(mode="json")

    def test_reset_endpoints(
        self,
        limits_client: LimitsClient,
        fake_transport: FakeTransport,
    ) -> None:
        fake_transport.enqueue({})
        fake_transport.enqueue({})
        fake_transport.enqueue({})
        fake_transport.enqueue({})

        limits_client.reset_session_limits()
        limits_client.reset_subject_limits()
        limits_client.reset_api_rate_limits()
        limits_client.set_production_rate_limits()

        assert [call.method for call in fake_transport.calls] == [
            "DELETE",
            "DELETE",
            "DELETE",
            "POST",
        ]
        assert [call.path for call in fake_transport.calls] == [
            LimitRoutes.RESET_SESSION_LIMITS,
            LimitRoutes.RESET_SUBJECT_LIMITS,
            LimitRoutes.RESET_API_RATE_LIMITS,
            LimitRoutes.SET_PRODUCTION_RATE_LIMITS,
        ]
