from typing import cast, Callable

import pytest

from polyfactory.factories import BaseFactory
from pydantic import BaseModel

from ksef2.core import exceptions
from ksef2.core.routes import LimitRoutes
from ksef2.endpoints.limits import LimitEndpoints
from tests.unit.fakes import transport

from ksef2.endpoints import limits
from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


@pytest.fixture
def req_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


@pytest.fixture
def resp_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


class TestLimitEndpoints:
    @pytest.fixture
    def limit_eps(
        self, fake_transport: transport.FakeTransport
    ) -> limits.LimitEndpoints:
        return limits.LimitEndpoints(fake_transport)

    @pytest.fixture
    def handled_limit_eps(
        self, fake_transport: transport.FakeTransport
    ) -> limits.LimitEndpoints:
        return limits.LimitEndpoints(KSeFExceptionMiddleware(fake_transport))

    @pytest.mark.parametrize(
        ["target_path", "method", "resp_factory"],
        [
            (
                LimitRoutes.GET_CONTEXT_LIMITS,
                LimitEndpoints.get_context_limits,
                "limit_context_resp",
            ),
            (
                LimitRoutes.GET_SUBJECT_LIMITS,
                LimitEndpoints.get_subject_limits,
                "limit_subject_resp",
            ),
            (
                LimitRoutes.GET_API_RATE_LIMITS,
                LimitEndpoints.get_api_rate_limits,
                "limit_rate_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_happy_path_get(
        self,
        limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[], BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        expected = resp_factory.build()
        expected_dump = expected.model_dump(mode="json")

        # Act
        fake_transport.enqueue(expected_dump)
        response = cast(BaseModel, getattr(limit_eps, method.__name__)())

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert target_path == call.path
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method", "req_factory"],
        [
            (
                LimitRoutes.SET_SESSION_LIMITS,
                LimitEndpoints.set_session_limits,
                "limit_set_session_req",
            ),
            (
                LimitRoutes.SET_SUBJECT_LIMITS,
                LimitEndpoints.set_subject_limits,
                "limit_set_subject_req",
            ),
            (
                LimitRoutes.SET_API_RATE_LIMITS,
                LimitEndpoints.set_api_rate_limits,
                "limit_set_rate_req",
            ),
        ],
        indirect=["req_factory"],
    )
    def test_happy_path_post(
        self,
        limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[BaseModel], None],
        req_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        request = req_factory.build()
        request_dump = request.model_dump(mode="json", by_alias=True)

        # Act
        fake_transport.enqueue({})
        getattr(limit_eps, method.__name__)(request)

        # Assert
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert target_path == call.path
        assert call.headers is None
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method"],
        [
            (LimitRoutes.RESET_SESSION_LIMITS, LimitEndpoints.reset_session_limits),
            (LimitRoutes.RESET_SUBJECT_LIMITS, LimitEndpoints.reset_subject_limits),
            (LimitRoutes.RESET_API_RATE_LIMITS, LimitEndpoints.reset_api_rate_limits),
        ],
    )
    def test_happy_path_delete(
        self,
        limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[], None],
    ):
        # Arrange
        fake_transport.enqueue({})

        # Act
        getattr(limit_eps, method.__name__)()

        # Assert
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert target_path == call.path
        assert fake_transport.responses == []

    def test_set_production_rate_limits(
        self,
        limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        # Arrange
        fake_transport.enqueue({})

        # Act
        limit_eps.set_production_rate_limits()

        # Assert
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == LimitRoutes.SET_PRODUCTION_RATE_LIMITS

    @pytest.mark.parametrize(
        ["method", "resp_factory"],
        [
            (
                LimitEndpoints.get_context_limits,
                "limit_context_resp",
            ),
            (
                LimitEndpoints.get_subject_limits,
                "limit_subject_resp",
            ),
            (
                LimitEndpoints.get_api_rate_limits,
                "limit_rate_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_response_validation(
        self,
        limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
        method: Callable[[], BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        response_data = resp_factory.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        # Act & Assert
        fake_transport.enqueue(response_data)
        _ = getattr(limit_eps, method.__name__)()

        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method", "req_factory"],
        [
            (
                LimitRoutes.SET_SESSION_LIMITS,
                LimitEndpoints.set_session_limits,
                "limit_set_session_req",
            ),
            (
                LimitRoutes.SET_SUBJECT_LIMITS,
                LimitEndpoints.set_subject_limits,
                "limit_set_subject_req",
            ),
            (
                LimitRoutes.SET_API_RATE_LIMITS,
                LimitEndpoints.set_api_rate_limits,
                "limit_set_rate_req",
            ),
        ],
        indirect=["req_factory"],
    )
    def test_transport_error_post(
        self,
        handled_limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[BaseModel], None],
        req_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        request = req_factory.build()
        expected_dump = request.model_dump(mode="json")

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            # Act
            fake_transport.enqueue(
                status_code=code, content=None, json_body=expected_dump
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel, getattr(handled_limit_eps, method.__name__)(request)
                )

            # Assert
            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert target_path == call.path
            assert call.headers is None
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None

            assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method", "resp_factory"],
        [
            (
                LimitRoutes.GET_CONTEXT_LIMITS,
                LimitEndpoints.get_context_limits,
                "limit_context_resp",
            ),
            (
                LimitRoutes.GET_SUBJECT_LIMITS,
                LimitEndpoints.get_subject_limits,
                "limit_subject_resp",
            ),
            (
                LimitRoutes.GET_API_RATE_LIMITS,
                LimitEndpoints.get_api_rate_limits,
                "limit_rate_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_transport_error_get(
        self,
        handled_limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[], BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        response = resp_factory.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            # Act
            fake_transport.enqueue(
                status_code=code, json_body=response.model_dump(mode="json")
            )

            with pytest.raises(exc):
                _ = getattr(handled_limit_eps, method.__name__)()

            # Assert
            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert target_path == call.path
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method"],
        [
            (LimitRoutes.RESET_SESSION_LIMITS, LimitEndpoints.reset_session_limits),
            (LimitRoutes.RESET_SUBJECT_LIMITS, LimitEndpoints.reset_subject_limits),
            (LimitRoutes.RESET_API_RATE_LIMITS, LimitEndpoints.reset_api_rate_limits),
        ],
    )
    def test_transport_error_delete(
        self,
        handled_limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[], None],
    ):
        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            # Act
            fake_transport.enqueue(status_code=code, json_body={})

            with pytest.raises(exc):
                getattr(handled_limit_eps, method.__name__)()

            # Assert
            call = fake_transport.calls[0]
            assert call.method == "DELETE"
            assert target_path == call.path
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    def test_set_production_rate_limits_transport_error(
        self,
        handled_limit_eps: limits.LimitEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            # Act
            fake_transport.enqueue(status_code=code, json_body={})

            with pytest.raises(exc):
                handled_limit_eps.set_production_rate_limits()

            # Assert
            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert call.path == LimitRoutes.SET_PRODUCTION_RATE_LIMITS
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []
