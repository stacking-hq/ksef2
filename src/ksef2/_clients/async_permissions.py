"""Async permissions branch client."""

from collections.abc import AsyncGenerator, Awaitable, Callable, Coroutine, Sequence
from typing import final

from typing_extensions import deprecated

from ksef2._clients._async_pager import AsyncPager
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.pagination import OffsetPaginationParams
from ksef2._domain.models.permissions import (
    AttachmentPermissionStatus,
    AuthorizationGrantDetail,
    AuthorizationPermissionsQuery,
    AuthorizationPermissionsQueryResponse,
    AuthorizationPermissionType,
    AuthorizationSubjectIdentifierType,
    CertificateSubjectIdentifierType,
    EntityPermission,
    EntityPermissionDetail,
    EntityPermissionsQuery,
    EntityPermissionsQueryResponse,
    EntityRole,
    EntityRolesResponse,
    EuEntityAdminContextIdentifierType,
    EuEntityPermission,
    EuEntityPermissionsQuery,
    EuEntityPermissionsQueryResponse,
    EuEntityPermissionType,
    GrantAuthorizationPermissionsRequest,
    GrantEntityPermissionsRequest,
    GrantEuEntityAdministrationRequest,
    GrantEuEntityPermissionsRequest,
    GrantIndirectPermissionsRequest,
    GrantPermissionsResponse,
    GrantPersonPermissionsRequest,
    GrantSubunitPermissionsRequest,
    IndirectPermissionType,
    IndirectTargetIdentifierType,
    PermissionOperationStatusResponse,
    PersonalPermissionDetail,
    PersonalPermissionsQuery,
    PersonalPermissionsQueryResponse,
    PersonPermissionDetail,
    PersonPermissionsQuery,
    PersonPermissionsQueryResponse,
    PersonPermissionScope,
    SubordinateEntityRoleDetail,
    SubordinateEntityRolesQuery,
    SubordinateEntityRolesQueryResponse,
    SubunitIdentifierType,
    SubunitPermission,
    SubunitPermissionsQuery,
    SubunitPermissionsQueryResponse,
)
from ksef2._endpoints.async_permissions import (
    AsyncGetPermissionsEndpoints,
    AsyncPermissionsGrantEndpoints,
    AsyncQueryPermissionsEndpoints,
    AsyncRevokePermissionsEndpoints,
)
from ksef2._infra.mappers.permissions import (
    entity_from_spec,
    eu_entity_from_spec,
    grant_from_spec,
    grant_to_spec,
    person_from_spec,
    personal_from_spec,
    query_to_spec,
    subordinate_roles_from_spec,
    subunit_from_spec,
)


def _offset_pager[PageT, ItemT](
    fetch: Callable[[OffsetPaginationParams], Awaitable[PageT]],
    items: Callable[[PageT], Sequence[ItemT]],
    has_more: Callable[[PageT], bool],
    params: OffsetPaginationParams | None,
) -> AsyncPager[ItemT]:
    """Build a pager over an offset-paged permissions query."""

    async def _pages() -> AsyncGenerator[list[ItemT], None]:
        current_params = params or OffsetPaginationParams()
        while True:
            page = await fetch(current_params)
            yield list(items(page))
            if not has_more(page):
                break
            current_params = current_params.next_page()

    return AsyncPager(_pages)


@final
class AsyncPermissionsClient:
    """Async high-level API for permission grants, revocations, and queries.

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
        self._grant_eps = AsyncPermissionsGrantEndpoints(transport)
        self._revoke_eps = AsyncRevokePermissionsEndpoints(transport)
        self._query_eps = AsyncQueryPermissionsEndpoints(transport)
        self._get_eps = AsyncGetPermissionsEndpoints(transport)

    async def grant_person(
        self,
        *,
        subject_type: CertificateSubjectIdentifierType,
        subject_value: str,
        permissions: list[PersonPermissionScope],
        description: str,
        first_name: str,
        last_name: str,
    ) -> GrantPermissionsResponse:
        """Grant person-scoped permissions to a subject identifier.

        Args:
            subject_type: Kind of identifier in ``subject_value`` (``nip``, ``pesel`` or ``fingerprint``).
            subject_value: Identifier of the person receiving the permissions.
            permissions: Permission scopes to grant; at least one is required.
            description: Free-text reason for the grant.
            first_name: First name of the person receiving the permissions.
            last_name: Last name of the person receiving the permissions.

        Returns:
            The reference of the asynchronous grant operation; poll ``get_operation_status()`` for the result.
        """
        body = grant_to_spec(
            GrantPersonPermissionsRequest(
                subject_type=subject_type,
                subject_value=subject_value,
                permissions=permissions,
                description=description,
                first_name=first_name,
                last_name=last_name,
            )
        )
        return grant_from_spec(await self._grant_eps.grant_person(request=body))

    async def grant_entity(
        self,
        *,
        subject_value: str,
        permissions: list[EntityPermission],
        description: str,
        entity_name: str,
    ) -> GrantPermissionsResponse:
        """Grant entity permissions to a NIP-identified entity.

        Args:
            subject_value: NIP of the entity receiving the permissions.
            permissions: Permissions to grant, each with its delegation flag.
            description: Free-text reason for the grant.
            entity_name: Full name of the entity receiving the permissions.

        Returns:
            The reference of the asynchronous grant operation; poll ``get_operation_status()`` for the result.
        """
        body = grant_to_spec(
            GrantEntityPermissionsRequest(
                subject_value=subject_value,
                permissions=permissions,
                description=description,
                entity_name=entity_name,
            )
        )
        return grant_from_spec(await self._grant_eps.grant_entity(request=body))

    async def grant_authorization(
        self,
        *,
        subject_type: AuthorizationSubjectIdentifierType,
        subject_value: str,
        permission: AuthorizationPermissionType,
        description: str,
        entity_name: str,
    ) -> GrantPermissionsResponse:
        """Grant an authorization permission such as self-invoicing.

        Args:
            subject_type: Kind of identifier in ``subject_value`` (``nip`` or ``peppol_id``).
            subject_value: Identifier of the entity being authorized (NIP or Peppol ID).
            permission: Authorization scope to grant, for example ``self_invoicing``.
            description: Free-text reason for the grant.
            entity_name: Full name of the entity being authorized.

        Returns:
            The reference of the asynchronous grant operation; poll ``get_operation_status()`` for the result.
        """
        body = grant_to_spec(
            GrantAuthorizationPermissionsRequest(
                subject_type=subject_type,
                subject_value=subject_value,
                permission=permission,
                description=description,
                entity_name=entity_name,
            )
        )
        return grant_from_spec(await self._grant_eps.grant_authorization(request=body))

    async def grant_indirect(
        self,
        *,
        subject_type: CertificateSubjectIdentifierType,
        subject_value: str,
        permissions: list[IndirectPermissionType],
        description: str,
        first_name: str,
        last_name: str,
        target_type: IndirectTargetIdentifierType | None = None,
        target_value: str | None = None,
    ) -> GrantPermissionsResponse:
        """Grant indirect permissions, optionally limited to a target entity.

        Args:
            subject_type: Kind of identifier in ``subject_value`` (``nip``, ``pesel`` or ``fingerprint``).
            subject_value: Identifier of the person receiving the indirect permissions.
            permissions: Indirect permission scopes to grant; at least one is required.
            description: Free-text reason for the grant.
            first_name: First name of the person receiving the permissions.
            last_name: Last name of the person receiving the permissions.
            target_type: Kind of identifier in ``target_value``; ``None`` or ``all_partners`` scopes the grant to every partner.
            target_value: Identifier of the partner context the grant is limited to; ``None`` when the target is all partners.

        Returns:
            The reference of the asynchronous grant operation; poll ``get_operation_status()`` for the result.
        """
        body = grant_to_spec(
            GrantIndirectPermissionsRequest(
                subject_type=subject_type,
                subject_value=subject_value,
                permissions=permissions,
                description=description,
                first_name=first_name,
                last_name=last_name,
                target_type=target_type,
                target_value=target_value,
            )
        )
        return grant_from_spec(await self._grant_eps.grant_indirect(request=body))

    async def grant_subunit(
        self,
        *,
        subject_type: CertificateSubjectIdentifierType,
        subject_value: str,
        context_type: SubunitIdentifierType,
        context_value: str,
        description: str,
        first_name: str,
        last_name: str,
        subunit_name: str | None = None,
    ) -> GrantPermissionsResponse:
        """Grant permissions within a subunit context.

        Args:
            subject_type: Kind of identifier in ``subject_value`` (``nip``, ``pesel`` or ``fingerprint``).
            subject_value: Identifier of the person receiving the permissions.
            context_type: Kind of identifier in ``context_value`` (``nip`` or ``internal_id``).
            context_value: Identifier of the subunit context the permissions apply to.
            description: Free-text reason for the grant.
            first_name: First name of the person receiving the permissions.
            last_name: Last name of the person receiving the permissions.
            subunit_name: Display name of the subunit; optional.

        Returns:
            The reference of the asynchronous grant operation; poll ``get_operation_status()`` for the result.
        """
        body = grant_to_spec(
            GrantSubunitPermissionsRequest(
                subject_type=subject_type,
                subject_value=subject_value,
                context_type=context_type,
                context_value=context_value,
                description=description,
                first_name=first_name,
                last_name=last_name,
                subunit_name=subunit_name,
            )
        )
        return grant_from_spec(await self._grant_eps.grant_subunit(request=body))

    async def grant_eu_entity(
        self,
        *,
        subject_value: str,
        permissions: list[EuEntityPermissionType],
        description: str,
    ) -> GrantPermissionsResponse:
        """Grant permissions to an EU entity identified by fingerprint data.

        Args:
            subject_value: Fingerprint of the certificate of the person receiving the permissions.
            permissions: EU-entity permission scopes to grant.
            description: Free-text reason for the grant.

        Returns:
            The reference of the asynchronous grant operation; poll ``get_operation_status()`` for the result.
        """
        body = grant_to_spec(
            GrantEuEntityPermissionsRequest(
                subject_value=subject_value,
                permissions=permissions,
                description=description,
            )
        )
        return grant_from_spec(await self._grant_eps.grant_eu_entity(request=body))

    async def grant_eu_entity_administration(
        self,
        *,
        subject_value: str,
        context_type: EuEntityAdminContextIdentifierType,
        context_value: str,
        description: str,
        eu_entity_name: str,
    ) -> GrantPermissionsResponse:
        """Grant administration rights for an EU entity in a VAT UE context.

        Args:
            subject_value: Fingerprint of the certificate of the person receiving administration rights.
            context_type: Kind of identifier in ``context_value``; always ``nip_vat_ue``.
            context_value: NIP-VAT UE identifier of the EU entity.
            description: Free-text reason for the grant.
            eu_entity_name: Full name of the EU entity.

        Returns:
            The reference of the asynchronous grant operation; poll ``get_operation_status()`` for the result.
        """
        body = grant_to_spec(
            GrantEuEntityAdministrationRequest(
                subject_value=subject_value,
                context_type=context_type,
                context_value=context_value,
                description=description,
                eu_entity_name=eu_entity_name,
            )
        )
        return grant_from_spec(
            await self._grant_eps.grant_administered_eu_entity(request=body)
        )

    async def revoke_authorization(
        self,
        *,
        permission_id: str,
    ) -> GrantPermissionsResponse:
        """Revoke an authorization permission by permission id.

        Args:
            permission_id: Identifier of the authorization permission, from a query result.

        Returns:
            The reference of the asynchronous revoke operation; poll ``get_operation_status()`` for the result.
        """
        return grant_from_spec(
            await self._revoke_eps.revoke_authorization(
                permission_id=permission_id,
            )
        )

    async def revoke_common(
        self,
        *,
        permission_id: str,
    ) -> GrantPermissionsResponse:
        """Revoke a non-authorization permission by permission id.

        Args:
            permission_id: Identifier of the permission, from a query result.

        Returns:
            The reference of the asynchronous revoke operation; poll ``get_operation_status()`` for the result.
        """
        return grant_from_spec(
            await self._revoke_eps.revoke_person(
                permission_id=permission_id,
            )
        )

    async def get_attachment_permission_status(self) -> AttachmentPermissionStatus:
        """Return whether attachments are currently allowed for the subject.

        Returns:
            Whether attachments are currently allowed for the subject.
        """
        return grant_from_spec(await self._query_eps.query_attachments_status())

    async def get_operation_status(
        self,
        *,
        reference_number: str,
    ) -> PermissionOperationStatusResponse:
        """Fetch the status of an asynchronous permission operation.

        Args:
            reference_number: Reference number returned by a grant or revoke call.

        Returns:
            The operation status; ``status.code`` is ``200`` once it has completed successfully.
        """
        return grant_from_spec(
            await self._get_eps.query_operation_status(
                reference_number=reference_number,
            )
        )

    async def _entity_roles(
        self, params: OffsetPaginationParams
    ) -> EntityRolesResponse:
        return entity_from_spec(
            await self._get_eps.query_entity_roles(**params.to_query_params())
        )

    async def _authorizations(
        self, query: AuthorizationPermissionsQuery, params: OffsetPaginationParams
    ) -> AuthorizationPermissionsQueryResponse:
        return entity_from_spec(
            await self._query_eps.query_authorizations_grants(
                request=query_to_spec(query), **params.to_query_params()
            )
        )

    async def _entities(
        self, query: EntityPermissionsQuery, params: OffsetPaginationParams
    ) -> EntityPermissionsQueryResponse:
        return entity_from_spec(
            await self._query_eps.query_entities_grants(
                request=query_to_spec(query), **params.to_query_params()
            )
        )

    async def _eu_entities(
        self, query: EuEntityPermissionsQuery, params: OffsetPaginationParams
    ) -> EuEntityPermissionsQueryResponse:
        return eu_entity_from_spec(
            await self._query_eps.query_eu_entities_grants(
                request=query_to_spec(query), **params.to_query_params()
            )
        )

    async def _personal(
        self, query: PersonalPermissionsQuery, params: OffsetPaginationParams
    ) -> PersonalPermissionsQueryResponse:
        return personal_from_spec(
            await self._query_eps.query_personal_grants(
                request=query_to_spec(query), **params.to_query_params()
            )
        )

    async def _persons(
        self, query: PersonPermissionsQuery, params: OffsetPaginationParams
    ) -> PersonPermissionsQueryResponse:
        return person_from_spec(
            await self._query_eps.query_persons_grants(
                request=query_to_spec(query), **params.to_query_params()
            )
        )

    async def _subordinate_entities(
        self, query: SubordinateEntityRolesQuery, params: OffsetPaginationParams
    ) -> SubordinateEntityRolesQueryResponse:
        return subordinate_roles_from_spec(
            await self._query_eps.query_subordinate_entities_roles(
                request=query_to_spec(query), **params.to_query_params()
            )
        )

    async def _subunits(
        self, query: SubunitPermissionsQuery, params: OffsetPaginationParams
    ) -> SubunitPermissionsQueryResponse:
        return subunit_from_spec(
            await self._query_eps.query_subunits_grants(
                request=query_to_spec(query), **params.to_query_params()
            )
        )

    @deprecated(
        "`get_entity_roles()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_entity_roles()` instead."
    )
    def get_entity_roles(
        self,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, EntityRolesResponse]:
        """Deprecated: fetch one page of roles assigned to the authenticated entity.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_entity_roles()`` instead; ``first_page()`` fetches one page.

        Args:
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of roles assigned to the authenticated entity.
        """
        return self._entity_roles(params or OffsetPaginationParams())

    @deprecated(
        "`query_authorizations()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_authorizations()` instead."
    )
    def query_authorizations(
        self,
        *,
        query: AuthorizationPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, AuthorizationPermissionsQueryResponse]:
        """Deprecated: fetch one page of authorization grants matching the provided filters.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_authorizations()`` instead; ``first_page()`` fetches one page.

        Args:
            query: Filters for the authorization grants.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of authorization grants.
        """
        return self._authorizations(query, params or OffsetPaginationParams())

    @deprecated(
        "`query_entities()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_entities()` instead."
    )
    def query_entities(
        self,
        *,
        query: EntityPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, EntityPermissionsQueryResponse]:
        """Deprecated: fetch one page of entity permission grants matching the provided filters.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_entities()`` instead; ``first_page()`` fetches one page.

        Args:
            query: Filters for the entity permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of entity permissions.
        """
        return self._entities(query, params or OffsetPaginationParams())

    @deprecated(
        "`query_eu_entities()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_eu_entities()` instead."
    )
    def query_eu_entities(
        self,
        *,
        query: EuEntityPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, EuEntityPermissionsQueryResponse]:
        """Deprecated: fetch one page of EU-entity permissions matching the provided filters.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_eu_entities()`` instead; ``first_page()`` fetches one page.

        Args:
            query: Filters for the EU-entity permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of EU-entity permissions.
        """
        return self._eu_entities(query, params or OffsetPaginationParams())

    @deprecated(
        "`query_personal()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_personal()` instead."
    )
    def query_personal(
        self,
        *,
        query: PersonalPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, PersonalPermissionsQueryResponse]:
        """Deprecated: fetch one page of permissions held by the authenticated subject.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_personal()`` instead; ``first_page()`` fetches one page.

        Args:
            query: Filters for the permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of permissions held by the authenticated subject.
        """
        return self._personal(query, params or OffsetPaginationParams())

    @deprecated(
        "`query_persons()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_persons()` instead."
    )
    def query_persons(
        self,
        *,
        query: PersonPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, PersonPermissionsQueryResponse]:
        """Deprecated: fetch one page of person permission grants matching the provided filters.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_persons()`` instead; ``first_page()`` fetches one page.

        Args:
            query: Filters for the person permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of person permissions.
        """
        return self._persons(query, params or OffsetPaginationParams())

    @deprecated(
        "`query_subordinate_entities()` is deprecated and will be removed in "
        "ksef2 1.10.0; use `list_subordinate_entities()` instead."
    )
    def query_subordinate_entities(
        self,
        *,
        query: SubordinateEntityRolesQuery,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, SubordinateEntityRolesQueryResponse]:
        """Deprecated: fetch one page of subordinate entity roles.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_subordinate_entities()`` instead; ``first_page()`` fetches one page.

        Args:
            query: Filters for the subordinate entity roles.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of subordinate entity roles.
        """
        return self._subordinate_entities(query, params or OffsetPaginationParams())

    @deprecated(
        "`query_subunits()` is deprecated and will be removed in ksef2 1.10.0; "
        "use `list_subunits()` instead."
    )
    def query_subunits(
        self,
        *,
        query: SubunitPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> Coroutine[None, None, SubunitPermissionsQueryResponse]:
        """Deprecated: fetch one page of subunit permission grants.

        Deprecated:
            Will be removed in ksef2 1.10.0. Use ``list_subunits()`` instead; ``first_page()`` fetches one page.

        Args:
            query: Filters for the subunit permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of subunit permissions.
        """
        return self._subunits(query, params or OffsetPaginationParams())

    def list_entity_roles(
        self, *, params: OffsetPaginationParams | None = None
    ) -> AsyncPager[EntityRole]:
        """List the roles assigned to the authenticated entity.

        Nothing is requested until the result is consumed. Iterate it for every
        role, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the roles assigned to the authenticated entity.

        Example:
            ```python
            async for role in auth.permissions.list_entity_roles():
                print(role.role)
            ```
        """
        return _offset_pager(
            self._entity_roles,
            lambda page: page.roles,
            lambda page: page.has_more,
            params,
        )

    def list_authorizations(
        self,
        query: AuthorizationPermissionsQuery,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncPager[AuthorizationGrantDetail]:
        """List the authorization grants matching the provided filters.

        Nothing is requested until the result is consumed. Iterate it for every
        grant, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            query: Filters for the authorization grants.
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the authorization grants.

        Example:
            ```python
            async for grant in auth.permissions.list_authorizations(query):
                print(grant.id)
            ```
        """
        return _offset_pager(
            lambda page_params: self._authorizations(query, page_params),
            lambda page: page.authorization_grants,
            lambda page: page.has_more,
            params,
        )

    def list_entities(
        self,
        query: EntityPermissionsQuery,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncPager[EntityPermissionDetail]:
        """List the entity permission grants matching the provided filters.

        Nothing is requested until the result is consumed. Iterate it for every
        grant, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            query: Filters for the entity permissions.
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the entity permissions.

        Example:
            ```python
            async for permission in auth.permissions.list_entities(query):
                print(permission.id)
            ```
        """
        return _offset_pager(
            lambda page_params: self._entities(query, page_params),
            lambda page: page.permissions,
            lambda page: page.has_more,
            params,
        )

    def list_eu_entities(
        self,
        query: EuEntityPermissionsQuery,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncPager[EuEntityPermission]:
        """List the EU-entity permissions matching the provided filters.

        Nothing is requested until the result is consumed. Iterate it for every
        permission, call ``pages()`` for page-sized lists or ``first_page()`` for
        one request only.

        Args:
            query: Filters for the EU-entity permissions.
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the EU-entity permissions.

        Example:
            ```python
            async for permission in auth.permissions.list_eu_entities(query):
                print(permission.id)
            ```
        """
        return _offset_pager(
            lambda page_params: self._eu_entities(query, page_params),
            lambda page: page.permissions,
            lambda page: page.has_more,
            params,
        )

    def list_personal(
        self,
        query: PersonalPermissionsQuery,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncPager[PersonalPermissionDetail]:
        """List the permissions held by the authenticated subject.

        Nothing is requested until the result is consumed. Iterate it for every
        permission, call ``pages()`` for page-sized lists or ``first_page()`` for
        one request only.

        Args:
            query: Filters for the permissions.
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the permissions held by the authenticated subject.

        Example:
            ```python
            async for permission in auth.permissions.list_personal(query):
                print(permission.id)
            ```
        """
        return _offset_pager(
            lambda page_params: self._personal(query, page_params),
            lambda page: page.permissions,
            lambda page: page.has_more,
            params,
        )

    def list_persons(
        self,
        query: PersonPermissionsQuery,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncPager[PersonPermissionDetail]:
        """List the person permission grants matching the provided filters.

        Nothing is requested until the result is consumed. Iterate it for every
        grant, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            query: Filters for the person permissions.
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the person permissions.

        Example:
            ```python
            async for permission in auth.permissions.list_persons(query):
                print(permission.id)
            ```
        """
        return _offset_pager(
            lambda page_params: self._persons(query, page_params),
            lambda page: page.permissions,
            lambda page: page.has_more,
            params,
        )

    def list_subordinate_entities(
        self,
        query: SubordinateEntityRolesQuery,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncPager[SubordinateEntityRoleDetail]:
        """List the subordinate entity roles matching the provided filters.

        Nothing is requested until the result is consumed. Iterate it for every
        role, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            query: Filters for the subordinate entity roles.
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the subordinate entity roles.

        Example:
            ```python
            async for role in auth.permissions.list_subordinate_entities(query):
                print(role.role)
            ```
        """
        return _offset_pager(
            lambda page_params: self._subordinate_entities(query, page_params),
            lambda page: page.roles,
            lambda page: page.has_more,
            params,
        )

    def list_subunits(
        self,
        query: SubunitPermissionsQuery,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncPager[SubunitPermission]:
        """List the subunit permission grants matching the provided filters.

        Nothing is requested until the result is consumed. Iterate it for every
        grant, call ``pages()`` for page-sized lists or ``first_page()`` for one
        request only.

        Args:
            query: Filters for the subunit permissions.
            params: Page size and offset of the first page; defaults are used when ``None``.

        Returns:
            A paging object over the subunit permissions.

        Example:
            ```python
            async for permission in auth.permissions.list_subunits(query):
                print(permission.id)
            ```
        """
        return _offset_pager(
            lambda page_params: self._subunits(query, page_params),
            lambda page: page.permissions,
            lambda page: page.has_more,
            params,
        )
