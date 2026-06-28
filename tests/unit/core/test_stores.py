from datetime import datetime, timedelta, timezone

import pytest

from ksef2.core.stores import CertificateStore
from ksef2.domain.models.encryption import CertUsage, PublicKeyCertificate


def _certificate(
    usage: CertUsage,
    *,
    public_key_id: str = "public-key-id",
) -> PublicKeyCertificate:
    return PublicKeyCertificate(
        certificate="certificate",
        certificate_id="certificate-id",
        public_key_id=public_key_id,
        valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        valid_to=datetime(2030, 1, 1, tzinfo=timezone.utc),
        usage=[usage],
    )


def test_empty_store_needs_refresh() -> None:
    store = CertificateStore()

    assert store.needs_refresh("symmetric_key_encryption")


def test_missing_usage_needs_refresh() -> None:
    store = CertificateStore()
    store.load([_certificate("ksef_token_encryption")])

    assert store.needs_refresh("symmetric_key_encryption")


def test_fresh_valid_certificate_does_not_need_refresh() -> None:
    store = CertificateStore()
    store.load([_certificate("symmetric_key_encryption")])

    assert not store.needs_refresh("symmetric_key_encryption")


def test_stale_valid_certificate_needs_refresh() -> None:
    store = CertificateStore()
    store.load([_certificate("symmetric_key_encryption")])

    assert store.needs_refresh(
        "symmetric_key_encryption",
        at=datetime.now(tz=timezone.utc) + timedelta(days=2),
    )


def test_refresh_after_none_keeps_valid_certificate_fresh() -> None:
    store = CertificateStore(refresh_after=None)
    store.load([_certificate("symmetric_key_encryption")])

    assert not store.needs_refresh(
        "symmetric_key_encryption",
        at=datetime.now(tz=timezone.utc) + timedelta(days=365),
    )


def test_zero_refresh_interval_always_refreshes_valid_certificate() -> None:
    store = CertificateStore(refresh_after=timedelta(0))
    store.load([_certificate("symmetric_key_encryption")])

    assert store.needs_refresh("symmetric_key_encryption")


def test_add_marks_store_fresh() -> None:
    store = CertificateStore()
    store.add(_certificate("symmetric_key_encryption"))

    assert not store.needs_refresh("symmetric_key_encryption")


def test_negative_refresh_interval_is_rejected() -> None:
    with pytest.raises(ValueError, match="refresh_after cannot be negative"):
        CertificateStore(refresh_after=timedelta(seconds=-1))
