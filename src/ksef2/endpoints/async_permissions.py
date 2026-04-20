from typing import Unpack, final

from ksef2.core import routes
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.endpoints.base import OffsetPaginationQueryParams
from ksef2.infra.schema.api import spec


@final
class AsyncPermissionsGrantEndpoints(AsyncBaseEndpoints):
    async def grant_person(
        self,
        request: spec.PersonPermissionsGrantRequest,
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.post(
                path=routes.GrantPermissionsRoutes.GRANT_PERSON,
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.PermissionsOperationResponse,
        )

    async def grant_entity(
        self, request: spec.EntityPermissionsGrantRequest
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.post(
                path=routes.GrantPermissionsRoutes.GRANT_ENTITY,
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.PermissionsOperationResponse,
        )

    async def grant_authorization(
        self, request: spec.EntityAuthorizationPermissionsGrantRequest
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.post(
                path=routes.GrantPermissionsRoutes.GRANT_AUTHORIZATION,
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.PermissionsOperationResponse,
        )

    async def grant_indirect(
        self, request: spec.IndirectPermissionsGrantRequest
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.post(
                path=routes.GrantPermissionsRoutes.GRANT_INDIRECT,
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.PermissionsOperationResponse,
        )

    async def grant_subunit(
        self, request: spec.SubunitPermissionsGrantRequest
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.post(
                path=routes.GrantPermissionsRoutes.GRANT_SUBUNITS,
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.PermissionsOperationResponse,
        )

    async def grant_administered_eu_entity(
        self, request: spec.EuEntityAdministrationPermissionsGrantRequest
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.post(
                path=routes.GrantPermissionsRoutes.GRANT_ADMINISTERED_EU_ENTITY,
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.PermissionsOperationResponse,
        )

    async def grant_eu_entity(
        self, request: spec.EuEntityPermissionsGrantRequest
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.post(
                path=routes.GrantPermissionsRoutes.GRANT_EU_ENTITY,
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.PermissionsOperationResponse,
        )


@final
class AsyncRevokePermissionsEndpoints(AsyncBaseEndpoints):
    async def revoke_person(
        self, permission_id: str
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.delete(
                path=routes.RevokePermissionsRoutes.REVOKE_PERMISSION.format(
                    permissionId=permission_id
                ),
            ),
            spec.PermissionsOperationResponse,
        )

    async def revoke_authorization(
        self, permission_id: str
    ) -> spec.PermissionsOperationResponse:
        return self._parse(
            await self._transport.delete(
                path=routes.RevokePermissionsRoutes.REVOKE_AUTHORIZATION_PERMISSION.format(
                    permissionId=permission_id
                ),
            ),
            spec.PermissionsOperationResponse,
        )


@final
class AsyncQueryPermissionsEndpoints(AsyncBaseEndpoints):
    async def query_entities_grants(
        self,
        request: spec.EntityPermissionsQueryRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryEntityPermissionsResponse:
        return self._parse(
            await self._transport.post(
                path=routes.QueryPermissionsRoutes.QUERY_ENTITIES_GRANTS,
                params=self.build_params(params),
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.QueryEntityPermissionsResponse,
        )

    async def query_personal_grants(
        self,
        request: spec.PersonalPermissionsQueryRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryPersonalPermissionsResponse:
        return self._parse(
            await self._transport.post(
                path=routes.QueryPermissionsRoutes.QUERY_PERSONAL_GRANTS,
                params=self.build_params(params),
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.QueryPersonalPermissionsResponse,
        )

    async def query_attachments_status(
        self,
    ) -> spec.CheckAttachmentPermissionStatusResponse:
        return self._parse(
            await self._transport.get(
                path=routes.QueryPermissionsRoutes.QUERY_ATTACHMENTS_STATUS,
            ),
            spec.CheckAttachmentPermissionStatusResponse,
        )

    async def query_authorizations_grants(
        self,
        request: spec.EntityAuthorizationPermissionsQueryRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryEntityAuthorizationPermissionsResponse:
        return self._parse(
            await self._transport.post(
                path=routes.QueryPermissionsRoutes.QUERY_AUTHORIZATIONS_GRANTS,
                params=self.build_params(params),
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.QueryEntityAuthorizationPermissionsResponse,
        )

    async def query_eu_entities_grants(
        self,
        request: spec.EuEntityPermissionsQueryRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryEuEntityPermissionsResponse:
        return self._parse(
            await self._transport.post(
                path=routes.QueryPermissionsRoutes.QUERY_EU_ENTITIES_GRANTS,
                params=self.build_params(params),
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.QueryEuEntityPermissionsResponse,
        )

    async def query_persons_grants(
        self,
        request: spec.PersonPermissionsQueryRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryPersonPermissionsResponse:
        return self._parse(
            await self._transport.post(
                path=routes.QueryPermissionsRoutes.QUERY_PERSONS_GRANTS,
                params=self.build_params(params),
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.QueryPersonPermissionsResponse,
        )

    async def query_subordinate_entities_roles(
        self,
        request: spec.SubordinateEntityRolesQueryRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QuerySubordinateEntityRolesResponse:
        return self._parse(
            await self._transport.post(
                path=routes.QueryPermissionsRoutes.QUERY_SUBORDINATE_ENTITIES_ROLES,
                params=self.build_params(params),
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.QuerySubordinateEntityRolesResponse,
        )

    async def query_subunits_grants(
        self,
        request: spec.SubunitPermissionsQueryRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QuerySubunitPermissionsResponse:
        return self._parse(
            await self._transport.post(
                path=routes.QueryPermissionsRoutes.QUERY_SUBUNITS_GRANTS,
                params=self.build_params(params),
                json=request.model_dump(mode="json", by_alias=True),
            ),
            spec.QuerySubunitPermissionsResponse,
        )


@final
class AsyncGetPermissionsEndpoints(AsyncBaseEndpoints):
    async def query_operation_status(
        self,
        reference_number: str,
    ) -> spec.PermissionsOperationStatusResponse:
        return self._parse(
            await self._transport.get(
                path=routes.QueryPermissionsRoutes.QUERY_OPERATIONS_STATUS.format(
                    referenceNumber=reference_number
                ),
            ),
            spec.PermissionsOperationStatusResponse,
        )

    async def query_entity_roles(
        self,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryEntityRolesResponse:
        return self._parse(
            await self._transport.get(
                path=routes.QueryPermissionsRoutes.QUERY_ENTITY_ROLES,
                params=self.build_params(params),
            ),
            spec.QueryEntityRolesResponse,
        )
