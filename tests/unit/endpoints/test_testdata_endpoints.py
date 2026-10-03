from datetime import datetime, timezone
from typing import cast, Callable

import pytest

from polyfactory.factories import BaseFactory
from pydantic import BaseModel

from ksef2._core import exceptions
from ksef2._core.routes import TestDataRoutes
from ksef2._endpoints.testdata import TestDataEndpoints
from ksef2._infra.schema.api import spec
from tests.unit.fakes import transport

from ksef2._core.middlewares.exceptions import KSeFExceptionMiddleware


@pytest.fixture
def req_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


class TestTestDataEndpoints:
    @pytest.fixture
    def testdata_eps(
        self, fake_transport: transport.FakeTransport
    ) -> TestDataEndpoints:
        return TestDataEndpoints(fake_transport)

    @pytest.fixture
    def handled_testdata_eps(
        self, fake_transport: transport.FakeTransport
    ) -> TestDataEndpoints:
        return TestDataEndpoints(KSeFExceptionMiddleware(fake_transport))

    @pytest.mark.parametrize(
        ["target_path", "method", "req_factory"],
        [
            (
                TestDataRoutes.CREATE_SUBJECT,
                TestDataEndpoints.create_subject,
                "td_create_subject_req",
            ),
            (
                TestDataRoutes.DELETE_SUBJECT,
                TestDataEndpoints.delete_subject,
                "td_delete_subject_req",
            ),
            (
                TestDataRoutes.CREATE_PERSON,
                TestDataEndpoints.create_person,
                "td_create_person_req",
            ),
            (
                TestDataRoutes.DELETE_PERSON,
                TestDataEndpoints.delete_person,
                "td_delete_person_req",
            ),
            (
                TestDataRoutes.GRANT_PERMISSIONS,
                TestDataEndpoints.grant_permissions,
                "td_grant_permissions_req",
            ),
            (
                TestDataRoutes.REVOKE_PERMISSIONS,
                TestDataEndpoints.revoke_permissions,
                "td_revoke_permissions_req",
            ),
            (
                TestDataRoutes.ENABLE_ATTACHMENTS,
                TestDataEndpoints.enable_attachments,
                "td_enable_attachments_req",
            ),
            (
                TestDataRoutes.REVOKE_ATTACHMENTS,
                TestDataEndpoints.revoke_attachments,
                "td_revoke_attachments_req",
            ),
            (
                TestDataRoutes.BLOCK_CONTEXT,
                TestDataEndpoints.block_context,
                "td_block_context_req",
            ),
            (
                TestDataRoutes.UNBLOCK_CONTEXT,
                TestDataEndpoints.unblock_context,
                "td_unblock_context_req",
            ),
        ],
        indirect=["req_factory"],
    )
    def test_happy_path(
        self,
        testdata_eps: TestDataEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[BaseModel], None],
        req_factory: BaseFactory[BaseModel],
    ):
        request = req_factory.build()
        request_dump = request.model_dump(mode="json", by_alias=True)

        fake_transport.enqueue({})
        getattr(testdata_eps, method.__name__)(request)

        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert target_path == call.path
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method", "req_factory"],
        [
            (
                TestDataRoutes.CREATE_SUBJECT,
                TestDataEndpoints.create_subject,
                "td_create_subject_req",
            ),
            (
                TestDataRoutes.DELETE_SUBJECT,
                TestDataEndpoints.delete_subject,
                "td_delete_subject_req",
            ),
            (
                TestDataRoutes.CREATE_PERSON,
                TestDataEndpoints.create_person,
                "td_create_person_req",
            ),
            (
                TestDataRoutes.DELETE_PERSON,
                TestDataEndpoints.delete_person,
                "td_delete_person_req",
            ),
            (
                TestDataRoutes.GRANT_PERMISSIONS,
                TestDataEndpoints.grant_permissions,
                "td_grant_permissions_req",
            ),
            (
                TestDataRoutes.REVOKE_PERMISSIONS,
                TestDataEndpoints.revoke_permissions,
                "td_revoke_permissions_req",
            ),
            (
                TestDataRoutes.ENABLE_ATTACHMENTS,
                TestDataEndpoints.enable_attachments,
                "td_enable_attachments_req",
            ),
            (
                TestDataRoutes.REVOKE_ATTACHMENTS,
                TestDataEndpoints.revoke_attachments,
                "td_revoke_attachments_req",
            ),
            (
                TestDataRoutes.BLOCK_CONTEXT,
                TestDataEndpoints.block_context,
                "td_block_context_req",
            ),
            (
                TestDataRoutes.UNBLOCK_CONTEXT,
                TestDataEndpoints.unblock_context,
                "td_unblock_context_req",
            ),
        ],
        indirect=["req_factory"],
    )
    def test_transport_error(
        self,
        handled_testdata_eps: TestDataEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[BaseModel], None],
        req_factory: BaseFactory[BaseModel],
    ):
        request = req_factory.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.enqueue(status_code=code, content=None, json_body={})

            with pytest.raises(exc):
                getattr(handled_testdata_eps, method.__name__)(request)

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert target_path == call.path
            assert call.headers is None
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None

            assert fake_transport.responses == []

    def test_update_certificate_uses_put(
        self,
        testdata_eps: TestDataEndpoints,
        fake_transport: transport.FakeTransport,
    ) -> None:
        request = spec.TestDataUpdateCertificateRequest(
            validTo=datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
        )
        fake_transport.enqueue({})

        testdata_eps.update_certificate("0123456789ABCDEF", request)

        call = fake_transport.calls[0]
        assert call.method == "PUT"
        assert call.path == TestDataRoutes.UPDATE_CERTIFICATE.format(
            serialNumber="0123456789ABCDEF"
        )
        assert call.json == {"validTo": "2026-07-22T10:00:00Z"}
