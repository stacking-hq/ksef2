from tests.integration.builders.helpers import load_sample, sample_path

from ksef2.infra.mappers.invoices.fa3.spec.invoice import from_spec


ADVANCE_SAMPLES = [
    "FA_3_Przykład_10.xml",
    "KSEF_03_ZAL.xml",
]


def test_fa3_przyklad_10():
    sample = load_sample(sample_path("FA_3_Przykład_10.xml"))

    mapped_samples = from_spec(sample)

    print(mapped_samples.model_dump_json(indent=2))


CORRECTION_ADVANCE_SAMPLES = [
    "FA_3_Przykład_11.xml",
    "FA_3_Przykład_12.xml",
    "FA_3_Przykład_13.xml",
    "KSEF_07_KOR_ZAL_A.xml",
    "KSEF_08_KOR_ZAL_B.xml",
]
