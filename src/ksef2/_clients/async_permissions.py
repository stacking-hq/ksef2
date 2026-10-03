"""Async permissions branch client."""

from typing import final

from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._domain.models.pagination import OffsetPaginationParams
from ksef2._domain.models.permissions import (
    AttachmentPermissionStatus,
    AuthorizationPermissionsQuery,
    AuthorizationPermissionsQueryResponse,
    AuthorizationPermissionType,
    AuthorizationSubjectIdentifierType,
    CertificateSubjectIdentifierType,
    EntityPermission,
    EntityPermissionsQuery,
    EntityPermissionsQueryResponse,
    EntityRolesResponse,
    EuEntityAdminContextIdentifierType,
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
    PersonalPermissionsQuery,
    PersonalPermissionsQueryResponse,
    PersonPermissionsQuery,
    PersonPermissionsQueryResponse,
    PersonPermissionScope,
    SubordinateEntityRolesQuery,
    SubordinateEntityRolesQueryResponse,
    SubunitIdentifierType,
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

    async def get_entity_roles(
        self,
        *,
        params: OffsetPaginationParams | None = None,
    ) -> EntityRolesResponse:
        """Fetch one page of roles assigned to the authenticated entity.

        Args:
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of roles assigned to the authenticated entity.
        """
        spec_resp = await self._get_eps.query_entity_roles(
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return entity_from_spec(spec_resp)

    async def query_authorizations(
        self,
        *,
        query: AuthorizationPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> AuthorizationPermissionsQueryResponse:
        """Fetch one page of authorization grants matching the provided filters.

        Args:
            query: Filters for the authorization grants.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of authorization grants.
        """
        spec_resp = await self._query_eps.query_authorizations_grants(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return entity_from_spec(spec_resp)

    async def query_entities(
        self,
        *,
        query: EntityPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> EntityPermissionsQueryResponse:
        """Fetch one page of entity permission grants matching the provided filters.

        Args:
            query: Filters for the entity permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of entity permissions.
        """
        spec_resp = await self._query_eps.query_entities_grants(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return entity_from_spec(spec_resp)

    async def query_eu_entities(
        self,
        *,
        query: EuEntityPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> EuEntityPermissionsQueryResponse:
        """Fetch one page of EU-entity permissions matching the provided filters.

        Args:
            query: Filters for the EU-entity permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of EU-entity permissions.
        """
        spec_resp = await self._query_eps.query_eu_entities_grants(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return eu_entity_from_spec(spec_resp)

    async def query_personal(
        self,
        *,
        query: PersonalPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> PersonalPermissionsQueryResponse:
        """Fetch one page of permissions held by the authenticated subject.

        Args:
            query: Filters for the permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of permissions held by the authenticated subject.
        """
        spec_resp = await self._query_eps.query_personal_grants(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return personal_from_spec(spec_resp)

    async def query_persons(
        self,
        *,
        query: PersonPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> PersonPermissionsQueryResponse:
        """Fetch one page of person permission grants matching the provided filters.

        Args:
            query: Filters for the person permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of person permissions.
        """
        spec_resp = await self._query_eps.query_persons_grants(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return person_from_spec(spec_resp)

    async def query_subordinate_entities(
        self,
        *,
        query: SubordinateEntityRolesQuery,
        params: OffsetPaginationParams | None = None,
    ) -> SubordinateEntityRolesQueryResponse:
        """Fetch one page of subordinate entity roles.

        Args:
            query: Filters for the subordinate entity roles.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of subordinate entity roles.
        """
        spec_resp = await self._query_eps.query_subordinate_entities_roles(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return subordinate_roles_from_spec(spec_resp)

    async def query_subunits(
        self,
        *,
        query: SubunitPermissionsQuery,
        params: OffsetPaginationParams | None = None,
    ) -> SubunitPermissionsQueryResponse:
        """Fetch one page of subunit permission grants.

        Args:
            query: Filters for the subunit permissions.
            params: Page size and offset; defaults are used when ``None``.

        Returns:
            One page of subunit permissions.
        """
        spec_resp = await self._query_eps.query_subunits_grants(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return subunit_from_spec(spec_resp)
