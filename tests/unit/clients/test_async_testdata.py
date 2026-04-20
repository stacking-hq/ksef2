import asyncio
from datetime import date, datetime, timezone

from polyfactory import BaseFactory

from ksef2.clients.async_testdata import (
    AsyncTemporalTestData,
    AsyncTestDataClient,
)
from ksef2.core.routes import TestDataRoutes as ApiRoutes
from ksef2.domain.models.testdata import (
    AuthContextIdentifier,
    CreatePersonRequest,
    CreateSubjectRequest,
    GrantPermissionsRequest,
    Identifier,
    Permission,
    RevokePermissionsRequest,
)
from ksef2.infra.mappers.testdata import to_spec
from tests.unit.fakes.transport import AsyncFakeTransport


class TestAsyncTestDataClient:
    def test_create_subject(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_td_create_subject_req: BaseFactory[CreateSubjectRequest],
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        request = domain_td_create_subject_req.build(
            created_date=datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc),
        )
        async_fake_transport.enqueue({})

        asyncio.run(
            client.create_subject(
                nip=request.subject_nip,
                subject_type=request.subject_type,
                description=request.description,
                subunits=request.subunits,
                created_date=request.created_date,
            )
        )

        assert async_fake_transport.calls[0].path == ApiRoutes.CREATE_SUBJECT
        assert async_fake_transport.calls[0].json == to_spec(request).model_dump(
            mode="json"
        )

    def test_create_person(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_td_create_person_req: BaseFactory[CreatePersonRequest],
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        request = domain_td_create_person_req.build()
        async_fake_transport.enqueue({})

        asyncio.run(
            client.create_person(
                nip=request.nip,
                pesel=request.pesel,
                description=request.description,
                is_bailiff=request.is_bailiff,
                is_deceased=request.is_deceased,
                created_date=request.created_date,
            )
        )

        assert async_fake_transport.calls[0].path == ApiRoutes.CREATE_PERSON

    def test_grant_permissions(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_td_grant_permissions_req: BaseFactory[GrantPermissionsRequest],
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        request = domain_td_grant_permissions_req.build()
        async_fake_transport.enqueue({})

        asyncio.run(
            client.grant_permissions(
                permissions=request.permissions,
                grant_to=request.grant_to,
                in_context_of=request.in_context_of,
            )
        )

        assert async_fake_transport.calls[0].path == ApiRoutes.GRANT_PERMISSIONS

    def test_revoke_permissions(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_td_revoke_permissions_req: BaseFactory[RevokePermissionsRequest],
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        request = domain_td_revoke_permissions_req.build()
        async_fake_transport.enqueue({})

        asyncio.run(
            client.revoke_permissions(
                revoke_from=request.revoke_from,
                in_context_of=request.in_context_of,
            )
        )

        assert async_fake_transport.calls[0].path == ApiRoutes.REVOKE_PERMISSIONS

    def test_revoke_attachments(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        async_fake_transport.enqueue({})

        asyncio.run(
            client.revoke_attachments(
                nip="1234567890",
                expected_end_date=date(2026, 3, 6),
            )
        )

        assert async_fake_transport.calls[0].path == ApiRoutes.REVOKE_ATTACHMENTS
        assert async_fake_transport.calls[0].json == {
            "nip": "1234567890",
            "expectedEndDate": "2026-03-06",
        }

    def test_block_and_unblock_context(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_td_auth_context_identifier: BaseFactory[AuthContextIdentifier],
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        context = domain_td_auth_context_identifier.build()
        async_fake_transport.enqueue({})
        async_fake_transport.enqueue({})

        asyncio.run(client.block_context(context=context))
        asyncio.run(client.unblock_context(context=context))

        assert [call.path for call in async_fake_transport.calls] == [
            ApiRoutes.BLOCK_CONTEXT,
            ApiRoutes.UNBLOCK_CONTEXT,
        ]

    def test_temporal_returns_helper(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        assert isinstance(client.temporal(), AsyncTemporalTestData)


class TestAsyncTemporalTestData:
    def test_cleanup_uses_client_api_in_reverse_order(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_td_identifier: BaseFactory[Identifier],
        domain_td_permission: BaseFactory[Permission],
        domain_td_auth_context_identifier: BaseFactory[AuthContextIdentifier],
    ) -> None:
        client = AsyncTestDataClient(async_fake_transport)
        grant_to = domain_td_identifier.build(value="1234567890")
        in_context_of = domain_td_identifier.build(value="2234567890")
        context = domain_td_auth_context_identifier.build(value="ctx-1")
        permission = domain_td_permission.build()
        for _ in range(10):
            async_fake_transport.enqueue({})

        async def _run() -> None:
            async with client.temporal() as temp:
                await temp.create_subject(
                    nip="1234567890",
                    subject_type="enforcement_authority",
                    description="Subject",
                )
                await temp.create_person(
                    nip="2234567890",
                    pesel="12345678901",
                    description="Person",
                )
                await temp.grant_permissions(
                    permissions=[permission],
                    grant_to=grant_to,
                    in_context_of=in_context_of,
                )
                await temp.enable_attachments(nip="1234567890")
                await temp.block_context(context=context)

        asyncio.run(_run())

        assert [call.path for call in async_fake_transport.calls] == [
            ApiRoutes.CREATE_SUBJECT,
            ApiRoutes.CREATE_PERSON,
            ApiRoutes.GRANT_PERMISSIONS,
            ApiRoutes.ENABLE_ATTACHMENTS,
            ApiRoutes.BLOCK_CONTEXT,
            ApiRoutes.UNBLOCK_CONTEXT,
            ApiRoutes.REVOKE_ATTACHMENTS,
            ApiRoutes.REVOKE_PERMISSIONS,
            ApiRoutes.DELETE_PERSON,
            ApiRoutes.DELETE_SUBJECT,
        ]
