"""Existing XML uses XSD validation; newly built drafts retain business rules."""

from decimal import Decimal
from pathlib import Path

import pytest

from ksef2 import KSeFInvoiceRenderingError, KSeFValidationError
from ksef2.fa3 import InvoiceBuilder, parse_invoice_xml
from ksef2._domain.models.fa3.body import InvoiceRow, InvoiceType
from ksef2.renderers import InvoiceXSLTRenderer

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("name, amount", [("zal", "500.00"), ("kor-zero", "-1230.00")])
def test_accepted_xml_parses_renders_and_builds(name: str, amount: str) -> None:
    xml = (FIXTURES / f"{name}.xml").read_bytes()
    invoice = parse_invoice_xml(xml, validate=True)
    assert invoice.total_gross == Decimal(amount)
    renderer = InvoiceXSLTRenderer()
    assert "REGRESSION/1" in renderer.render_from_string(xml)
    assert "REGRESSION/1" in renderer.render_from_path(FIXTURES / f"{name}.xml")
    rebuilt = parse_invoice_xml(InvoiceBuilder.from_invoice(invoice).to_xml())
    assert rebuilt.total_gross == Decimal(amount)
    if name == "zal":
        assert invoice.body.order is not None
        assert invoice.body.order.total_value == Decimal("1230.00")
    else:
        assert rebuilt.body.rows[1].quantity == 0
        assert not rebuilt.body.rows[1].before_correction


@pytest.mark.parametrize("before", [True, False])
def test_zero_quantity_requires_kor_after_correction(before: bool) -> None:
    invoice = parse_invoice_xml((FIXTURES / "kor-zero.xml").read_bytes())
    data = invoice.body.model_dump()
    data["rows"] = [InvoiceRow(quantity=Decimal(0), before_correction=before)]
    if before:
        with pytest.raises(KSeFValidationError, match="quantity"):
            type(invoice.body).model_validate(data)
    else:
        assert type(invoice.body).model_validate(data).rows[0].quantity == 0
    data["invoice_type"] = InvoiceType.VAT
    data["correction"] = None
    with pytest.raises(KSeFValidationError, match="quantity"):
        type(invoice.body).model_validate(data)


def test_inspection_does_not_apply_other_draft_business_rules() -> None:
    xml = (
        (FIXTURES / "kor-zero.xml")
        .read_bytes()
        .replace(b"<P_8B>1</P_8B>", b"<P_8B>0</P_8B>")
    )
    assert parse_invoice_xml(xml).body.rows[0].quantity == 0
    assert "REGRESSION/1" in InvoiceXSLTRenderer().render_from_string(xml)
    with pytest.raises(KSeFValidationError, match="quantity"):
        InvoiceBuilder.from_invoice(parse_invoice_xml(xml)).build()


@pytest.mark.parametrize("render", [False, True])
def test_fa2_has_actionable_schema_error(render: bool) -> None:
    xml = (FIXTURES / "fa2.xml").read_bytes()
    error_type = KSeFInvoiceRenderingError if render else KSeFValidationError
    with pytest.raises(error_type, match=r"FA\(2\) is unsupported") as caught:
        if render:
            InvoiceXSLTRenderer().render_from_string(xml)
        else:
            parse_invoice_xml(xml)
    error = caught.value
    assert error.hint and "FA(2)" in error.hint
    assert error.context["detected_schema"] == "FA(2)"
    assert (
        error.context["detected_namespace"]
        == "http://crd.gov.pl/wzor/2023/06/29/12648/"
    )
    assert error.context["field_path"] == "/Faktura"
    assert error.context["local_rule"] is False
    assert error.context["accepted_by_ksef"] is None
    assert error.__cause__ is not None


@pytest.mark.parametrize("render", [False, True])
def test_xsd_failure_has_field_path_and_hint(render: bool) -> None:
    xml = (
        (FIXTURES / "zal.xml")
        .read_bytes()
        .replace(b"<P_15>500.00</P_15>", b"<P_15>oops</P_15>")
    )
    error_type = KSeFInvoiceRenderingError if render else KSeFValidationError
    with pytest.raises(error_type) as caught:
        if render:
            InvoiceXSLTRenderer(validate=True).render_from_string(xml)
        else:
            parse_invoice_xml(xml, validate=True)
    assert caught.value.hint
    assert caught.value.context["detected_schema"] == "FA(3)"
    assert caught.value.context["field_path"] != "/Faktura"
    assert caught.value.context["local_rule"] is False


def test_draft_failure_has_local_rule_hint() -> None:
    with pytest.raises(KSeFValidationError) as caught:
        InvoiceRow(name="invalid\x00")
    assert caught.value.field_path == "name"
    assert caught.value.local_rule is True
    assert caught.value.accepted_by_ksef is None
    assert caught.value.hint and "accepted by KSeF" in caught.value.hint


def test_zal_declared_order_value_is_independent_of_supplied_lines() -> None:
    xml = (
        (FIXTURES / "zal.xml")
        .read_bytes()
        .replace(b"<WartoscZamowienia>1230.00", b"<WartoscZamowienia>2000.00")
    )
    invoice = parse_invoice_xml(xml, validate=True)
    assert invoice.total_gross == Decimal("500.00")
    assert "REGRESSION/1" in InvoiceXSLTRenderer().render_from_string(xml)
    rebuilt = parse_invoice_xml(InvoiceBuilder.from_invoice(invoice).to_xml())
    assert rebuilt.body.order is not None
    assert rebuilt.body.order.total_value == Decimal("2000.00")


def test_xsd_validation_is_opt_in_for_inspection_and_rendering() -> None:
    xml = (
        (FIXTURES / "zal.xml")
        .read_bytes()
        .replace(b"<P_15>500.00</P_15>", b"<P_15>500.001</P_15>")
    )
    assert parse_invoice_xml(xml).total_gross == Decimal("500.001")
    assert "REGRESSION/1" in InvoiceXSLTRenderer().render_from_string(xml)
    with pytest.raises(KSeFValidationError):
        parse_invoice_xml(xml, validate=True)
    with pytest.raises(KSeFInvoiceRenderingError):
        InvoiceXSLTRenderer(validate=True).render_from_string(xml)


@pytest.mark.parametrize("name", ["zal", "kor-zero"])
def test_validated_rendering_keeps_footer_and_watermark(name: str) -> None:
    xml = (FIXTURES / f"{name}.xml").read_bytes()
    renderer = InvoiceXSLTRenderer(
        validate=True, footer_text="Local footer", watermark_text="Draft preview"
    )
    html = renderer.render_from_string(xml)
    assert "REGRESSION/1" in html
    assert "Local footer" in html
    assert "Draft preview" in html
    invalid = xml.replace(
        b"<KodWaluty>PLN</KodWaluty>", b"<KodWaluty>INVALID</KodWaluty>"
    )
    with pytest.raises(KSeFInvoiceRenderingError) as caught:
        renderer.render_from_string(invalid)
    assert caught.value.detected_schema == "FA(3)"
    assert caught.value.local_rule is False
