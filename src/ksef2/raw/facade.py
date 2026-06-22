"""Synchronous raw endpoint facades."""

from functools import cached_property
from typing import final

from ksef2.config import Environment
from ksef2.core import exceptions
from ksef2.core.protocols import Middleware
from ksef2.endpoints.auth import AuthEndpoints
from ksef2.endpoints.certificates import CertificatesEndpoints
from ksef2.endpoints.encryption import EncryptionEndpoints
from ksef2.endpoints.invoices import InvoicesEndpoints
from ksef2.endpoints.limits import LimitEndpoints
from ksef2.endpoints.peppol import PeppolEndpoints
from ksef2.endpoints.permissions import (
    GetPermissionsEndpoints,
    PermissionsGrantEndpoints,
    QueryPermissionsEndpoints,
    RevokePermissionsEndpoints,
)
from ksef2.endpoints.session import SessionEndpoints
from ksef2.endpoints.testdata import TestDataEndpoints
from ksef2.endpoints.tokens import TokenEndpoints


@final
class RawPermissionsEndpoints:
    """Raw permission endpoint groups bound to one transport."""

    def __init__(self, transport: Middleware) -> None:
        self._transport = transport

    @cached_property
    def grant(self) -> PermissionsGrantEndpoints:
        """Return permission grant endpoints."""
        return PermissionsGrantEndpoints(self._transport)

    @cached_property
    def revoke(self) -> RevokePermissionsEndpoints:
        """Return permission revocation endpoints."""
        return RevokePermissionsEndpoints(self._transport)

    @cached_property
    def query(self) -> QueryPermissionsEndpoints:
        """Return permission query endpoints."""
        return QueryPermissionsEndpoints(self._transport)

    @cached_property
    def status(self) -> GetPermissionsEndpoints:
        """Return permission operation status and role endpoints."""
        return GetPermissionsEndpoints(self._transport)


@final
class RawClient:
    """Raw unauthenticated endpoint facade for advanced integrations."""

    def __init__(self, transport: Middleware, environment: Environment) -> None:
        self._transport = transport
        self._environment = environment

    @cached_property
    def auth(self) -> AuthEndpoints:
        """Return raw authentication endpoints."""
        return AuthEndpoints(self._transport)

    @cached_property
    def encryption(self) -> EncryptionEndpoints:
        """Return raw public encryption-certificate endpoints."""
        return EncryptionEndpoints(self._transport)

    @cached_property
    def peppol(self) -> PeppolEndpoints:
        """Return raw Peppol provider endpoints."""
        return PeppolEndpoints(self._transport)

    @cached_property
    def testdata(self) -> TestDataEndpoints:
        """Return raw TEST-only data seeding endpoints."""
        if self._environment is not Environment.TEST:
            raise exceptions.KSeFUnsupportedEnvironmentError(
                "testdata is only available for Environment.TEST"
            )
        return TestDataEndpoints(self._transport)


@final
class RawAuthenticatedClient:
    """Raw authenticated endpoint facade for advanced integrations."""

    def __init__(
        self,
        *,
        transport: Middleware,
        authed_transport: Middleware,
        environment: Environment,
    ) -> None:
        self._transport = transport
        self._authed_transport = authed_transport
        self._environment = environment

    @cached_property
    def auth(self) -> AuthEndpoints:
        """Return raw authenticated authentication-session endpoints."""
        return AuthEndpoints(self._authed_transport)

    @cached_property
    def certificates(self) -> CertificatesEndpoints:
        """Return raw certificate lifecycle endpoints."""
        return CertificatesEndpoints(self._authed_transport)

    @cached_property
    def encryption(self) -> EncryptionEndpoints:
        """Return raw public encryption-certificate endpoints."""
        return EncryptionEndpoints(self._transport)

    @cached_property
    def invoices(self) -> InvoicesEndpoints:
        """Return raw invoice and invoice-session endpoints."""
        return InvoicesEndpoints(self._authed_transport)

    @cached_property
    def limits(self) -> LimitEndpoints:
        """Return raw limit endpoints."""
        return LimitEndpoints(self._authed_transport)

    @cached_property
    def peppol(self) -> PeppolEndpoints:
        """Return raw Peppol provider endpoints."""
        return PeppolEndpoints(self._transport)

    @cached_property
    def permissions(self) -> RawPermissionsEndpoints:
        """Return raw permission endpoint groups."""
        return RawPermissionsEndpoints(self._authed_transport)

    @cached_property
    def session(self) -> SessionEndpoints:
        """Return raw online and batch session endpoints."""
        return SessionEndpoints(self._authed_transport)

    @cached_property
    def testdata(self) -> TestDataEndpoints:
        """Return raw TEST-only data seeding endpoints."""
        if self._environment is not Environment.TEST:
            raise exceptions.KSeFUnsupportedEnvironmentError(
                "testdata is only available for Environment.TEST"
            )
        return TestDataEndpoints(self._transport)

    @cached_property
    def tokens(self) -> TokenEndpoints:
        """Return raw token lifecycle endpoints."""
        return TokenEndpoints(self._authed_transport)
