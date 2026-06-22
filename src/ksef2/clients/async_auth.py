"""Async authentication branch client."""

import asyncio
from pathlib import Path
from typing import final

from cryptography.x509 import Certificate

from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_encryption import AsyncEncryptionClient
from ksef2.clients.profiles import (
    ProfileAuthType,
    load_cli_profile,
    load_profile_p12_credentials,
    load_profile_pem_credentials,
    profile_context_type,
    resolve_profile_secret,
)
from ksef2.config import Environment
from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.core.crypto import encrypt_token
from ksef2.core.polling import async_poll_until
from ksef2.core.stores import CertificateStore
from ksef2.xades import XAdESPrivateKey, generate_test_certificate
from ksef2.domain.models.auth import (
    AuthOperationStatus,
    AuthTokens,
    ContextIdentifierType,
    InitTokenAuthenticationRequest,
    RefreshedToken,
)
from ksef2.endpoints.async_auth import AsyncAuthEndpoints
from ksef2.infra.mappers.auth import from_spec, to_spec


def _build_signed_xades(
    *,
    challenge: str,
    nip: str,
    cert: Certificate,
    private_key: XAdESPrivateKey,
) -> bytes:
    from ksef2.xades import build_auth_token_request_xml, sign_xades

    xml_bytes = build_auth_token_request_xml(challenge, nip)
    return sign_xades(xml_bytes, cert, private_key)


@final
class AsyncAuthClient:
    """Async entry point for creating authenticated SDK clients.

    Catch ``KSeFException`` for SDK-classified failures raised by this branch,
    and ``httpx.HTTPError`` for transport failures.

    Raises:
        KSeFApiError: If KSeF returns an API error response. Catch
            ``KSeFAuthError`` for authentication or authorization failures and
            ``KSeFRateLimitError`` for throttling.
        KSeFValidationError: If a KSeF response cannot be parsed into SDK models.
        httpx.HTTPError: If the HTTP transport fails before KSeF returns a response.
    """

    def __init__(
        self,
        transport: AsyncMiddleware,
        certificate_store: CertificateStore,
        environment: Environment = Environment.PRODUCTION,
    ) -> None:
        self._transport = transport
        self._certificate_store = certificate_store
        self._environment = environment
        self._certificates = AsyncEncryptionClient(transport)
        self._auth_ep = AsyncAuthEndpoints(transport)

    async def with_token(
        self,
        *,
        ksef_token: str,
        nip: str,
        context_type: ContextIdentifierType = "nip",
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> AsyncAuthenticatedClient:
        """Authenticate with a KSeF token and return an authenticated client.

        Args:
            ksef_token: Token generated in KSeF for the target context.
            nip: Context identifier value used for authentication.
            context_type: Type of identifier represented by ``nip``.
            timeout: Maximum number of seconds to wait for authentication.
            poll_interval: Delay in seconds between authentication status checks.

        Returns:
            An authenticated client with redeemed access and refresh tokens.

        Raises:
            NoCertificateAvailableError: If no valid token-encryption certificate is
                available.
            KSeFEncryptionError: If token encryption fails.
            KSeFAuthError: If authentication fails.
            KSeFAuthPollingTimeoutError: If polling exceeds ``timeout``.
        """
        await self._ensure_certificates()

        challenge = from_spec(await self._auth_ep.challenge())
        try:
            cert = self._certificate_store.get_valid("ksef_token_encryption")
        except exceptions.NoCertificateAvailableError as exc:
            raise exceptions.NoCertificateAvailableError(
                "No valid certificate for KsefTokenEncryption found."
            ) from exc

        encrypted = encrypt_token(
            ksef_token, str(challenge.timestamp_ms), cert.certificate
        )
        request = InitTokenAuthenticationRequest(
            challenge=challenge.challenge,
            context_type=context_type,
            context_value=nip,
            encrypted_token=encrypted,
            public_key_id=cert.public_key_id,
        )
        init_resp = from_spec(await self._auth_ep.token_auth(body=to_spec(request)))

        await self._poll_until_authenticated(
            auth_token=init_resp.authentication_token.token,
            reference_number=init_resp.reference_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )

        return self._build_authenticated_client(
            auth_tokens=await self._redeem(init_resp.authentication_token.token)
        )

    async def with_xades(
        self,
        *,
        nip: str,
        cert: Certificate,
        private_key: XAdESPrivateKey,
        verify_chain: bool = False,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> AsyncAuthenticatedClient:
        """Authenticate with an XAdES-signed challenge response.

        Args:
            nip: Taxpayer identifier embedded in the authentication request.
            cert: Signing certificate accepted by the target environment.
            private_key: RSA or EC private key used to sign the XAdES payload.
            verify_chain: Whether KSeF should verify the certificate chain.
            timeout: Maximum number of seconds to wait for authentication.
            poll_interval: Delay in seconds between authentication status checks.

        Returns:
            An authenticated client with redeemed access and refresh tokens.

        Raises:
            KSeFAuthError: If authentication fails.
            KSeFAuthPollingTimeoutError: If polling exceeds ``timeout``.
        """
        challenge = from_spec(await self._auth_ep.challenge())
        signed_xml = await asyncio.to_thread(
            _build_signed_xades,
            challenge=challenge.challenge,
            nip=nip,
            cert=cert,
            private_key=private_key,
        )

        init_resp = from_spec(
            await self._auth_ep.xades_auth(signed_xml, verify_chain=verify_chain)
        )

        await self._poll_until_authenticated(
            auth_token=init_resp.authentication_token.token,
            reference_number=init_resp.reference_number,
            timeout=timeout,
            poll_interval=poll_interval,
        )

        return self._build_authenticated_client(
            auth_tokens=await self._redeem(init_resp.authentication_token.token)
        )

    async def with_test_certificate(
        self,
        *,
        nip: str,
        verify_chain: bool = False,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
    ) -> AsyncAuthenticatedClient:
        """Authenticate in the TEST environment using an SDK-generated certificate.

        Raises:
            KSeFUnsupportedEnvironmentError: If the client is not configured for TEST.
            KSeFAuthError: If authentication fails.
            KSeFAuthPollingTimeoutError: If polling exceeds ``timeout``.
        """
        if self._environment is not Environment.TEST:
            raise exceptions.KSeFUnsupportedEnvironmentError(
                "with_test_certificate() is only available for Environment.TEST"
            )

        cert, private_key = await asyncio.to_thread(generate_test_certificate, nip)
        return await self.with_xades(
            nip=nip,
            cert=cert,
            private_key=private_key,
            verify_chain=verify_chain,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def with_profile(
        self,
        name: str | None = None,
        *,
        config_path: str | Path | None = None,
        timeout: float | None = None,
        poll_interval: float | None = None,
        verify_chain: bool = False,
    ) -> AsyncAuthenticatedClient:
        """Authenticate with a local ``ksef2-cli`` profile.

        Profile selection follows the CLI order: explicit ``name``,
        ``KSEF2_PROFILE``, then ``active_profile`` from the local CLI config.
        The profile environment must match the root client environment.
        """
        profile_name, profile = load_cli_profile(name, config_path=config_path)
        if profile.sdk_environment is not self._environment:
            raise exceptions.KSeFValidationError(
                f"ksef2-cli profile {profile_name!r} uses "
                f"Environment.{profile.sdk_environment.name}, but this client uses "
                f"Environment.{self._environment.name}.",
                profile_name=profile_name,
                profile_environment=profile.sdk_environment.name,
                client_environment=self._environment.name,
            )

        effective_poll_interval = poll_interval
        if effective_poll_interval is None:
            effective_poll_interval = profile.poll_interval or 1.0

        effective_timeout = timeout
        if effective_timeout is None and profile.max_poll_attempts is not None:
            effective_timeout = profile.max_poll_attempts * effective_poll_interval
        if effective_timeout is None:
            effective_timeout = 60.0

        auth = profile.auth
        match auth.type:
            case ProfileAuthType.TOKEN:
                token = resolve_profile_secret(
                    auth.token_env,
                    label="KSeF token",
                    profile_name=profile_name,
                )
                if token is None:
                    raise exceptions.KSeFValidationError(
                        f"ksef2-cli profile {profile_name!r} requires auth.token_env.",
                        profile_name=profile_name,
                    )
                return await self.with_token(
                    ksef_token=token,
                    nip=profile.nip,
                    context_type=profile_context_type(auth),
                    timeout=effective_timeout,
                    poll_interval=effective_poll_interval,
                )
            case ProfileAuthType.TEST_CERTIFICATE:
                return await self.with_test_certificate(
                    nip=profile.nip,
                    verify_chain=verify_chain,
                    timeout=effective_timeout,
                    poll_interval=effective_poll_interval,
                )
            case ProfileAuthType.XADES_PEM:
                cert, private_key = await asyncio.to_thread(
                    load_profile_pem_credentials,
                    profile,
                    profile_name=profile_name,
                )
                return await self.with_xades(
                    nip=profile.nip,
                    cert=cert,
                    private_key=private_key,
                    verify_chain=verify_chain,
                    timeout=effective_timeout,
                    poll_interval=effective_poll_interval,
                )
            case ProfileAuthType.XADES_P12:
                cert, private_key = await asyncio.to_thread(
                    load_profile_p12_credentials,
                    profile,
                    profile_name=profile_name,
                )
                return await self.with_xades(
                    nip=profile.nip,
                    cert=cert,
                    private_key=private_key,
                    verify_chain=verify_chain,
                    timeout=effective_timeout,
                    poll_interval=effective_poll_interval,
                )

    async def refresh(self, *, refresh_token: str) -> RefreshedToken:
        """Exchange a refresh token for a new access token."""
        return from_spec(await self._auth_ep.refresh_token(bearer_token=refresh_token))

    async def _redeem(self, auth_token: str) -> AuthTokens:
        """Redeem the temporary authentication token for access and refresh tokens."""
        return from_spec(await self._auth_ep.redeem_token(bearer_token=auth_token))

    def _build_authenticated_client(
        self,
        *,
        auth_tokens: AuthTokens,
    ) -> AsyncAuthenticatedClient:
        """Wrap redeemed tokens in an authenticated SDK client."""
        return AsyncAuthenticatedClient(
            transport=self._transport,
            auth_tokens=auth_tokens,
            certificate_store=self._certificate_store,
            environment=self._environment,
        )

    async def _ensure_certificates(self) -> None:
        """Populate the certificate store when token authentication needs it."""
        if not self._certificate_store.all():
            self._certificate_store.load(await self._certificates.get_certificates())

    async def _poll_until_authenticated(
        self,
        *,
        auth_token: str,
        reference_number: str,
        timeout: float,
        poll_interval: float,
    ) -> None:
        """Poll authentication status until the operation succeeds or fails."""
        auth_token_local = auth_token
        reference_number_local = reference_number

        async def _poll() -> AuthOperationStatus:
            status = from_spec(
                await self._auth_ep.auth_status(
                    bearer_token=auth_token_local,
                    reference_number=reference_number_local,
                )
            )
            if status.status_code >= 400:
                raise exceptions.KSeFAuthError(
                    status_code=status.status_code,
                    message=f"Authentication failed: {status.status_description}",
                )
            return status

        _ = await async_poll_until(
            operation=_poll,
            retry_predicate=lambda status: status.status_code < 200,
            poll_interval=poll_interval,
            timeout_seconds=timeout,
            timeout_error_factory=lambda: exceptions.KSeFAuthPollingTimeoutError(
                reference_number=reference_number_local,
                timeout=timeout,
            ),
        )
