from collections.abc import Callable

import pytest

from ksef2._clients.async_auth import _validated_nip
from ksef2._clients.async_base import AsyncClient
from ksef2._clients.base import Client
from ksef2._config import RetryConfig, TimeoutConfig
from ksef2._core.exceptions import KSeFArgumentError, KSeFValidationError
from ksef2._domain.models.batch import BatchInvoice
from ksef2._services.batch_preparation import prepare_batch_package


def test_nip_accepts_dashes_and_pl_prefix_and_normalizes() -> None:
    assert _validated_nip("PL526-104-08-28") == "5261040828"


@pytest.mark.parametrize("nip", [None, "123", "5261040829", "PL526-104-08-28x"])
def test_nip_rejects_invalid_values_with_hint(nip: str | None) -> None:
    with pytest.raises(KSeFArgumentError, match="nip") as error:
        _validated_nip(nip)
    assert error.value.hint


def test_batch_part_count_is_rejected_before_encryption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def encryption_must_not_run(**_: object) -> bytes:
        pytest.fail("part encryption ran before the part-count validation")

    monkeypatch.setattr(
        "ksef2._services.batch_preparation.encrypt_batch_part", encryption_must_not_run
    )
    with pytest.raises(KSeFValidationError, match="needs"):
        prepare_batch_package(
            invoices=[BatchInvoice(file_name="invoice.xml", content=b"<a/>")],
            aes_key=b"k" * 32,
            iv=b"i" * 16,
            encrypted_key=b"encrypted",
            max_part_size=1,
        )


def test_batch_preparation_rejects_invoice_over_default_size() -> None:
    with pytest.raises(KSeFValidationError, match="1 MB"):
        prepare_batch_package(
            invoices=[BatchInvoice(file_name="large.xml", content=b"x" * 1_000_001)],
            aes_key=b"k" * 32,
            iv=b"i" * 16,
            encrypted_key=b"encrypted",
        )


@pytest.mark.parametrize(
    "build",
    [
        lambda: TimeoutConfig(read=-5),
        lambda: TimeoutConfig(read="30"),
        lambda: RetryConfig(max_attempts=0),
    ],
)
def test_transport_configuration_rejects_invalid_values(
    build: Callable[[], object],
) -> None:
    with pytest.raises(KSeFArgumentError):
        build()


def test_sync_root_client_rejects_dictionary_transport_config() -> None:
    with pytest.raises(KSeFArgumentError, match="TransportConfig instance"):
        Client(transport_config={})


def test_async_root_client_rejects_dictionary_transport_config() -> None:
    with pytest.raises(KSeFArgumentError, match="TransportConfig instance"):
        AsyncClient(transport_config={})
