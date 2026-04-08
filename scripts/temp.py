from datetime import date, datetime, timezone
from decimal import Decimal

from ksef2.domain.models.fa3.body import VatRate
from ksef2.services import FA3InvoiceBuilder
from ksef2.services.builders.fa3.payloads import standard
from ksef2.services.builders.fa3.payment import payment


def build_standard_builder() -> FA3InvoiceBuilder:
    builder = (
        FA3InvoiceBuilder()
        .header(
            generation_timestamp=datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
            system_info="TEMP",
        )
        .seller(
            name="TEMP SELLER sp. z o.o.",
            tax_id="9999999999",
            country_code="PL",
            address_line_1="ul. Testowa 1",
            address_line_2="00-001 Warszawa",
        )
        .buyer(
            name="TEMP BUYER sp. z o.o.",
            tax_id="1111111111",
            country_code="PL",
            address_line_1="ul. Testowa 2",
            address_line_2="00-002 Warszawa",
        )
        .body(
            issue_date=date(2026, 1, 1),
            issue_place="Warszawa",
            invoice_number="FV/2026/01/0001",
            date_of_supply=date(2026, 1, 1),
        )
        .add_line(
            name="Test item",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("100"),
            vat_rate=VatRate.VAT_23,
            unique_id="TEMP-LINE-001",
        )
        .body(
            standard().payment(
                payment(form="bank_transfer").add_term(due_on=date(2026, 1, 15))
            )
        )
        .build()
    )
    return builder


def build_invoice() -> None:
    invoice = build_standard_builder().build()
    _ = invoice
