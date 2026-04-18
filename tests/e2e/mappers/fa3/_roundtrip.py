from decimal import Decimal
from pathlib import Path

from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3 import KsefInvoice
from ksef2.domain.models.fa3.body import InvoiceType
from ksef2.infra.mappers.invoices.fa3.domain.invoice import to_spec as invoice_to_spec
from ksef2.infra.mappers.invoices.fa3.spec.invoice import from_spec as invoice_from_spec
from ksef2.infra.schema.fa3.models.schemat import Faktura


SAMPLES_DIR = Path(__file__).resolve().parents[4] / "schemas" / "FA3" / "samples"

SUMMARY_FIELDS = [
    "p_13_1",
    "p_14_1",
    "p_14_1_w",
    "p_13_2",
    "p_14_2",
    "p_14_2_w",
    "p_13_3",
    "p_14_3",
    "p_14_3_w",
    "p_13_4",
    "p_14_4",
    "p_14_4_w",
    "p_13_5",
    "p_14_5",
    "p_13_6_1",
    "p_13_6_2",
    "p_13_6_3",
    "p_13_7",
    "p_13_8",
    "p_13_9",
    "p_13_10",
    "p_13_11",
    "p_15",
    "p_15_zk",
]

TEXT_FIELDS = [
    "p_1",
    "p_1_m",
    "p_2",
    "p_6",
    "kod_waluty",
    "rodzaj_faktury",
]


def load_sample(sample_name: str) -> Faktura:
    parser = XmlParser()
    return parser.from_bytes((SAMPLES_DIR / sample_name).read_bytes(), Faktura)


def roundtrip(sample_name: str) -> tuple[Faktura, KsefInvoice, Faktura, KsefInvoice]:
    original_spec = load_sample(sample_name)
    domain_invoice = invoice_from_spec(original_spec)
    roundtripped_spec = invoice_to_spec(domain_invoice)
    roundtripped_domain_invoice = invoice_from_spec(roundtripped_spec)
    return original_spec, domain_invoice, roundtripped_spec, roundtripped_domain_invoice


def assert_roundtrip(sample_name: str, expected_invoice_type: InvoiceType) -> None:
    original_spec, domain_invoice, roundtripped_spec, roundtripped_domain_invoice = (
        roundtrip(sample_name)
    )

    assert domain_invoice == roundtripped_domain_invoice
    assert domain_invoice.body.invoice_type is expected_invoice_type
    assert roundtripped_domain_invoice.body.invoice_type is expected_invoice_type

    for field_name in TEXT_FIELDS:
        assert getattr(roundtripped_spec.fa, field_name) == getattr(
            original_spec.fa, field_name
        )

    for field_name in SUMMARY_FIELDS:
        assert_decimal_field_equal(
            getattr(roundtripped_spec.fa, field_name),
            getattr(original_spec.fa, field_name),
            field_name,
        )


def assert_decimal_field_equal(
    actual: str | Decimal | None,
    expected: str | Decimal | None,
    field_name: str,
) -> None:
    if expected is None or actual is None:
        assert actual == expected, field_name
        return
    assert Decimal(actual) == Decimal(expected), field_name
