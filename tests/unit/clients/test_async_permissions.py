import asyncio

from polyfactory import BaseFactory

from ksef2.clients.async_permissions import AsyncPermissionsClient
from ksef2.domain.models import permissions as domain_permissions
from ksef2.infra.schema.api import spec
from tests.unit.factories.permissions import (
    DomainAuthorizationPermissionsQueryFactory,
    DomainGrantPersonPermissionsRequestFactory,
    DomainPersonPermissionsQueryFactory,
)
from tests.unit.fakes.transport import AsyncFakeTransport


class TestAsyncPermissionsClient:
    def test_grant_person(
        self,
        async_fake_transport: AsyncFakeTransport,
        perm_op_resp: BaseFactory[spec.PermissionsOperationResponse],
    ):
        client = AsyncPermissionsClient(async_fake_transport)
        expected = perm_op_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        request = DomainGrantPersonPermissionsRequestFactory.build()
        result = asyncio.run(
            client.grant_person(
                subject_type=request.subject_type,
                subject_value=request.subject_value,
                permissions=request.permissions,
                description=request.description,
                first_name=request.first_name,
                last_name=request.last_name,
            )
        )

        assert isinstance(result, domain_permissions.GrantPermissionsResponse)
        assert async_fake_transport.calls[0].method == "POST"

    def test_query_persons(
        self,
        async_fake_transport: AsyncFakeTransport,
        perm_query_person_resp: BaseFactory[spec.QueryPersonPermissionsResponse],
    ):
        client = AsyncPermissionsClient(async_fake_transport)
        expected = perm_query_person_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainPersonPermissionsQueryFactory.build()
        result = asyncio.run(client.query_persons(query=query))

        assert isinstance(result, domain_permissions.PersonPermissionsQueryResponse)
        assert async_fake_transport.calls[0].method == "POST"

    def test_query_authorizations(
        self,
        async_fake_transport: AsyncFakeTransport,
        perm_query_auth_resp: BaseFactory[
            spec.QueryEntityAuthorizationPermissionsResponse
        ],
    ):
        client = AsyncPermissionsClient(async_fake_transport)
        expected = perm_query_auth_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        query = DomainAuthorizationPermissionsQueryFactory.build()
        result = asyncio.run(client.query_authorizations(query=query))

        assert isinstance(
            result, domain_permissions.AuthorizationPermissionsQueryResponse
        )
