from datetime import date, datetime
from types import TracebackType
from typing import Self, final

import httpx

from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.testdata import (
    AuthContextIdentifier,
    BlockContextRequest,
    CreatePersonRequest,
    CreateSubjectRequest,
    DeletePersonRequest,
    DeleteSubjectRequest,
    EnableAttachmentsRequest,
    GrantPermissionsRequest,
    Identifier,
    Permission,
    RevokeAttachmentsRequest,
    RevokePermissionsRequest,
    SubjectType,
    SubUnit,
    UnblockContextRequest,
)
from ksef2.endpoints.async_testdata import AsyncTestDataEndpoints
from ksef2.infra.mappers.testdata import to_spec
from ksef2.logging import get_logger

logger = get_logger(__name__)


@final
class AsyncTestDataClient:
    """Async helper for TEST-only endpoints that seed and mutate sandbox data."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._endpoints = AsyncTestDataEndpoints(transport)

    async def create_subject(
        self,
        *,
        nip: str,
        subject_type: SubjectType,
        description: str,
        subunits: list[SubUnit] | None = None,
        created_date: datetime | None = None,
    ) -> None:
        request = CreateSubjectRequest(
            subject_nip=nip,
            subject_type=subject_type,
            description=description,
            subunits=subunits,
            created_date=created_date,
        )
        await self._endpoints.create_subject(to_spec(request))

    async def delete_subject(self, *, nip: str) -> None:
        await self._endpoints.delete_subject(
            to_spec(DeleteSubjectRequest(subject_nip=nip))
        )

    async def create_person(
        self,
        *,
        nip: str,
        pesel: str,
        description: str,
        is_bailiff: bool = False,
        is_deceased: bool = False,
        created_date: datetime | None = None,
    ) -> None:
        request = CreatePersonRequest(
            nip=nip,
            pesel=pesel,
            description=description,
            is_bailiff=is_bailiff,
            is_deceased=is_deceased,
            created_date=created_date,
        )
        await self._endpoints.create_person(to_spec(request))

    async def delete_person(self, *, nip: str) -> None:
        await self._endpoints.delete_person(to_spec(DeletePersonRequest(nip=nip)))

    async def grant_permissions(
        self,
        *,
        permissions: list[Permission],
        grant_to: Identifier,
        in_context_of: Identifier,
    ) -> None:
        request = GrantPermissionsRequest(
            permissions=permissions,
            grant_to=grant_to,
            in_context_of=in_context_of,
        )
        await self._endpoints.grant_permissions(to_spec(request))

    async def revoke_permissions(
        self, *, revoke_from: Identifier, in_context_of: Identifier
    ) -> None:
        request = RevokePermissionsRequest(
            revoke_from=revoke_from,
            in_context_of=in_context_of,
        )
        await self._endpoints.revoke_permissions(to_spec(request))

    async def enable_attachments(self, *, nip: str) -> None:
        await self._endpoints.enable_attachments(
            to_spec(EnableAttachmentsRequest(nip=nip))
        )

    async def revoke_attachments(
        self, *, nip: str, expected_end_date: date | None = None
    ) -> None:
        request = RevokeAttachmentsRequest(
            nip=nip,
            expected_end_date=expected_end_date,
        )
        await self._endpoints.revoke_attachments(to_spec(request))

    async def block_context(self, *, context: AuthContextIdentifier) -> None:
        await self._endpoints.block_context(
            to_spec(BlockContextRequest(context=context))
        )

    async def unblock_context(self, *, context: AuthContextIdentifier) -> None:
        await self._endpoints.unblock_context(
            to_spec(UnblockContextRequest(context=context))
        )

    def temporal(self) -> "AsyncTemporalTestData":
        return AsyncTemporalTestData(self)


@final
class AsyncTemporalTestData:
    """Async context manager that records testdata mutations and reverts them on exit."""

    def __init__(self, client: AsyncTestDataClient) -> None:
        self._client = client
        self._subjects: list[str] = []
        self._persons: list[str] = []
        self._permissions: list[tuple[Identifier, Identifier]] = []
        self._attachments: list[str] = []
        self._blocked_contexts: list[AuthContextIdentifier] = []

    async def __aenter__(self) -> Self:
        return self

    async def _cleanup_blocked_context(self, context: AuthContextIdentifier) -> None:
        try:
            await self._client.unblock_context(context=context)
        except (exceptions.KSeFException, httpx.HTTPError):
            logger.warning(
                "Failed to unblock context",
                context=context,
                exc_info=True,
            )

    async def _cleanup_attachment(self, nip: str) -> None:
        try:
            await self._client.revoke_attachments(nip=nip)
        except (exceptions.KSeFException, httpx.HTTPError):
            logger.warning(
                "Failed to revoke attachments",
                nip=nip,
                exc_info=True,
            )

    async def _cleanup_permission(
        self, in_context_of: Identifier, grant_to: Identifier
    ) -> None:
        try:
            await self._client.revoke_permissions(
                revoke_from=grant_to,
                in_context_of=in_context_of,
            )
        except (exceptions.KSeFException, httpx.HTTPError):
            logger.warning(
                "Failed to revoke permissions",
                in_context_of=in_context_of,
                grant_to=grant_to,
                exc_info=True,
            )

    async def _cleanup_person(self, nip: str) -> None:
        try:
            await self._client.delete_person(nip=nip)
        except (exceptions.KSeFException, httpx.HTTPError):
            logger.warning(
                "Failed to delete person",
                nip=nip,
                exc_info=True,
            )

    async def _cleanup_subject(self, nip: str) -> None:
        try:
            await self._client.delete_subject(nip=nip)
        except (exceptions.KSeFException, httpx.HTTPError):
            logger.warning(
                "Failed to delete subject",
                nip=nip,
                exc_info=True,
            )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        for context in reversed(self._blocked_contexts):
            await self._cleanup_blocked_context(context)
        for nip in reversed(self._attachments):
            await self._cleanup_attachment(nip)
        for in_context_of, grant_to in reversed(self._permissions):
            await self._cleanup_permission(in_context_of, grant_to)
        for nip in reversed(self._persons):
            await self._cleanup_person(nip)
        for nip in reversed(self._subjects):
            await self._cleanup_subject(nip)

    async def create_subject(
        self,
        *,
        nip: str,
        subject_type: SubjectType,
        description: str,
        subunits: list[SubUnit] | None = None,
        created_date: datetime | None = None,
    ) -> None:
        if nip not in self._subjects:
            self._subjects.append(nip)
        await self._client.create_subject(
            nip=nip,
            subject_type=subject_type,
            description=description,
            subunits=subunits,
            created_date=created_date,
        )

    async def delete_subject(self, *, nip: str) -> None:
        await self._client.delete_subject(nip=nip)
        if nip in self._subjects:
            self._subjects.remove(nip)

    async def create_person(
        self,
        *,
        nip: str,
        pesel: str,
        description: str,
        is_bailiff: bool = False,
        is_deceased: bool = False,
        created_date: datetime | None = None,
    ) -> None:
        if nip not in self._persons:
            self._persons.append(nip)
        await self._client.create_person(
            nip=nip,
            pesel=pesel,
            description=description,
            is_bailiff=is_bailiff,
            is_deceased=is_deceased,
            created_date=created_date,
        )

    async def delete_person(self, *, nip: str) -> None:
        await self._client.delete_person(nip=nip)
        if nip in self._persons:
            self._persons.remove(nip)

    async def grant_permissions(
        self,
        *,
        permissions: list[Permission],
        grant_to: Identifier,
        in_context_of: Identifier,
    ) -> None:
        key = (in_context_of, grant_to)
        if key not in self._permissions:
            self._permissions.append(key)
        await self._client.grant_permissions(
            permissions=permissions,
            grant_to=grant_to,
            in_context_of=in_context_of,
        )

    async def revoke_permissions(
        self, *, revoke_from: Identifier, in_context_of: Identifier
    ) -> None:
        await self._client.revoke_permissions(
            revoke_from=revoke_from,
            in_context_of=in_context_of,
        )
        key = (in_context_of, revoke_from)
        if key in self._permissions:
            self._permissions.remove(key)

    async def enable_attachments(self, *, nip: str) -> None:
        if nip not in self._attachments:
            self._attachments.append(nip)
        await self._client.enable_attachments(nip=nip)

    async def revoke_attachments(
        self, *, nip: str, expected_end_date: date | None = None
    ) -> None:
        await self._client.revoke_attachments(
            nip=nip,
            expected_end_date=expected_end_date,
        )
        if nip in self._attachments:
            self._attachments.remove(nip)

    async def block_context(self, *, context: AuthContextIdentifier) -> None:
        if context not in self._blocked_contexts:
            self._blocked_contexts.append(context)
        await self._client.block_context(context=context)

    async def unblock_context(self, *, context: AuthContextIdentifier) -> None:
        await self._client.unblock_context(context=context)
        if context in self._blocked_contexts:
            self._blocked_contexts.remove(context)
