"""Async testdata endpoints for creating test data in KSeF."""

from typing import final

from ksef2.core import routes
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.infra.schema.api.supp.testdata import (
    BlockContextRequest,
    CreatePersonRequest,
    CreateSubjectRequest,
    DeletePersonRequest,
    DeleteSubjectRequest,
    EnableAttachmentsRequest,
    GrantPermissionsRequest,
    RevokeAttachmentsRequest,
    RevokePermissionsRequest,
    UnblockContextRequest,
)


@final
class AsyncTestDataEndpoints(AsyncBaseEndpoints):
    __test__ = False

    async def create_subject(self, body: CreateSubjectRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.CREATE_SUBJECT,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def delete_subject(self, body: DeleteSubjectRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.DELETE_SUBJECT,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def create_person(self, body: CreatePersonRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.CREATE_PERSON,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def delete_person(self, body: DeletePersonRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.DELETE_PERSON,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def grant_permissions(self, body: GrantPermissionsRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.GRANT_PERMISSIONS,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def revoke_permissions(self, body: RevokePermissionsRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.REVOKE_PERMISSIONS,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def enable_attachments(self, body: EnableAttachmentsRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.ENABLE_ATTACHMENTS,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def revoke_attachments(self, body: RevokeAttachmentsRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.REVOKE_ATTACHMENTS,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def block_context(self, body: BlockContextRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.BLOCK_CONTEXT,
            json=body.model_dump(mode="json", by_alias=True),
        )

    async def unblock_context(self, body: UnblockContextRequest) -> None:
        _ = await self._transport.post(
            path=routes.TestDataRoutes.UNBLOCK_CONTEXT,
            json=body.model_dump(mode="json", by_alias=True),
        )
