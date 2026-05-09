from typing import cast, Callable
from urllib.parse import urlencode

import pytest

from polyfactory.factories import BaseFactory
from pydantic import BaseModel

from ksef2.core import exceptions
from ksef2.domain.models.pagination import PermissionsQueryParams
from ksef2.endpoints.permissions import (
    GetPermissionsEndpoints,
    PermissionsGrantEndpoints,
    RevokePermissionsEndpoints,
    QueryPermissionsEndpoints,
)
from tests.unit.fakes import transport
from tests.unit.factories.permissions import (
    CheckAttachmentPermissionStatusResponseFactory,
    PermissionsOperationResponseFactory,
    PermissionsOperationStatusResponseFactory,
    QueryEntityRolesResponseFactory,
)

from ksef2.core.routes import (
    GrantPermissionsRoutes,
    RevokePermissionsRoutes,
    QueryPermissionsRoutes,
)

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware


@pytest.fixture
def req_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


@pytest.fixture
def resp_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


class TestGrantPermissionsEndpoints:
    @pytest.fixture
    def grant_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> PermissionsGrantEndpoints:
        return PermissionsGrantEndpoints(fake_transport)

    @pytest.fixture
    def handled_grant_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> PermissionsGrantEndpoints:
        return PermissionsGrantEndpoints(KSeFExceptionMiddleware(fake_transport))

    @pytest.mark.parametrize(
        ["target_path", "method", "req_factory", "resp_factory"],
        [
            (
                GrantPermissionsRoutes.GRANT_PERSON,
                PermissionsGrantEndpoints.grant_person,
                "perm_grant_person_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_ENTITY,
                PermissionsGrantEndpoints.grant_entity,
                "perm_grant_entity_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_AUTHORIZATION,
                PermissionsGrantEndpoints.grant_authorization,
                "perm_grant_auth_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_INDIRECT,
                PermissionsGrantEndpoints.grant_indirect,
                "perm_grant_indirect_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_SUBUNITS,
                PermissionsGrantEndpoints.grant_subunit,
                "perm_grant_subunit_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_ADMINISTERED_EU_ENTITY,
                PermissionsGrantEndpoints.grant_administered_eu_entity,
                "perm_grant_eu_admin_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_EU_ENTITY,
                PermissionsGrantEndpoints.grant_eu_entity,
                "perm_grant_eu_entity_req",
                "perm_op_resp",
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_happy_path(
        self,
        grant_permissions_eps: PermissionsGrantEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[BaseModel], BaseModel],
        req_factory: BaseFactory[BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        request = req_factory.build()
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = resp_factory.build()
        expected_dump = expected.model_dump(mode="json")

        # Act
        fake_transport.enqueue(expected_dump)
        response = getattr(grant_permissions_eps, method.__name__)(request)

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST", "All grant endpoints should use POST"
        assert target_path == call.path
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None, "Grant endpoints dont require custom headers"
        assert call.params is None, "Grant endpoints dont take in params"
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method", "req_factory", "resp_factory"],
        [
            (
                PermissionsGrantEndpoints.grant_person,
                "perm_grant_person_req",
                "perm_op_resp",
            ),
            (
                PermissionsGrantEndpoints.grant_entity,
                "perm_grant_entity_req",
                "perm_op_resp",
            ),
            (
                PermissionsGrantEndpoints.grant_authorization,
                "perm_grant_auth_req",
                "perm_op_resp",
            ),
            (
                PermissionsGrantEndpoints.grant_indirect,
                "perm_grant_indirect_req",
                "perm_op_resp",
            ),
            (
                PermissionsGrantEndpoints.grant_subunit,
                "perm_grant_subunit_req",
                "perm_op_resp",
            ),
            (
                PermissionsGrantEndpoints.grant_administered_eu_entity,
                "perm_grant_eu_admin_req",
                "perm_op_resp",
            ),
            (
                PermissionsGrantEndpoints.grant_eu_entity,
                "perm_grant_eu_entity_req",
                "perm_op_resp",
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_response_validation(
        self,
        grant_permissions_eps: PermissionsGrantEndpoints,
        fake_transport: transport.FakeTransport,
        method: Callable[[BaseModel], BaseModel],
        req_factory: BaseFactory[BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        request = req_factory.build()

        response_data = resp_factory.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }
        fake_transport.enqueue(response_data)
        _ = getattr(grant_permissions_eps, method.__name__)(request)

    @pytest.mark.parametrize(
        ["target_path", "method", "req_factory", "resp_factory"],
        [
            (
                GrantPermissionsRoutes.GRANT_PERSON,
                PermissionsGrantEndpoints.grant_person,
                "perm_grant_person_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_ENTITY,
                PermissionsGrantEndpoints.grant_entity,
                "perm_grant_entity_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_AUTHORIZATION,
                PermissionsGrantEndpoints.grant_authorization,
                "perm_grant_auth_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_INDIRECT,
                PermissionsGrantEndpoints.grant_indirect,
                "perm_grant_indirect_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_SUBUNITS,
                PermissionsGrantEndpoints.grant_subunit,
                "perm_grant_subunit_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_ADMINISTERED_EU_ENTITY,
                PermissionsGrantEndpoints.grant_administered_eu_entity,
                "perm_grant_eu_admin_req",
                "perm_op_resp",
            ),
            (
                GrantPermissionsRoutes.GRANT_EU_ENTITY,
                PermissionsGrantEndpoints.grant_eu_entity,
                "perm_grant_eu_entity_req",
                "perm_op_resp",
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_transport_error(
        self,
        handled_grant_permissions_eps: PermissionsGrantEndpoints,
        fake_transport: transport.FakeTransport,
        target_path: str,
        method: Callable[[BaseModel], BaseModel],
        req_factory: BaseFactory[BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        request = req_factory.build()
        expected = resp_factory.build()
        expected_dump = expected.model_dump(mode="json")

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            # Act
            fake_transport.clear()
            fake_transport.enqueue(
                status_code=code, content=None, json_body=expected_dump
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel,
                    getattr(handled_grant_permissions_eps, method.__name__)(request),
                )

            # Assert
            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert target_path == call.path
            assert call.headers is None
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []
            fake_transport.clear()


class TestRevokePermissionsEndpoints:
    @pytest.fixture
    def revoke_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> RevokePermissionsEndpoints:
        return RevokePermissionsEndpoints(fake_transport)

    @pytest.fixture
    def handled_revoke_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> RevokePermissionsEndpoints:
        return RevokePermissionsEndpoints(KSeFExceptionMiddleware(fake_transport))

    @pytest.mark.parametrize(
        ["target_path", "method"],
        [
            (
                RevokePermissionsRoutes.REVOKE_PERMISSION,
                RevokePermissionsEndpoints.revoke_person,
            ),
            (
                RevokePermissionsRoutes.REVOKE_AUTHORIZATION_PERMISSION,
                RevokePermissionsEndpoints.revoke_authorization,
            ),
        ],
    )
    def test_happy_path(
        self,
        revoke_permissions_eps: RevokePermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_op_resp: PermissionsOperationResponseFactory,
        target_path: str,
        method: Callable[[str], BaseModel],
    ):
        # Arrange
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))
        permission_id = "test-permission-id"

        # Act
        response = getattr(revoke_permissions_eps, method.__name__)(permission_id)

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert call.path == target_path.format(permissionId=permission_id)
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method", "resp_factory"],
        [
            (
                RevokePermissionsEndpoints.revoke_person,
                "perm_op_resp",
            ),
            (
                RevokePermissionsEndpoints.revoke_authorization,
                "perm_op_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_response_validation(
        self,
        revoke_permissions_eps: RevokePermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        method: Callable[[str], BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        response_data = resp_factory.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        # Act
        fake_transport.enqueue(response_data)
        _ = getattr(revoke_permissions_eps, method.__name__)("dummy-permission-id")
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["target_path", "method"],
        [
            (
                RevokePermissionsRoutes.REVOKE_PERMISSION,
                RevokePermissionsEndpoints.revoke_person,
            ),
            (
                RevokePermissionsRoutes.REVOKE_AUTHORIZATION_PERMISSION,
                RevokePermissionsEndpoints.revoke_authorization,
            ),
        ],
    )
    def test_transport_error(
        self,
        handled_revoke_permissions_eps: RevokePermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_op_resp: PermissionsOperationResponseFactory,
        target_path: str,
        method: Callable[[BaseModel], BaseModel],
    ):
        response = perm_op_resp.build()
        permission_id = "test-permission-id"

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            # Act
            fake_transport.clear()
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel,
                    getattr(handled_revoke_permissions_eps, method.__name__)(
                        permission_id
                    ),
                )

            # Assert
            call = fake_transport.calls[0]
            assert call.method == "DELETE"
            assert target_path.format(permissionId=permission_id) == call.path
            assert call.headers is None
            assert call.json is None
            assert call.content is None
            assert call.params is None

            assert fake_transport.responses == []
            fake_transport.clear()


class TestQueryPermissionsEndpoints:
    @pytest.fixture
    def query_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> QueryPermissionsEndpoints:
        return QueryPermissionsEndpoints(fake_transport)

    @pytest.fixture
    def handled_query_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> QueryPermissionsEndpoints:
        return QueryPermissionsEndpoints(KSeFExceptionMiddleware(fake_transport))

    @pytest.mark.parametrize(
        ["target_path", "method", "req_factory", "resp_factory"],
        [
            (
                QueryPermissionsRoutes.QUERY_ENTITIES_GRANTS,
                QueryPermissionsEndpoints.query_entities_grants,
                "perm_query_entity_req",
                "perm_query_entity_resp",
            ),
            (
                QueryPermissionsRoutes.QUERY_PERSONAL_GRANTS,
                QueryPermissionsEndpoints.query_personal_grants,
                "perm_query_personal_req",
                "perm_query_personal_resp",
            ),
            (
                QueryPermissionsRoutes.QUERY_AUTHORIZATIONS_GRANTS,
                QueryPermissionsEndpoints.query_authorizations_grants,
                "perm_query_auth_req",
                "perm_query_auth_resp",
            ),
            (
                QueryPermissionsRoutes.QUERY_EU_ENTITIES_GRANTS,
                QueryPermissionsEndpoints.query_eu_entities_grants,
                "perm_query_eu_entity_req",
                "perm_query_eu_entity_resp",
            ),
            (
                QueryPermissionsRoutes.QUERY_PERSONS_GRANTS,
                QueryPermissionsEndpoints.query_persons_grants,
                "perm_query_person_req",
                "perm_query_person_resp",
            ),
            (
                QueryPermissionsRoutes.QUERY_SUBORDINATE_ENTITIES_ROLES,
                QueryPermissionsEndpoints.query_subordinate_entities_roles,
                "perm_query_subordinate_req",
                "perm_query_subordinate_resp",
            ),
            (
                QueryPermissionsRoutes.QUERY_SUBUNITS_GRANTS,
                QueryPermissionsEndpoints.query_subunits_grants,
                "perm_query_subunit_req",
                "perm_query_subunit_resp",
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_happy_path(
        self,
        query_permissions_eps: QueryPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        permissions_params: PermissionsQueryParams,
        target_path: str,
        method: Callable[[BaseModel], BaseModel],
        req_factory: BaseFactory[BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        request = req_factory.build()
        params = permissions_params.to_query_params()
        expected = resp_factory.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        # Act
        response = getattr(query_permissions_eps, method.__name__)(request, **params)

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert call.path == target_path
        assert call.json == request.model_dump(mode="json")
        assert call.params is not None
        assert all((param in call.params for param in params.keys()))
        assert call.headers is None, "Query endpoints dont require custom headers"
        assert fake_transport.responses == []

    def test_query_attachments_status(
        self,
        query_permissions_eps: QueryPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_attachment_status_resp: CheckAttachmentPermissionStatusResponseFactory,
    ):
        # Arrange
        expected = perm_attachment_status_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        # Act
        response = query_permissions_eps.query_attachments_status()

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == QueryPermissionsRoutes.QUERY_ATTACHMENTS_STATUS
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method", "req_factory", "resp_factory"],
        [
            (
                QueryPermissionsEndpoints.query_entities_grants,
                "perm_query_entity_req",
                "perm_query_entity_resp",
            ),
            (
                QueryPermissionsEndpoints.query_personal_grants,
                "perm_query_personal_req",
                "perm_query_personal_resp",
            ),
            (
                QueryPermissionsEndpoints.query_authorizations_grants,
                "perm_query_auth_req",
                "perm_query_auth_resp",
            ),
            (
                QueryPermissionsEndpoints.query_eu_entities_grants,
                "perm_query_eu_entity_req",
                "perm_query_eu_entity_resp",
            ),
            (
                QueryPermissionsEndpoints.query_persons_grants,
                "perm_query_person_req",
                "perm_query_person_resp",
            ),
            (
                QueryPermissionsEndpoints.query_subordinate_entities_roles,
                "perm_query_subordinate_req",
                "perm_query_subordinate_resp",
            ),
            (
                QueryPermissionsEndpoints.query_subunits_grants,
                "perm_query_subunit_req",
                "perm_query_subunit_resp",
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_pagination_params(
        self,
        query_permissions_eps: QueryPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        method: Callable[[BaseModel], BaseModel],
        req_factory: BaseFactory[BaseModel],
        resp_factory: BaseFactory[BaseModel],
        permissions_params: PermissionsQueryParams,
    ):
        # Arrange
        expected = resp_factory.build()
        params = permissions_params.to_query_params()
        fake_transport.enqueue(expected.model_dump(mode="json"))
        request = req_factory.build()

        # Act
        response = getattr(query_permissions_eps, method.__name__)(request, **params)

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.params is not None
        assert all((param in call.params for param in params.keys()))

    @pytest.mark.parametrize(
        ["method", "req_factory", "resp_factory"],
        [
            (
                QueryPermissionsEndpoints.query_entities_grants,
                "perm_query_entity_req",
                "perm_query_entity_resp",
            ),
            (
                QueryPermissionsEndpoints.query_personal_grants,
                "perm_query_personal_req",
                "perm_query_personal_resp",
            ),
            (
                QueryPermissionsEndpoints.query_authorizations_grants,
                "perm_query_auth_req",
                "perm_query_auth_resp",
            ),
            (
                QueryPermissionsEndpoints.query_eu_entities_grants,
                "perm_query_eu_entity_req",
                "perm_query_eu_entity_resp",
            ),
            (
                QueryPermissionsEndpoints.query_persons_grants,
                "perm_query_person_req",
                "perm_query_person_resp",
            ),
            (
                QueryPermissionsEndpoints.query_subordinate_entities_roles,
                "perm_query_subordinate_req",
                "perm_query_subordinate_resp",
            ),
            (
                QueryPermissionsEndpoints.query_subunits_grants,
                "perm_query_subunit_req",
                "perm_query_subunit_resp",
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_response_validation(
        self,
        query_permissions_eps: QueryPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        method: Callable[[BaseModel], BaseModel],
        req_factory: BaseFactory[BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        # Arrange
        request = req_factory.build()
        response_data = resp_factory.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        # Act
        fake_transport.enqueue(response_data)
        _ = getattr(query_permissions_eps, method.__name__)(request)

        assert fake_transport.responses == []

    def test_query_attachments_status_response_validation(
        self,
        query_permissions_eps: QueryPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_attachment_status_resp: CheckAttachmentPermissionStatusResponseFactory,
    ):
        # Arrange
        response_data = perm_attachment_status_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        # Act
        fake_transport.enqueue(response_data)
        _ = query_permissions_eps.query_attachments_status()

        assert fake_transport.responses == []

    def test_query_attachments_status_transport_error(
        self,
        handled_query_permissions_eps: QueryPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_attachment_status_resp: CheckAttachmentPermissionStatusResponseFactory,
    ):
        response = perm_attachment_status_resp.build()
        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.clear()
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = handled_query_permissions_eps.query_attachments_status()

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert call.path == QueryPermissionsRoutes.QUERY_ATTACHMENTS_STATUS
            assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method", "req_factory", "resp_factory"],
        [
            (
                QueryPermissionsEndpoints.query_entities_grants,
                "perm_query_entity_req",
                "perm_query_entity_resp",
            ),
            (
                QueryPermissionsEndpoints.query_personal_grants,
                "perm_query_personal_req",
                "perm_query_personal_resp",
            ),
            (
                QueryPermissionsEndpoints.query_authorizations_grants,
                "perm_query_auth_req",
                "perm_query_auth_resp",
            ),
            (
                QueryPermissionsEndpoints.query_eu_entities_grants,
                "perm_query_eu_entity_req",
                "perm_query_eu_entity_resp",
            ),
            (
                QueryPermissionsEndpoints.query_persons_grants,
                "perm_query_person_req",
                "perm_query_person_resp",
            ),
            (
                QueryPermissionsEndpoints.query_subordinate_entities_roles,
                "perm_query_subordinate_req",
                "perm_query_subordinate_resp",
            ),
            (
                QueryPermissionsEndpoints.query_subunits_grants,
                "perm_query_subunit_req",
                "perm_query_subunit_resp",
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_transport_error(
        self,
        handled_query_permissions_eps: QueryPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        permissions_params: PermissionsQueryParams,
        method: Callable[[BaseModel], BaseModel],
        req_factory: BaseFactory[BaseModel],
        resp_factory: BaseFactory[BaseModel],
    ):
        request = req_factory.build()
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
            fake_transport.clear()
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = cast(
                    BaseModel,
                    getattr(handled_query_permissions_eps, method.__name__)(
                        request, **permissions_params.to_query_params()
                    ),
                )

            # Assert
            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert call.headers is None
            assert call.json is not None
            assert call.json == request.model_dump(mode="json")
            assert call.content is None

            assert fake_transport.responses == []
            fake_transport.clear()


class TestGetPermissionsEndpoints:
    @pytest.fixture
    def get_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> GetPermissionsEndpoints:
        return GetPermissionsEndpoints(fake_transport)

    @pytest.fixture
    def handled_get_permissions_eps(
        self, fake_transport: transport.FakeTransport
    ) -> GetPermissionsEndpoints:
        return GetPermissionsEndpoints(KSeFExceptionMiddleware(fake_transport))

    def test_query_operation_status(
        self,
        get_permissions_eps: GetPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_op_status_resp: PermissionsOperationStatusResponseFactory,
    ):
        # Arrange
        expected = perm_op_status_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))
        reference_number = "test-reference-number"

        # Act
        response = get_permissions_eps.query_operation_status(reference_number)

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == QueryPermissionsRoutes.QUERY_OPERATIONS_STATUS.format(
            referenceNumber=reference_number
        )
        assert fake_transport.responses == []

    def test_query_entity_roles(
        self,
        get_permissions_eps: GetPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_entity_roles_resp: QueryEntityRolesResponseFactory,
    ):
        # Arrange
        expected = perm_entity_roles_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        # Act
        response = get_permissions_eps.query_entity_roles()

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path == QueryPermissionsRoutes.QUERY_ENTITY_ROLES
        assert fake_transport.responses == []

    def test_query_entity_roles_pagination_params(
        self,
        get_permissions_eps: GetPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_entity_roles_resp: QueryEntityRolesResponseFactory,
        permissions_params: PermissionsQueryParams,
    ):
        # Arrange
        expected = perm_entity_roles_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))
        params = permissions_params.to_query_params()

        # Act
        response = get_permissions_eps.query_entity_roles(**params)

        # Assert
        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.params is not None
        assert urlencode(params) == str(call.params)

    def test_query_operation_status_response_validation(
        self,
        get_permissions_eps: GetPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_op_status_resp: PermissionsOperationStatusResponseFactory,
    ):
        # Arrange
        response_data = perm_op_status_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        # Act
        fake_transport.enqueue(response_data)
        _ = get_permissions_eps.query_operation_status("dummy-reference")

        assert fake_transport.responses == []

    def test_query_entity_roles_response_validation(
        self,
        get_permissions_eps: GetPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_entity_roles_resp: QueryEntityRolesResponseFactory,
    ):
        # Arrange
        response_data = perm_entity_roles_resp.build().model_dump(mode="json") | {
            "invalid_field": "invalid"
        }

        # Act
        fake_transport.enqueue(response_data)
        _ = get_permissions_eps.query_entity_roles()

        assert fake_transport.responses == []

    def test_query_operation_status_transport_error(
        self,
        handled_get_permissions_eps: GetPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_op_status_resp: PermissionsOperationStatusResponseFactory,
    ):
        reference_number = "test-reference-number"
        response = perm_op_status_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.clear()
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = handled_get_permissions_eps.query_operation_status(reference_number)

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert call.path == QueryPermissionsRoutes.QUERY_OPERATIONS_STATUS.format(
                referenceNumber=reference_number
            )
            assert fake_transport.responses == []

    def test_query_entity_roles_transport_error(
        self,
        handled_get_permissions_eps: GetPermissionsEndpoints,
        fake_transport: transport.FakeTransport,
        perm_entity_roles_resp: QueryEntityRolesResponseFactory,
    ):
        response = perm_entity_roles_resp.build()

        responses_to_try = [
            (exceptions.KSeFApiError, 500),
            (exceptions.KSeFRateLimitError, 429),
            (exceptions.KSeFAuthError, 403),
            (exceptions.KSeFAuthError, 401),
            (exceptions.KSeFApiError, 400),
        ]

        for exc, code in responses_to_try:
            fake_transport.clear()
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = handled_get_permissions_eps.query_entity_roles()

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert call.path == QueryPermissionsRoutes.QUERY_ENTITY_ROLES
            assert fake_transport.responses == []
