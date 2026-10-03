from collections.abc import Iterable

from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable

from ksef2._core import exceptions
from ksef2._domain.models import encryption

DEFAULT_CERTIFICATE_REFRESH_AFTER = timedelta(hours=24)


def _make_aware(dt: datetime, tz: timezone = timezone.utc) -> datetime:
    """Convert naive datetime to aware, or return if already aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt


@runtime_checkable
class CertificateStoreProtocol(Protocol):
    """Structural contract for SDK public encryption certificate stores.

    Implement it to supply your own cache for KSeF public-key certificates, then pass it to the ``Client`` as ``certificate_store``.
    """

    def load(self, certs: Iterable[encryption.PublicKeyCertificate]) -> None:
        """Replace the stored certificates.

        Args:
            certs: Certificates to store.
        """
        ...

    def get_valid(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
    ) -> encryption.PublicKeyCertificate:
        """Return a valid certificate for a usage.

        Args:
            usage: Required usage, for example ``"ksef_token_encryption"`` or ``"symmetric_key_encryption"``.

        Returns:
            A certificate that is currently valid for the usage.

        Raises:
            NoCertificateAvailableError: If no valid certificate exists for the usage.
        """
        ...

    def needs_refresh(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
        *,
        at: datetime | None = None,
    ) -> bool:
        """Tell whether the stored certificates should be reloaded.

        Args:
            usage: Usage that must be covered by a valid certificate.
            at: Time to evaluate at; the current time when ``None``.

        Returns:
            ``True`` if no valid certificate covers the usage or the store is stale.
        """
        ...


class CertificateStore:
    """In-memory store of KSeF public-key certificates.

    The store is filled by the SDK from the KSeF API and serves the certificates used to encrypt tokens and session keys.
    """

    def __init__(
        self,
        refresh_after: timedelta | None = DEFAULT_CERTIFICATE_REFRESH_AFTER,
    ) -> None:
        """Create the CertificateStore.

        Args:
            refresh_after: How long loaded certificates stay fresh before ``needs_refresh()`` reports ``True``; ``None`` to never expire them. Defaults to 24 hours.

        Raises:
            ValueError: If ``refresh_after`` is negative.
        """
        if refresh_after is not None and refresh_after < timedelta(0):
            raise ValueError("refresh_after cannot be negative.")
        self._certificates: list[encryption.PublicKeyCertificate] = []
        self._refresh_after = refresh_after
        self._loaded_at: datetime | None = None

    def load(self, certs: Iterable[encryption.PublicKeyCertificate]) -> None:
        """Replace stored certificates.

        Args:
            certs: Certificates to store.
        """
        self._certificates = list(certs)
        self._loaded_at = datetime.now(tz=timezone.utc)

    def add(self, cert: encryption.PublicKeyCertificate) -> None:
        """Append a certificate to the store.

        Args:
            cert: Certificate to add.
        """
        self._certificates.append(cert)
        self._loaded_at = datetime.now(tz=timezone.utc)

    def all(self) -> list[encryption.PublicKeyCertificate]:
        """List all stored certificates, valid or not.

        Returns:
            A copy of the stored certificates.
        """
        return list(self._certificates)

    def get_valid(
        self,
        usage: encryption.CertUsage | encryption.CertUsageEnum | str,
    ) -> encryption.PublicKeyCertificate:
        """Get a valid certificate for given usage.

        Args:
            usage: Required usage, for example ``"ksef_token_encryption"`` or ``"symmetric_key_encryption"``.

        Returns:
            The first certificate that is currently valid for the usage.

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
        """List the certificates that are valid at a given time.

        Args:
            at: Time to evaluate at; the current time when ``None``. Naive values are read as UTC.

        Returns:
            Certificates whose validity period contains ``at``.
        """
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
        """List valid certificates that cover a usage.

        Args:
            usage: Required usage, for example ``"ksef_token_encryption"``.
            at: Time to evaluate at; the current time when ``None``.

        Returns:
            Certificates that are valid at ``at`` and list the usage.
        """
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
        """Tell whether the stored certificates should be reloaded.

        Args:
            usage: Usage that must be covered by a valid certificate.
            at: Time to evaluate at; the current time when ``None``.

        Returns:
            ``True`` if no valid certificate covers the usage, nothing was loaded yet, or the loaded certificates are older than ``refresh_after``.
        """
        if not self.by_usage(usage=usage, at=at):
            return True

        if self._loaded_at is None:
            return True

        if self._refresh_after is None:
            return False

        now = _make_aware(at) if at else datetime.now(tz=timezone.utc)
        return _make_aware(self._loaded_at) + self._refresh_after <= now
