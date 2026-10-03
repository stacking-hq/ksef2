"""Async TEST data branch client and cleanup helpers."""

from datetime import date, datetime
from types import TracebackType
from typing import Self, final

import httpx

from ksef2._core import exceptions
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.testdata import (
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
    UpdateCertificateRequest,
)
from ksef2._endpoints.async_testdata import AsyncTestDataEndpoints
from ksef2._infra.mappers.testdata import to_spec
from ksef2._logging import get_logger

logger = get_logger(__name__)


@final
class AsyncTestDataClient:
    """Async helper for TEST-only endpoints that seed and mutate sandbox data.

    Catch ``KSeFException`` for SDK-classified failures raised by this branch,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(self, transport: AsyncMiddleware) -> None:
        """Create the client.

        Args:
            transport: Middleware chain used for requests to KSeF.
        """
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
        """Create a test subject with optional subunits.

        Args:
            nip: NIP of the subject to create.
            subject_type: Kind of subject, such as an enforcement authority or a VAT group.
            description: Description of the subject.
            subunits: Subunits to create with the subject; ``None`` for none.
            created_date: Creation date to record for the subject; ``None`` for now.
        """
        request = CreateSubjectRequest(
            subject_nip=nip,
            subject_type=subject_type,
            description=description,
            subunits=subunits,
            created_date=created_date,
        )
        await self._endpoints.create_subject(to_spec(request))

    async def delete_subject(self, *, nip: str) -> None:
        """Delete a test subject by NIP.

        Args:
            nip: NIP of the subject to delete.
        """
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
        """Create a test person in the chosen subject.

        Args:
            nip: NIP of the person.
            pesel: PESEL of the person.
            description: Description of the person.
            is_bailiff: Whether the person is a bailiff.
            is_deceased: Whether the person is marked as deceased.
            created_date: Creation date to record for the person; ``None`` for now.
        """
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
        """Delete a test person by subject NIP.

        Args:
            nip: NIP of the person to delete.
        """
        await self._endpoints.delete_person(to_spec(DeletePersonRequest(nip=nip)))

    async def grant_permissions(
        self,
        *,
        permissions: list[Permission],
        grant_to: Identifier,
        in_context_of: Identifier,
    ) -> None:
        """Grant test permissions in a chosen context.

        Args:
            permissions: Permissions to grant.
            grant_to: Identifier of the subject receiving the permissions.
            in_context_of: Identifier of the context in which the permissions apply.
        """
        request = GrantPermissionsRequest(
            permissions=permissions,
            grant_to=grant_to,
            in_context_of=in_context_of,
        )
        await self._endpoints.grant_permissions(to_spec(request))

    async def revoke_permissions(
        self, *, revoke_from: Identifier, in_context_of: Identifier
    ) -> None:
        """Revoke test permissions in a chosen context.

        Args:
            revoke_from: Identifier of the subject losing the permissions.
            in_context_of: Identifier of the context from which the permissions are revoked.
        """
        request = RevokePermissionsRequest(
            revoke_from=revoke_from,
            in_context_of=in_context_of,
        )
        await self._endpoints.revoke_permissions(to_spec(request))

    async def enable_attachments(self, *, nip: str) -> None:
        """Enable invoice attachments for a test subject.

        Args:
            nip: NIP of the subject to enable attachments for.
        """
        await self._endpoints.enable_attachments(
            to_spec(EnableAttachmentsRequest(nip=nip))
        )

    async def revoke_attachments(
        self, *, nip: str, expected_end_date: date | None = None
    ) -> None:
        """Revoke attachment permissions, optionally effective on a given date.

        Args:
            nip: NIP of the subject to revoke attachments for.
            expected_end_date: Date on which attachment permission should end; ``None`` to revoke immediately.
        """
        request = RevokeAttachmentsRequest(
            nip=nip,
            expected_end_date=expected_end_date,
        )
        await self._endpoints.revoke_attachments(to_spec(request))

    async def block_context(self, *, context: AuthContextIdentifier) -> None:
        """Block authentication for a specific test context.

        Args:
            context: Authentication context to block.
        """
        await self._endpoints.block_context(
            to_spec(BlockContextRequest(context=context))
        )

    async def unblock_context(self, *, context: AuthContextIdentifier) -> None:
        """Unblock authentication for a specific test context.

        Args:
            context: Authentication context to unblock.
        """
        await self._endpoints.unblock_context(
            to_spec(UnblockContextRequest(context=context))
        )

    async def update_certificate_valid_to(
        self,
        *,
        serial_number: str,
        valid_to: datetime,
    ) -> None:
        """Shorten the validity of a certificate in the TEST environment.

        Args:
            serial_number: Serial number of the certificate to shorten.
            valid_to: New, earlier end of the certificate validity period.
        """
        request = UpdateCertificateRequest(valid_to=valid_to)
        await self._endpoints.update_certificate(
            serial_number=serial_number,
            body=to_spec(request),
        )

    def temporal(self) -> "AsyncTemporalTestData":
        """Return a context manager that automatically cleans up created test data.

        Returns:
            A context manager that automatically cleans up created test data.
        """
        return AsyncTemporalTestData(self)


@final
class AsyncTemporalTestData:
    """Async context manager that records testdata mutations and reverts them on exit.

    Cleanup failures are logged and suppressed. Direct mutation methods expose
    the same catch contract as the parent test-data branch.

    Raises:
        KSeFApiError: If KSeF returns an API error response during direct mutations.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(self, client: AsyncTestDataClient) -> None:
        """Create the helper.

        Args:
            client: Test-data client the operations are delegated to.
        """
        self._client = client
        self._subjects: list[str] = []
        self._persons: list[str] = []
        self._permissions: list[tuple[Identifier, Identifier]] = []
        self._attachments: list[str] = []
        self._blocked_contexts: list[AuthContextIdentifier] = []

    async def __aenter__(self) -> Self:
        """Return the helper for use in a ``with`` block."""
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
        """Best-effort cleanup of tracked changes in reverse creation order."""
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
        """Create a TEST subject and register it for context-manager cleanup.

        Args:
            nip: NIP of the subject to create.
            subject_type: Kind of subject, such as an enforcement authority or a VAT group.
            description: Description of the subject.
            subunits: Subunits to create with the subject; ``None`` for none.
            created_date: Creation date to record for the subject; ``None`` for now.
        """
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
        """Delete a TEST subject and remove it from cleanup tracking.

        Args:
            nip: NIP of the subject to delete.
        """
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
        """Create a TEST person and register it for context-manager cleanup.

        Args:
            nip: NIP of the person.
            pesel: PESEL of the person.
            description: Description of the person.
            is_bailiff: Whether the person is a bailiff.
            is_deceased: Whether the person is marked as deceased.
            created_date: Creation date to record for the person; ``None`` for now.
        """
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
        """Delete a TEST person and remove it from cleanup tracking.

        Args:
            nip: NIP of the person to delete.
        """
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
        """Grant TEST permissions and register them for cleanup.

        Args:
            permissions: Permissions to grant.
            grant_to: Identifier of the subject receiving the permissions.
            in_context_of: Identifier of the context in which the permissions apply.
        """
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
        """Revoke TEST permissions and remove them from cleanup tracking.

        Args:
            revoke_from: Identifier of the subject losing the permissions.
            in_context_of: Identifier of the context from which the permissions are revoked.
        """
        await self._client.revoke_permissions(
            revoke_from=revoke_from,
            in_context_of=in_context_of,
        )
        key = (in_context_of, revoke_from)
        if key in self._permissions:
            self._permissions.remove(key)

    async def enable_attachments(self, *, nip: str) -> None:
        """Enable TEST attachments and register the context for cleanup.

        Args:
            nip: NIP of the subject to enable attachments for.
        """
        if nip not in self._attachments:
            self._attachments.append(nip)
        await self._client.enable_attachments(nip=nip)

    async def revoke_attachments(
        self, *, nip: str, expected_end_date: date | None = None
    ) -> None:
        """Revoke TEST attachment access and remove it from cleanup tracking.

        Args:
            nip: NIP of the subject to revoke attachments for.
            expected_end_date: Date on which attachment permission should end; ``None`` to revoke immediately.
        """
        await self._client.revoke_attachments(
            nip=nip,
            expected_end_date=expected_end_date,
        )
        if nip in self._attachments:
            self._attachments.remove(nip)

    async def block_context(self, *, context: AuthContextIdentifier) -> None:
        """Block a TEST context and register it for cleanup.

        Args:
            context: Authentication context to block.
        """
        if context not in self._blocked_contexts:
            self._blocked_contexts.append(context)
        await self._client.block_context(context=context)

    async def unblock_context(self, *, context: AuthContextIdentifier) -> None:
        """Unblock a TEST context and remove it from cleanup tracking.

        Args:
            context: Authentication context to unblock.
        """
        await self._client.unblock_context(context=context)
        if context in self._blocked_contexts:
            self._blocked_contexts.remove(context)
