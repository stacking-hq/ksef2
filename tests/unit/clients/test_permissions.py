from polyfactory import BaseFactory

from ksef2.clients.permissions import PermissionsClient
from ksef2.core.routes import GrantPermissionsRoutes, QueryPermissionsRoutes
from ksef2.domain.models import permissions as domain_permissions
from ksef2.domain.models.pagination import OffsetPaginationParams
from ksef2.infra.mappers.permissions import grant_to_spec, query_to_spec
from ksef2.infra.schema.api import spec
from tests.unit.factories.permissions import (
    DomainAuthorizationPermissionsQueryFactory,
    DomainEntityPermissionsQueryFactory,
    DomainEuEntityPermissionsQueryFactory,
    DomainGrantAuthorizationPermissionsRequestFactory,
    DomainGrantEntityPermissionsRequestFactory,
    DomainGrantEuEntityAdministrationRequestFactory,
    DomainGrantEuEntityPermissionsRequestFactory,
    DomainGrantIndirectPermissionsRequestFactory,
    DomainGrantPersonPermissionsRequestFactory,
    DomainGrantSubunitPermissionsRequestFactory,
    DomainPersonalPermissionsQueryFactory,
    DomainPersonPermissionsQueryFactory,
    DomainSubordinateEntityRolesQueryFactory,
    DomainSubunitPermissionsQueryFactory,
)
from tests.unit.fakes.transport import FakeTransport


class TestPermissionsClient:
    def test_grant_person(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantPersonPermissionsRequestFactory.build()
        result = permissions_client.grant_person(
            subject_type=request.subject_type,
            subject_value=request.subject_value,
            permissions=request.permissions,
            description=request.description,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        expected_request = grant_to_spec(request)

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == GrantPermissionsRoutes.GRANT_PERSON
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request

    def test_grant_entity(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantEntityPermissionsRequestFactory.build()
        result = permissions_client.grant_entity(
            subject_value=request.subject_value,
            permissions=request.permissions,
            description=request.description,
            entity_name=request.entity_name,
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == GrantPermissionsRoutes.GRANT_ENTITY

    def test_grant_authorization(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantAuthorizationPermissionsRequestFactory.build()
        result = permissions_client.grant_authorization(
            subject_type=request.subject_type,
            subject_value=request.subject_value,
            permission=request.permission,
            description=request.description,
            entity_name=request.entity_name,
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == GrantPermissionsRoutes.GRANT_AUTHORIZATION

    def test_grant_indirect(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantIndirectPermissionsRequestFactory.build()
        result = permissions_client.grant_indirect(
            subject_type=request.subject_type,
            subject_value=request.subject_value,
            permissions=request.permissions,
            description=request.description,
            first_name=request.first_name,
            last_name=request.last_name,
            target_type=request.target_type,
            target_value="1234567890-12345",
        )
        expected_request = grant_to_spec(
            request.model_copy(update={"target_value": "1234567890-12345"})
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == GrantPermissionsRoutes.GRANT_INDIRECT
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request

    def test_grant_subunit(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantSubunitPermissionsRequestFactory.build()
        result = permissions_client.grant_subunit(
            subject_type=request.subject_type,
            subject_value=request.subject_value,
            context_type=request.context_type,
            context_value=request.context_value,
            description=request.description,
            first_name=request.first_name,
            last_name=request.last_name,
            subunit_name=request.subunit_name,
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == GrantPermissionsRoutes.GRANT_SUBUNITS

    def test_grant_eu_entity(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantEuEntityPermissionsRequestFactory.build()
        result = permissions_client.grant_eu_entity(
            subject_value=request.subject_value,
            permissions=request.permissions,
            description=request.description,
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == GrantPermissionsRoutes.GRANT_EU_ENTITY

    def test_grant_eu_entity_administration(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantEuEntityAdministrationRequestFactory.build()
        result = permissions_client.grant_eu_entity_administration(
            subject_value=request.subject_value,
            context_type=request.context_type,
            context_value=request.context_value,
            description=request.description,
            eu_entity_name=request.eu_entity_name,
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == GrantPermissionsRoutes.GRANT_ADMINISTERED_EU_ENTITY

    def test_query_persons(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_person_resp: BaseFactory[spec.QueryPersonPermissionsResponse],
    ):
        expected = perm_query_person_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainPersonPermissionsQueryFactory.build()
        result = permissions_client.query_persons(query=query)

        assert isinstance(result, domain_permissions.PersonPermissionsQueryResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_PERSONS_GRANTS
        assert call.params is not None
        assert call.params["pageOffset"] == "0"
        assert call.params["pageSize"] == "10"

    def test_query_authorizations(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_auth_resp: BaseFactory[
            spec.QueryEntityAuthorizationPermissionsResponse
        ],
    ):
        expected = perm_query_auth_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainAuthorizationPermissionsQueryFactory.build()
        result = permissions_client.query_authorizations(query=query)

        assert isinstance(
            result, domain_permissions.AuthorizationPermissionsQueryResponse
        )
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_AUTHORIZATIONS_GRANTS

    def test_query_entities(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_entity_resp: BaseFactory[spec.QueryEntityPermissionsResponse],
    ):
        expected = perm_query_entity_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainEntityPermissionsQueryFactory.build()
        result = permissions_client.query_entities(query=query)

        assert isinstance(result, domain_permissions.EntityPermissionsQueryResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_ENTITIES_GRANTS

    def test_query_personal(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_personal_resp: BaseFactory[spec.QueryPersonalPermissionsResponse],
    ):
        expected = perm_query_personal_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainPersonalPermissionsQueryFactory.build()
        result = permissions_client.query_personal(query=query)

        assert isinstance(result, domain_permissions.PersonalPermissionsQueryResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_PERSONAL_GRANTS

    def test_query_eu_entities(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_eu_entity_resp: BaseFactory[spec.QueryEuEntityPermissionsResponse],
    ):
        expected = perm_query_eu_entity_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainEuEntityPermissionsQueryFactory.build()
        result = permissions_client.query_eu_entities(query=query)

        assert isinstance(result, domain_permissions.EuEntityPermissionsQueryResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_EU_ENTITIES_GRANTS

    def test_query_subordinate_entities(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_subordinate_resp: BaseFactory[
            spec.QuerySubordinateEntityRolesResponse
        ],
    ):
        expected = perm_query_subordinate_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainSubordinateEntityRolesQueryFactory.build()
        result = permissions_client.query_subordinate_entities(query=query)

        assert isinstance(
            result, domain_permissions.SubordinateEntityRolesQueryResponse
        )
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_SUBORDINATE_ENTITIES_ROLES

    def test_query_subunits(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_subunit_resp: BaseFactory[spec.QuerySubunitPermissionsResponse],
    ):
        expected = perm_query_subunit_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainSubunitPermissionsQueryFactory.build()
        result = permissions_client.query_subunits(query=query)

        assert isinstance(result, domain_permissions.SubunitPermissionsQueryResponse)
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_SUBUNITS_GRANTS

    def test_revoke_authorization(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = permissions_client.revoke_authorization(
            permission_id="123e4567-e89b-12d3-a456-426614174000"
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert call.path.endswith(
            "/authorizations/grants/123e4567-e89b-12d3-a456-426614174000"
        )

    def test_revoke_common(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        expected = perm_op_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = permissions_client.revoke_common(
            permission_id="123e4567-e89b-12d3-a456-426614174000"
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        call = fake_transport.calls[0]
        assert call.method == "DELETE"
        assert call.path.endswith("/common/grants/123e4567-e89b-12d3-a456-426614174000")

    def test_get_attachment_permission_status(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_attachment_status_resp: BaseFactory[
            spec.CheckAttachmentPermissionStatusResponse
        ],
    ):
        expected = perm_attachment_status_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = permissions_client.get_attachment_permission_status()

        assert isinstance(result, domain_permissions.AttachmentPermissionStatus)
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_ATTACHMENTS_STATUS

    def test_get_operation_status(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_op_status_resp: BaseFactory[spec.PermissionsOperationStatusResponse],
    ):
        expected = perm_op_status_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = permissions_client.get_operation_status(reference_number="ref-123")

        assert isinstance(result, domain_permissions.PermissionOperationStatusResponse)
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert call.path.endswith("/operations/ref-123")

    def test_get_entity_roles_with_custom_pagination(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_entity_roles_resp: BaseFactory[spec.QueryEntityRolesResponse],
    ):
        expected = perm_entity_roles_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        result = permissions_client.get_entity_roles(
            params=OffsetPaginationParams(page_offset=2, page_size=25)
        )

        assert isinstance(result, domain_permissions.EntityRolesResponse)
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == QueryPermissionsRoutes.QUERY_ENTITY_ROLES
        assert call.params is not None
        assert call.params["pageOffset"] == "2"
        assert call.params["pageSize"] == "25"

    def test_query_persons_with_custom_pagination(
        self,
        permissions_client: PermissionsClient,
        fake_transport: FakeTransport,
        perm_query_person_resp: BaseFactory[spec.QueryPersonPermissionsResponse],
    ):
        expected = perm_query_person_resp.build()
        fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainPersonPermissionsQueryFactory.build(
            author_type="nip",
            author_value="1234567890",
        )
        result = permissions_client.query_persons(
            query=query,
            params=OffsetPaginationParams(page_offset=1, page_size=20),
        )
        expected_request = query_to_spec(query)

        assert isinstance(result, domain_permissions.PersonPermissionsQueryResponse)
        call = fake_transport.calls[0]
        assert call.params is not None
        assert call.params["pageOffset"] == "1"
        assert call.params["pageSize"] == "20"
        assert call.json is not None
        actual_request = type(expected_request).model_validate(call.json)
        assert actual_request == expected_request
