import code
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from ksef2.domain.models.fa3.body import VatRate
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder


def build_sample_1_builder() -> StandardInvoiceBuilder:
    builder = StandardInvoiceBuilder()
    _ = (
        builder.header(
            generation_timestamp=datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
            system_info="SampleBuilder",
        )
        .seller(
            name="ABC AGD sp. z o. o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Kwiatowa 1 m. 2",
            address_line_2="00-001 Warszawa",
            email="abc@abc.pl",
            phone="667444555",
        )
        .buyer(
            name="F.H.U. Jan Kowalski",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Polna 1",
            address_line_2="00-001 Warszawa",
            customer_number="fdfd778343",
            email="jan@kowalski.pl",
            phone="555777999",
        )
    )

    _ = (
        builder.footer()
        .add_information("Kapital zakladowy 5 000 000")
        .add_registry(
            krs="0000099999",
            regon="999999999",
            bdo="000099999",
        )
        .done()
    )

    _ = (
        builder.standard()
        .issue_date(date(2026, 2, 15))
        .issue_place("Warszawa")
        .invoice_number("FV2026/02/150")
        .date_of_supply(date(2026, 1, 27))
        .mark_fp()
        .add_description(
            key="preferowane godziny dowozu",
            value="dni robocze 17:00 - 20:00",
        )
        .rows()
        .add_line(
            name="lodowka Zimnotech mk1",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("1626.01"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339990",
        )
        .add_line(
            name="wniesienie sprzetu",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("40.65"),
            vat_rate=VatRate.VAT_23,
            unique_id="aaaa111133339991",
        )
        .add_line(
            name="promocja lodowka pelna mleka",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("0.95"),
            vat_rate=VatRate.VAT_5,
            unique_id="aaaa111133339992",
        )
        .done()
        .payment()
        .via("bank_transfer")
        .already_paid(date(2026, 1, 27))
        .done()
        .transaction()
        .add_order(order_date=date(2026, 1, 26), order_number="4354343")
        .done()
        .done()
    )
    return builder


def build_sample_1_xml() -> str:
    return build_sample_1_builder().to_xml()


def write_sample_1_xml(path: str | Path = "output/new_fa3_sample_1.xml") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_sample_1_xml(), encoding="utf-8")
    return target


def main() -> int:
    banner = (
        "New FA3 builder REPL\n"
        "Available symbols:\n"
        "  - StandardInvoiceBuilder\n"
        "  - build_sample_1_builder()\n"
        "  - build_sample_1_xml()\n"
        "  - write_sample_1_xml(path='output/new_fa3_sample_1.xml')\n"
    )
    local_vars = {
        "StandardInvoiceBuilder": StandardInvoiceBuilder,
        "build_sample_1_builder": build_sample_1_builder,
        "build_sample_1_xml": build_sample_1_xml,
        "write_sample_1_xml": write_sample_1_xml,
    }
    code.InteractiveConsole(locals=local_vars).interact(banner=banner)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
