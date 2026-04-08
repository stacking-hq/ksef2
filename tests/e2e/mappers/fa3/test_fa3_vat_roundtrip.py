import pytest

from ksef2.domain.models.fa3.body import InvoiceType

from tests.e2e.mappers.fa3._roundtrip import assert_roundtrip


VAT_SAMPLES = [
    "FA_3_Przykład_1.xml",
    "FA_3_Przykład_4.xml",
    "FA_3_Przykład_8.xml",
    "FA_3_Przykład_9.xml",
    "FA_3_Przykład_21.xml",
    "FA_3_Przykład_22.xml",
    "FA_3_Przykład_23.xml",
    "FA_3_Przykład_24.xml",
    "FA_3_Przykład_25.xml",
    "FA_3_Przykład_26.xml",
    "Fa_3_Przykład_19.xml",
    "Fa_3_Przykład_20.xml",
    "KSEF_01_VAT_STANDARD.xml",
    "KSEF_05_WDT.xml",
    "KSEF_06_EXP.xml",
]


@pytest.mark.parametrize("sample_name", VAT_SAMPLES)
def test_fa3_vat_samples_roundtrip(sample_name: str) -> None:
    assert_roundtrip(sample_name, InvoiceType.VAT)
