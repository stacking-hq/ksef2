import pytest

from ksef2.domain.models.fa3.body import InvoiceType

from tests.e2e.mappers.fa3._roundtrip import assert_roundtrip


ADVANCE_SAMPLES = [
    "FA_3_Przykład_10.xml",
    "KSEF_03_ZAL.xml",
]

CORRECTION_ADVANCE_SAMPLES = [
    "FA_3_Przykład_11.xml",
    "FA_3_Przykład_12.xml",
    "FA_3_Przykład_13.xml",
    "KSEF_07_KOR_ZAL_A.xml",
    "KSEF_08_KOR_ZAL_B.xml",
]


@pytest.mark.parametrize("sample_name", ADVANCE_SAMPLES)
def test_fa3_advance_samples_roundtrip(sample_name: str) -> None:
    assert_roundtrip(sample_name, InvoiceType.ZAL)


@pytest.mark.parametrize("sample_name", CORRECTION_ADVANCE_SAMPLES)
def test_fa3_correction_advance_samples_roundtrip(sample_name: str) -> None:
    assert_roundtrip(sample_name, InvoiceType.CORRECTING_ZAL)
