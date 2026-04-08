import pytest
from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.infra.schema.fa3.models.schemat import Faktura
from tests.integration.builders.helpers import load_sample

CORRECTION_SAMPLES = [
    "FA_3_Przykład_2.xml",
    "FA_3_Przykład_3.xml",
    "FA_3_Przykład_5.xml",
    "FA_3_Przykład_6.xml",
    "FA_3_Przykład_7.xml",
    "KSEF_02_KOR.xml",
]


def _assert_sample(sample_name: str) -> None:
    parser = XmlParser()
    expected = load_sample(sample_name)
    builder = _build_from_sample(sample_name)
    actual = builder.to_spec()
    expected = normalize_expected(expected, actual)

    assert actual == expected
    assert parser.from_bytes(builder.to_xml().encode("utf-8"), Faktura) == expected


@pytest.mark.integration
@pytest.mark.parametrize("sample_name", CORRECTION_SAMPLES)
def test_new_fa3_correction_samples(sample_name: str) -> None:
    _assert_sample(sample_name)
