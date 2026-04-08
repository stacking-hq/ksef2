import pytest

from ksef2.domain.models.fa3.body import InvoiceType

from tests.e2e.mappers.fa3._roundtrip import assert_roundtrip


SIMPLIFIED_SAMPLES = [
    "FA_3_Przykład_15.xml",
    "FA_3_Przykład_16.xml",
    "KSEF_04_UPR.xml",
]


@pytest.mark.parametrize("sample_name", SIMPLIFIED_SAMPLES)
def test_fa3_simplified_samples_roundtrip(sample_name: str) -> None:
    assert_roundtrip(sample_name, InvoiceType.UPR)
