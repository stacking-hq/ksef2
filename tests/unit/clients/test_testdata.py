from datetime import date, datetime, timezone

from polyfactory import BaseFactory

from ksef2._clients.testdata import (
    TemporalTestData,
    TestDataClient as KSeFTestDataClient,
)
from ksef2._core.routes import TestDataRoutes as ApiRoutes
from ksef2._domain.models.testdata import (
    AuthContextIdentifier,
    CreatePersonRequest,
    CreateSubjectRequest,
    GrantPermissionsRequest,
    Identifier,
    Permission,
    RevokePermissionsRequest,
)
from ksef2._infra.mappers.testdata import to_spec
from tests.unit.fakes.transport import FakeTransport


class TestTestDataClient:
    def test_create_subject(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
        domain_td_create_subject_req: BaseFactory[CreateSubjectRequest],
    ) -> None:
        request = domain_td_create_subject_req.build(
            created_date=datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc),
        )
        fake_transport.enqueue({})

        testdata_client.create_subject(
            nip=request.subject_nip,
            subject_type=request.subject_type,
            description=request.description,
            subunits=request.subunits,
            created_date=request.created_date,
        )

        assert fake_transport.calls[0].path == ApiRoutes.CREATE_SUBJECT
        assert fake_transport.calls[0].json == to_spec(request).model_dump(mode="json")

    def test_create_person(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
        domain_td_create_person_req: BaseFactory[CreatePersonRequest],
    ) -> None:
        request = domain_td_create_person_req.build()
        fake_transport.enqueue({})

        testdata_client.create_person(
            nip=request.nip,
            pesel=request.pesel,
            description=request.description,
            is_bailiff=request.is_bailiff,
            is_deceased=request.is_deceased,
            created_date=request.created_date,
        )

        assert fake_transport.calls[0].path == ApiRoutes.CREATE_PERSON
        assert fake_transport.calls[0].json == to_spec(request).model_dump(mode="json")

    def test_grant_permissions(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
        domain_td_grant_permissions_req: BaseFactory[GrantPermissionsRequest],
    ) -> None:
        request = domain_td_grant_permissions_req.build()
        fake_transport.enqueue({})

        testdata_client.grant_permissions(
            permissions=request.permissions,
            grant_to=request.grant_to,
            in_context_of=request.in_context_of,
        )

        assert fake_transport.calls[0].path == ApiRoutes.GRANT_PERMISSIONS
        assert fake_transport.calls[0].json == to_spec(request).model_dump(mode="json")

    def test_revoke_permissions(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
        domain_td_revoke_permissions_req: BaseFactory[RevokePermissionsRequest],
    ) -> None:
        request = domain_td_revoke_permissions_req.build()
        fake_transport.enqueue({})

        testdata_client.revoke_permissions(
            revoke_from=request.revoke_from,
            in_context_of=request.in_context_of,
        )

        assert fake_transport.calls[0].path == ApiRoutes.REVOKE_PERMISSIONS
        assert fake_transport.calls[0].json == to_spec(request).model_dump(mode="json")

    def test_revoke_attachments(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
    ) -> None:
        fake_transport.enqueue({})

        testdata_client.revoke_attachments(
            nip="1234567890",
            expected_end_date=date(2026, 3, 6),
        )

        assert fake_transport.calls[0].path == ApiRoutes.REVOKE_ATTACHMENTS
        assert fake_transport.calls[0].json == {
            "nip": "1234567890",
            "expectedEndDate": "2026-03-06",
        }

    def test_block_and_unblock_context(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
        domain_td_auth_context_identifier: BaseFactory[AuthContextIdentifier],
    ) -> None:
        context = domain_td_auth_context_identifier.build()
        fake_transport.enqueue({})
        fake_transport.enqueue({})

        testdata_client.block_context(context=context)
        testdata_client.unblock_context(context=context)

        assert [call.path for call in fake_transport.calls] == [
            ApiRoutes.BLOCK_CONTEXT,
            ApiRoutes.UNBLOCK_CONTEXT,
        ]

    def test_update_certificate_valid_to(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
    ) -> None:
        fake_transport.enqueue({})

        testdata_client.update_certificate_valid_to(
            serial_number="0123456789ABCDEF",
            valid_to=datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc),
        )

        call = fake_transport.calls[0]
        assert call.method == "PUT"
        assert call.path == ApiRoutes.UPDATE_CERTIFICATE.format(
            serialNumber="0123456789ABCDEF"
        )
        assert call.json == {"validTo": "2026-07-22T10:00:00Z"}

    def test_temporal_returns_helper(
        self,
        testdata_client: KSeFTestDataClient,
    ) -> None:
        assert isinstance(testdata_client.temporal(), TemporalTestData)


class TestTemporalTestData:
    def test_cleanup_uses_client_api_in_reverse_order(
        self,
        testdata_client: KSeFTestDataClient,
        fake_transport: FakeTransport,
        domain_td_identifier: BaseFactory[Identifier],
        domain_td_permission: BaseFactory[Permission],
        domain_td_auth_context_identifier: BaseFactory[AuthContextIdentifier],
    ) -> None:
        grant_to = domain_td_identifier.build(value="1234567890")
        in_context_of = domain_td_identifier.build(value="2234567890")
        context = domain_td_auth_context_identifier.build(value="ctx-1")
        permission = domain_td_permission.build()
        for _ in range(10):
            fake_transport.enqueue({})

        with testdata_client.temporal() as temp:
            temp.create_subject(
                nip="1234567890",
                subject_type="enforcement_authority",
                description="Subject",
            )
            temp.create_person(
                nip="2234567890",
                pesel="12345678901",
                description="Person",
            )
            temp.grant_permissions(
                permissions=[permission],
                grant_to=grant_to,
                in_context_of=in_context_of,
            )
            temp.enable_attachments(nip="1234567890")
            temp.block_context(context=context)

        assert [call.path for call in fake_transport.calls] == [
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
