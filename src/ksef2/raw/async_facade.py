"""Asynchronous raw endpoint facades."""

from functools import cached_property
from typing import final

from ksef2.config import Environment
from ksef2.core import exceptions
from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.endpoints.async_auth import AsyncAuthEndpoints
from ksef2.endpoints.async_certificates import AsyncCertificatesEndpoints
from ksef2.endpoints.async_encryption import AsyncEncryptionEndpoints
from ksef2.endpoints.async_invoices import AsyncInvoicesEndpoints
from ksef2.endpoints.async_limits import AsyncLimitEndpoints
from ksef2.endpoints.async_peppol import AsyncPeppolEndpoints
from ksef2.endpoints.async_permissions import (
    AsyncGetPermissionsEndpoints,
    AsyncPermissionsGrantEndpoints,
    AsyncQueryPermissionsEndpoints,
    AsyncRevokePermissionsEndpoints,
)
from ksef2.endpoints.async_session import AsyncSessionEndpoints
from ksef2.endpoints.async_testdata import AsyncTestDataEndpoints
from ksef2.endpoints.async_tokens import AsyncTokenEndpoints


@final
class AsyncRawPermissionsEndpoints:
    """Raw permission endpoint groups bound to one async transport."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._transport = transport

    @cached_property
    def grant(self) -> AsyncPermissionsGrantEndpoints:
        """Return permission grant endpoints."""
        return AsyncPermissionsGrantEndpoints(self._transport)

    @cached_property
    def revoke(self) -> AsyncRevokePermissionsEndpoints:
        """Return permission revocation endpoints."""
        return AsyncRevokePermissionsEndpoints(self._transport)

    @cached_property
    def query(self) -> AsyncQueryPermissionsEndpoints:
        """Return permission query endpoints."""
        return AsyncQueryPermissionsEndpoints(self._transport)

    @cached_property
    def status(self) -> AsyncGetPermissionsEndpoints:
        """Return permission operation status and role endpoints."""
        return AsyncGetPermissionsEndpoints(self._transport)


@final
class AsyncRawClient:
    """Raw unauthenticated endpoint facade for advanced async integrations."""

    def __init__(self, transport: AsyncMiddleware, environment: Environment) -> None:
        self._transport = transport
        self._environment = environment

    @cached_property
    def auth(self) -> AsyncAuthEndpoints:
        """Return raw authentication endpoints."""
        return AsyncAuthEndpoints(self._transport)

    @cached_property
    def encryption(self) -> AsyncEncryptionEndpoints:
        """Return raw public encryption-certificate endpoints."""
        return AsyncEncryptionEndpoints(self._transport)

    @cached_property
    def peppol(self) -> AsyncPeppolEndpoints:
        """Return raw Peppol provider endpoints."""
        return AsyncPeppolEndpoints(self._transport)

    @cached_property
    def testdata(self) -> AsyncTestDataEndpoints:
        """Return raw TEST-only data seeding endpoints."""
        if self._environment is not Environment.TEST:
            raise exceptions.KSeFUnsupportedEnvironmentError(
                "testdata is only available for Environment.TEST"
            )
        return AsyncTestDataEndpoints(self._transport)


@final
class AsyncRawAuthenticatedClient:
    """Raw authenticated endpoint facade for advanced async integrations."""

    def __init__(
        self,
        *,
        transport: AsyncMiddleware,
        authed_transport: AsyncMiddleware,
        environment: Environment,
    ) -> None:
        self._transport = transport
        self._authed_transport = authed_transport
        self._environment = environment

    @cached_property
    def auth(self) -> AsyncAuthEndpoints:
        """Return raw authenticated authentication-session endpoints."""
        return AsyncAuthEndpoints(self._authed_transport)

    @cached_property
    def certificates(self) -> AsyncCertificatesEndpoints:
        """Return raw certificate lifecycle endpoints."""
        return AsyncCertificatesEndpoints(self._authed_transport)

    @cached_property
    def encryption(self) -> AsyncEncryptionEndpoints:
        """Return raw public encryption-certificate endpoints."""
        return AsyncEncryptionEndpoints(self._transport)

    @cached_property
    def invoices(self) -> AsyncInvoicesEndpoints:
        """Return raw invoice and invoice-session endpoints."""
        return AsyncInvoicesEndpoints(self._authed_transport)

    @cached_property
    def limits(self) -> AsyncLimitEndpoints:
        """Return raw limit endpoints."""
        return AsyncLimitEndpoints(self._authed_transport)

    @cached_property
    def peppol(self) -> AsyncPeppolEndpoints:
        """Return raw Peppol provider endpoints."""
        return AsyncPeppolEndpoints(self._transport)

    @cached_property
    def permissions(self) -> AsyncRawPermissionsEndpoints:
        """Return raw permission endpoint groups."""
        return AsyncRawPermissionsEndpoints(self._authed_transport)

    @cached_property
    def session(self) -> AsyncSessionEndpoints:
        """Return raw online and batch session endpoints."""
        return AsyncSessionEndpoints(self._authed_transport)

    @cached_property
    def testdata(self) -> AsyncTestDataEndpoints:
        """Return raw TEST-only data seeding endpoints."""
        if self._environment is not Environment.TEST:
            raise exceptions.KSeFUnsupportedEnvironmentError(
                "testdata is only available for Environment.TEST"
            )
        return AsyncTestDataEndpoints(self._transport)

    @cached_property
    def tokens(self) -> AsyncTokenEndpoints:
        """Return raw token lifecycle endpoints."""
        return AsyncTokenEndpoints(self._authed_transport)
