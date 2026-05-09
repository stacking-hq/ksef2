from typing import cast

import pytest

from pydantic import BaseModel

from ksef2.core import exceptions
from ksef2.core.routes import SessionRoutes
from ksef2.endpoints.session import SessionEndpoints
from tests.unit.fakes import transport
from tests.unit.factories.session import (
    OpenOnlineSessionRequestFactory,
    OpenOnlineSessionResponseFactory,
    OpenBatchSessionRequestFactory,
    OpenBatchSessionResponseFactory,
    SessionsQueryResponseFactory,
)

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


class TestSessionEndpoints:
    @pytest.fixture
    def session_eps(self, fake_transport: transport.FakeTransport) -> SessionEndpoints:
        return SessionEndpoints(fake_transport)

    @pytest.fixture
    def handled_session_eps(
        self, fake_transport: transport.FakeTransport
    ) -> SessionEndpoints:
        return SessionEndpoints(KSeFExceptionMiddleware(fake_transport))

    def test_open_online(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_open_online_req: OpenOnlineSessionRequestFactory,
        session_open_online_resp: OpenOnlineSessionResponseFactory,
    ):
        request = session_open_online_req.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = session_open_online_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = session_eps.open_online(request)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == SessionRoutes.OPEN_ONLINE
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_open_online_response_validation(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_open_online_req: OpenOnlineSessionRequestFactory,
        session_open_online_resp: OpenOnlineSessionResponseFactory,
    ):
        request = session_open_online_req.build()
        response_data = session_open_online_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = session_eps.open_online(request)

        assert fake_transport.responses == []

    def test_open_online_transport_error(
        self,
        handled_session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_open_online_req: OpenOnlineSessionRequestFactory,
        session_open_online_resp: OpenOnlineSessionResponseFactory,
    ):
        request = session_open_online_req.build()
        response = session_open_online_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                status_code=code,
                json_body=response.model_dump(mode="json"),
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_session_eps.open_online(request))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == SessionRoutes.OPEN_ONLINE
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.headers is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_terminate_online(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-SO-2C3E6C8000-B675CF5D68-07"

        fake_transport.enqueue(json_body={})
        session_eps.terminate_online(reference_number)

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == SessionRoutes.TERMINATE_ONLINE.format(
            referenceNumber=reference_number
        )
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_terminate_online_transport_error(
        self,
        handled_session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-SO-2C3E6C8000-B675CF5D68-07"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code, json_body={})

            with pytest.raises(exc):
                handled_session_eps.terminate_online(reference_number)

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == SessionRoutes.TERMINATE_ONLINE.format(
                referenceNumber=reference_number
            )
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_open_batch(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_open_batch_req: OpenBatchSessionRequestFactory,
        session_open_batch_resp: OpenBatchSessionResponseFactory,
    ):
        request = session_open_batch_req.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = session_open_batch_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = session_eps.open_batch(request)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == SessionRoutes.OPEN_BATCH
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert call.params is None
        assert fake_transport.responses == []

    def test_open_batch_response_validation(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_open_batch_req: OpenBatchSessionRequestFactory,
        session_open_batch_resp: OpenBatchSessionResponseFactory,
    ):
        request = session_open_batch_req.build()
        response_data = session_open_batch_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = session_eps.open_batch(request)

        assert fake_transport.responses == []

    def test_open_batch_transport_error(
        self,
        handled_session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_open_batch_req: OpenBatchSessionRequestFactory,
        session_open_batch_resp: OpenBatchSessionResponseFactory,
    ):
        request = session_open_batch_req.build()
        response = session_open_batch_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                status_code=code,
                json_body=response.model_dump(mode="json"),
            )

            with pytest.raises(exc):
                _ = cast(BaseModel, handled_session_eps.open_batch(request))

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == SessionRoutes.OPEN_BATCH
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.headers is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_close_batch(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-SB-2C3E6C8000-B675CF5D68-07"

        fake_transport.enqueue(json_body={})
        session_eps.close_batch(reference_number)

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == SessionRoutes.CLOSE_BATCH.format(
            referenceNumber=reference_number
        )
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_close_batch_transport_error(
        self,
        handled_session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-SB-2C3E6C8000-B675CF5D68-07"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code, json_body={})

            with pytest.raises(exc):
                handled_session_eps.close_batch(reference_number)

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == SessionRoutes.CLOSE_BATCH.format(
                referenceNumber=reference_number
            )
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []

    def test_get_session_upo(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-SO-2C3E6C8000-B675CF5D68-07"
        upo_reference_number = "20250625-UPO-2C3E6C8000-B675CF5D68-07"
        upo_content = b"<UPO>...</UPO>"

        fake_transport.enqueue(content=upo_content)
        result = session_eps.get_session_upo(reference_number, upo_reference_number)

        assert result == upo_content
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == SessionRoutes.GET_SESSION_UPO.format(
            referenceNumber=reference_number,
            upoReferenceNumber=upo_reference_number,
        )
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_get_session_upo_transport_error(
        self,
        handled_session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
    ):
        reference_number = "20250625-SO-2C3E6C8000-B675CF5D68-07"
        upo_reference_number = "20250625-UPO-2C3E6C8000-B675CF5D68-07"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code, content=b"")

            with pytest.raises(exc):
                handled_session_eps.get_session_upo(
                    reference_number, upo_reference_number
                )

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == SessionRoutes.GET_SESSION_UPO.format(
                referenceNumber=reference_number,
                upoReferenceNumber=upo_reference_number,
            )
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    def test_list_sessions(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_list_resp: SessionsQueryResponseFactory,
    ):
        expected = session_list_resp.build()
        expected_dump = expected.model_dump(mode="json")

        fake_transport.enqueue(expected_dump)
        response = session_eps.list_sessions(sessionType="Online")

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == SessionRoutes.LIST_SESSIONS
        assert call.params is not None
        assert call.params.get("sessionType") == "Online"
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    def test_list_sessions_continuation_token(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_list_resp: SessionsQueryResponseFactory,
    ):
        expected = session_list_resp.build()
        expected_dump = expected.model_dump(mode="json")
        continuation_token = "test-continuation-token"

        fake_transport.enqueue(expected_dump)
        response = session_eps.list_sessions(
            sessionType="Online", continuation_token=continuation_token
        )

        assert response == expected
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == SessionRoutes.LIST_SESSIONS
        assert call.headers is not None
        assert call.headers.get("x-continuation-token") == continuation_token
        assert fake_transport.responses == []

    def test_list_sessions_response_validation(
        self,
        session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_list_resp: SessionsQueryResponseFactory,
    ):
        response_data = session_list_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        fake_transport.enqueue(response_data)
        _ = session_eps.list_sessions(sessionType="Online")

        assert fake_transport.responses == []

    def test_list_sessions_transport_error(
        self,
        handled_session_eps: SessionEndpoints,
        fake_transport: transport.FakeTransport,
        session_list_resp: SessionsQueryResponseFactory,
    ):
        response = session_list_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel,
                    handled_session_eps.list_sessions(sessionType="Online"),
                )

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == SessionRoutes.LIST_SESSIONS
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []
