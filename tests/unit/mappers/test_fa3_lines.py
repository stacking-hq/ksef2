from datetime import date
from decimal import Decimal

from ksef2.domain.models.fa3 import AdvanceOrderLine
from ksef2.domain.models.fa3.body import InvoiceRow, SaleCategory, VatRate
from ksef2.infra.mappers.invoices.fa3.domain.lines import to_spec as lines_to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaFaWiersz,
    FakturaFaZamowienieZamowienieWiersz,
    Tgtu,
    ToznaczenieProcedury,
    ToznaczenieProceduryZ,
    TstawkaPodatku,
)


def test_lines_to_spec_maps_complete_invoice_line() -> None:
    output = lines_to_spec(
        InvoiceRow(
            name="Laptop",
            quantity=Decimal("2"),
            unit_price_net=Decimal("3500.12345678"),
            net_amount=Decimal("7000.25"),
            vat_rate=VatRate.VAT_23,
            vat_amount=Decimal("1600.55"),
            unique_id="line-001",
            supply_date=date(2026, 3, 29),
            sku="SKU-001",
            gtin="05901234567890",
            pkwiu="62.01.11.0",
            cn="84713000",
            pkob="1122",
            unit_price_gross=Decimal("4305.15"),
            discount_amount=Decimal("100.25"),
            gross_amount=Decimal("8600.80"),
            vat_rate_xii=Decimal("23"),
            annex_15_marker=True,
            excise_amount=Decimal("0.00"),
            gtu_code="GTU_06",
            procedure="TT_D",
            currency_exchange_rate=Decimal("4.123456"),
            before_correction=True,
        ),
        row_number=7,
    )

    assert isinstance(output, FakturaFaFaWiersz)
    assert output.nr_wiersza_fa == 7
    assert output.uu_id == "line-001"
    assert output.p_6_a == "2026-03-29"
    assert output.p_7 == "Laptop"
    assert output.indeks == "SKU-001"
    assert output.gtin == "05901234567890"
    assert output.pkwi_u == "62.01.11.0"
    assert output.cn == "84713000"
    assert output.pkob == "1122"
    assert output.p_8_a == "szt"
    assert output.p_8_b == "2"
    assert output.p_9_a == "3500.12345678"
    assert output.p_9_b == "4305.15"
    assert output.p_10 == "100.25"
    assert output.p_11 == "7000.25"
    assert output.p_11_a == "8600.80"
    assert output.p_11_vat == "1600.55"
    assert output.p_12 == TstawkaPodatku.VALUE_23
    assert output.p_12_xii == Decimal("23")
    assert output.p_12_zal_15 == Twybor1.VALUE_1
    assert output.kwota_akcyzy == "0.00"
    assert output.gtu == Tgtu.GTU_06
    assert output.procedura == ToznaczenieProcedury.TT_D
    assert output.kurs_waluty == "4.123456"
    assert output.stan_przed == Twybor1.VALUE_1


def test_lines_to_spec_maps_optional_fields_to_none() -> None:
    output = lines_to_spec(
        InvoiceRow(
            name="Consulting service",
            quantity=Decimal("10"),
            unit_price_net=Decimal("100.00"),
            net_amount=Decimal("1000.00"),
            vat_rate=VatRate.EXEMPT,
            sale_category=SaleCategory.EXEMPT,
            vat_amount=Decimal("0.00"),
        ),
        row_number=1,
    )

    assert output.nr_wiersza_fa == 1
    assert output.p_7 == "Consulting service"
    assert output.p_8_a == "szt"
    assert output.p_8_b == "10"
    assert output.p_9_a == "100.00"
    assert output.p_11 == "1000.00"
    assert output.p_11_vat is None
    assert output.p_12 == TstawkaPodatku.ZW
    assert output.uu_id is None
    assert output.p_6_a is None
    assert output.p_10 is None
    assert output.gtu is None
    assert output.procedura is None
    assert output.p_12_zal_15 is None
    assert output.stan_przed is None


def test_lines_to_spec_maps_zero_wdt_bucket_to_brochure_specific_value() -> None:
    output = lines_to_spec(
        InvoiceRow(
            name="WDT supply",
            quantity=Decimal("1"),
            unit_price_net=Decimal("500.00"),
            net_amount=Decimal("500.00"),
            vat_rate=VatRate.VAT_0,
            sale_category=SaleCategory.ZERO_WDT,
            vat_amount=Decimal("0.00"),
        ),
        row_number=3,
    )

    assert output.p_12 == TstawkaPodatku.VALUE_0_WDT


def test_lines_to_spec_maps_advance_order_line_to_zamowienie_row() -> None:
    output = lines_to_spec(
        AdvanceOrderLine(
            name="Dom jednorodzinny",
            quantity=Decimal("1"),
            unit_of_measure="usl",
            gross_amount=Decimal("1230.00"),
            vat_rate=VatRate.VAT_23,
            procedure="TT_D",
            annex_15_marker=True,
        ),
        row_number=1,
    )

    assert isinstance(output, FakturaFaZamowienieZamowienieWiersz)
    assert output.nr_wiersza_zam == 1
    assert output.p_7_z == "Dom jednorodzinny"
    assert output.p_11_netto_z == "1000.00"
    assert output.p_11_vat_z == "230.00"
    assert output.p_12_z == TstawkaPodatku.VALUE_23
    assert output.procedura_z == ToznaczenieProceduryZ.TT_D
    assert output.p_12_z_zal_15 == Twybor1.VALUE_1
