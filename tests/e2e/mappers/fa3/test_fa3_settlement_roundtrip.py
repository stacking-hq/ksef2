import pytest

from ksef2.domain.models.fa3.body import InvoiceType

from tests.e2e.mappers.fa3._roundtrip import assert_roundtrip


SETTLEMENT_SAMPLES = [
    "Fa_3_Przykład_14.xml",
    "Fa_3_Przykład_17.xml",
    "KSEF_09_ROZ_A.xml",
    "KSEF_10_ROZ_B.xml",
]

CORRECTION_SETTLEMENT_SAMPLES = [
    "Fa_3_Przykład_18.xml",
    "KSEF_11_KOR_ROZ_A.xml",
    "KSEF_12_KOR_ROZ_B.xml",
]


@pytest.mark.parametrize("sample_name", SETTLEMENT_SAMPLES)
def test_fa3_settlement_samples_roundtrip(sample_name: str) -> None:
    assert_roundtrip(sample_name, InvoiceType.ROZ)


@pytest.mark.parametrize("sample_name", CORRECTION_SETTLEMENT_SAMPLES)
def test_fa3_correction_settlement_samples_roundtrip(sample_name: str) -> None:
    assert_roundtrip(sample_name, InvoiceType.CORRECTING_ROZ)
