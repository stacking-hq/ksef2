from datetime import date
from decimal import Decimal
from pathlib import Path

from xsdata.formats.dataclass.parsers import XmlParser

from ksef2.domain.models.fa3.body import SaleCategory, VatTreatment
from ksef2.infra.mappers.invoices.fa3.domain.invoice import to_spec as invoice_to_spec
from ksef2.infra.mappers.invoices.fa3.spec.invoice import from_spec as invoice_from_spec
from ksef2.infra.schema.fa3.models.schemat import Faktura


SAMPLE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "FA3"
    / "samples"
    / "KSEF_01_VAT_STANDARD.xml"
)


def test_standard_invoice_sample_roundtrips_between_spec_and_domain() -> None:
    parser = XmlParser()
    original_spec = parser.from_bytes(SAMPLE_PATH.read_bytes(), Faktura)

    domain_invoice = invoice_from_spec(original_spec)

    roundtripped_spec = invoice_to_spec(domain_invoice)

    roundtripped_domain_invoice = invoice_from_spec(roundtripped_spec)

    assert domain_invoice == roundtripped_domain_invoice

    assert domain_invoice.body.invoice_number == original_spec.fa.p_2
    assert domain_invoice.body.issue_date == date.fromisoformat(original_spec.fa.p_1)
    assert len(domain_invoice.body.rows) == 1

    row = domain_invoice.body.rows[0]
    assert row.name == "Laptop Dell XPS 15"
    assert row.sale_category is SaleCategory.RATE_23
    assert row.vat_classification is not None
    assert row.vat_classification.treatment is VatTreatment.TAXABLE
    assert row.vat_classification.rate == Decimal("23")

    assert roundtripped_spec.fa.kod_waluty == original_spec.fa.kod_waluty
    assert roundtripped_spec.fa.rodzaj_faktury == original_spec.fa.rodzaj_faktury
    assert roundtripped_spec.fa.p_2 == original_spec.fa.p_2
    assert roundtripped_spec.fa.p_13_1 == original_spec.fa.p_13_1
    assert roundtripped_spec.fa.p_14_1 == original_spec.fa.p_14_1
    assert Decimal(roundtripped_spec.fa.p_15) == Decimal(original_spec.fa.p_15)

    original_row = original_spec.fa.fa_wiersz[0]
    roundtripped_row = roundtripped_spec.fa.fa_wiersz[0]
    assert roundtripped_row.p_7 == original_row.p_7
    assert roundtripped_row.p_12 == original_row.p_12
    assert roundtripped_row.p_11 == original_row.p_11

    # The mapper enriches the outgoing spec with computed gross/VAT fields.
    assert roundtripped_row.p_11_vat == "934.96"
    assert roundtripped_row.p_11_a == "5000.00"
