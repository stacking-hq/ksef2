from collections.abc import Iterable

from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable

from ksef2.core import exceptions
from ksef2.domain.models import encryption

DEFAULT_CERTIFICATE_REFRESH_AFTER = timedelta(hours=24)


def _make_aware(dt: datetime, tz: timezone = timezone.utc) -> datetime:
    """Convert naive datetime to aware, or return if already aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt


@runtime_checkable
class CertificateStoreProtocol(Protocol):
    """Structural contract for SDK public encryption certificate stores."""

    def load(self, certs: Iterable[encryption.PublicKeyCertificate]) -> None: ...

    def get_valid(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
    ) -> encryption.PublicKeyCertificate: ...

    def needs_refresh(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
        *,
        at: datetime | None = None,
    ) -> bool: ...


class CertificateStore:
    def __init__(
        self,
        refresh_after: timedelta | None = DEFAULT_CERTIFICATE_REFRESH_AFTER,
    ) -> None:
        if refresh_after is not None and refresh_after < timedelta(0):
            raise ValueError("refresh_after cannot be negative.")
        self._certificates: list[encryption.PublicKeyCertificate] = []
        self._refresh_after = refresh_after
        self._loaded_at: datetime | None = None

    def load(self, certs: Iterable[encryption.PublicKeyCertificate]) -> None:
        """Replace stored certificates."""
        self._certificates = list(certs)
        self._loaded_at = datetime.now(tz=timezone.utc)

    def add(self, cert: encryption.PublicKeyCertificate) -> None:
        self._certificates.append(cert)
        self._loaded_at = datetime.now(tz=timezone.utc)

    def all(self) -> list[encryption.PublicKeyCertificate]:
        return list(self._certificates)

    def get_valid(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
    ) -> encryption.PublicKeyCertificate:
        """Get a valid certificate for given usage.

        Raises:
            NoCertificateAvailableError: If no valid certificate found for usage.
        """
        cert = next(iter(self.by_usage(usage=usage)), None)
        if cert is None:
            raise exceptions.NoCertificateAvailableError(
                f"No valid certificate for usage: {usage}"
            )
        return cert

    def list_valid(
        self,
        *,
        at: datetime | None = None,
    ) -> list[encryption.PublicKeyCertificate]:
        now = _make_aware(at) if at else datetime.now(tz=timezone.utc)

        return [
            cert
            for cert in self._certificates
            if cert.valid_from <= now <= cert.valid_to
        ]

    def by_usage(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
        *,
        at: datetime | None = None,
    ) -> list[encryption.PublicKeyCertificate]:
        normalized_usage = encryption.normalize_cert_usage(usage)
        return [
            cert for cert in self.list_valid(at=at) if normalized_usage in cert.usage
        ]

    def needs_refresh(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
        *,
        at: datetime | None = None,
    ) -> bool:
        if not self.by_usage(usage=usage, at=at):
            return True

        if self._loaded_at is None:
            return True

        if self._refresh_after is None:
            return False

        now = _make_aware(at) if at else datetime.now(tz=timezone.utc)
        return _make_aware(self._loaded_at) + self._refresh_after <= now
