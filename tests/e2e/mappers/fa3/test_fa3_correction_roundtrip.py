import pytest

from ksef2.domain.models.fa3.body import InvoiceType

from tests.e2e.mappers.fa3._roundtrip import assert_roundtrip


CORRECTION_SAMPLES = [
    "FA_3_Przykład_2.xml",
    "FA_3_Przykład_3.xml",
    "FA_3_Przykład_5.xml",
    "FA_3_Przykład_6.xml",
    "FA_3_Przykład_7.xml",
    "KSEF_02_KOR.xml",
]


@pytest.mark.parametrize("sample_name", CORRECTION_SAMPLES)
def test_fa3_correction_samples_roundtrip(sample_name: str) -> None:
    assert_roundtrip(sample_name, InvoiceType.CORRECTING)
