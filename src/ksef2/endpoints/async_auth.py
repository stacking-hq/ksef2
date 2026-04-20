"""Async authentication endpoints."""

from typing import NotRequired, TypedDict, Unpack, final

from pydantic import TypeAdapter

from ksef2.core import headers, routes
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.infra.schema.api import spec
from ksef2.infra.schema.api.supp.auth import InitTokenAuthenticationRequest

AuthSessionsQueryParams = TypedDict(
    "AuthSessionsQueryParams",
    {
        "pageSize": NotRequired[int | None],
    },
)

XadesAuthParams = TypedDict(
    "XadesAuthParams",
    {
        "verifyCertificateChain": NotRequired[str | None],
    },
)


@final
class AsyncAuthEndpoints(AsyncBaseEndpoints):
    _AUTH_SESSIONS_PARAMS = TypeAdapter(AuthSessionsQueryParams)
    _XADES_AUTH_PARAMS = TypeAdapter(XadesAuthParams)

    async def list_sessions(
        self,
        continuation_token: str | None = None,
        **params: Unpack[AuthSessionsQueryParams],
    ) -> spec.AuthenticationListResponse:
        req_headers = (
            {"x-continuation-token": continuation_token} if continuation_token else None
        )

        return self._parse(
            await self._transport.get(
                path=routes.AuthRoutes.LIST_SESSIONS,
                params=self.build_params(params, self._AUTH_SESSIONS_PARAMS),
                headers=req_headers,
            ),
            spec.AuthenticationListResponse,
        )

    async def xades_auth(
        self,
        signed_xml: bytes,
        verify_chain: bool = False,
    ) -> spec.AuthenticationInitResponse:
        query_params: XadesAuthParams = {
            "verifyCertificateChain": str(verify_chain).lower(),
        }
        return self._parse(
            await self._transport.request(
                "POST",
                routes.AuthRoutes.XADES_SIGNATURE,
                params=self.build_params(query_params, self._XADES_AUTH_PARAMS),
                content=signed_xml,
                headers={"Content-Type": "application/xml"},
            ),
            spec.AuthenticationInitResponse,
        )

    async def challenge(self) -> spec.AuthenticationChallengeResponse:
        return self._parse(
            await self._transport.post(
                path=routes.AuthRoutes.CHALLENGE,
            ),
            spec.AuthenticationChallengeResponse,
        )

    async def token_auth(
        self, body: InitTokenAuthenticationRequest
    ) -> spec.AuthenticationInitResponse:
        return self._parse(
            await self._transport.post(
                path=routes.AuthRoutes.TOKEN_AUTH,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.AuthenticationInitResponse,
        )

    async def auth_status(
        self,
        bearer_token: str,
        reference_number: str,
    ) -> spec.AuthenticationOperationStatusResponse:
        return self._parse(
            await self._transport.get(
                path=routes.AuthRoutes.AUTH_STATUS.format(
                    referenceNumber=reference_number
                ),
                headers=headers.KSeFHeaders.bearer(bearer_token),
            ),
            spec.AuthenticationOperationStatusResponse,
        )

    async def redeem_token(
        self,
        bearer_token: str,
    ) -> spec.AuthenticationTokensResponse:
        return self._parse(
            await self._transport.post(
                path=routes.AuthRoutes.REDEEM_TOKEN,
                headers=headers.KSeFHeaders.bearer(bearer_token),
            ),
            spec.AuthenticationTokensResponse,
        )

    async def refresh_token(
        self, bearer_token: str
    ) -> spec.AuthenticationTokenRefreshResponse:
        return self._parse(
            await self._transport.post(
                path=routes.AuthRoutes.REFRESH_TOKEN,
                headers=headers.KSeFHeaders.bearer(bearer_token),
            ),
            spec.AuthenticationTokenRefreshResponse,
        )

    async def terminate_current_session(self) -> None:
        _ = await self._transport.delete(
            path=routes.AuthRoutes.TERMINATE_CURRENT_SESSION,
        )

    async def terminate_auth_session(self, reference_number: str) -> None:
        _ = await self._transport.delete(
            path=routes.AuthRoutes.TERMINATE_AUTH_SESSION.format(
                referenceNumber=reference_number
            ),
        )
