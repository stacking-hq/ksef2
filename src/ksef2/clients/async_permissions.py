from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.pagination import OffsetPaginationParams
from ksef2.domain.models.permissions import (
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
from ksef2.endpoints.async_permissions import (
    AsyncGetPermissionsEndpoints,
    AsyncPermissionsGrantEndpoints,
    AsyncQueryPermissionsEndpoints,
    AsyncRevokePermissionsEndpoints,
)
from ksef2.infra.mappers.permissions import (
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
    """Async high-level API for permission grants, revocations, and queries."""

    def __init__(self, transport: AsyncMiddleware) -> None:
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
        return grant_from_spec(
            await self._revoke_eps.revoke_person(
                permission_id=permission_id,
            )
        )

    async def get_attachment_permission_status(self) -> AttachmentPermissionStatus:
        return grant_from_spec(await self._query_eps.query_attachments_status())

    async def get_operation_status(
        self,
        *,
        reference_number: str,
    ) -> PermissionOperationStatusResponse:
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
        spec_resp = await self._query_eps.query_subunits_grants(
            request=query_to_spec(query),
            **params.to_query_params()
            if params
            else OffsetPaginationParams().to_query_params(),
        )
        return subunit_from_spec(spec_resp)
