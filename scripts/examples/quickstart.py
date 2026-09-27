"""Send a minimal invoice in the TEST environment.

This file is self-contained: copy it, run it, it works. Nothing here needs the
rest of ``scripts/examples``.

    uv run -m scripts.examples.quickstart

What it demonstrates:
- building a FA(3) invoice with ``FA3InvoiceBuilder``
- authenticating in TEST
- opening an online session
- sending an invoice with both context-manager and manual session handling
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import uuid4

from ksef2 import Client, Environment, FormSchema
from ksef2.fa3 import FA3InvoiceBuilder, VatRate

# KSeF TEST accepts any well-formed NIP together with a generated test
# certificate, so the quickstart needs no configuration. Pass
# ExampleConfig(seller_nip=...) to submit as another subject, for example the
# subject your own TEST credentials belong to.
SELLER_NIP = "5261040828"


def build_invoice(seller_nip: str) -> bytes:
    """Return a minimal FA(3) standard invoice issued by ``seller_nip``.

    Every call gets a fresh ``<P_2>`` number, because KSeF identifies an invoice
    by seller plus number and rejects a repeat with ``440 Duplikat faktury``.
    """
    builder = (
        FA3InvoiceBuilder()
        .header(system_info="ksef2 quickstart")
        .seller(
            name="KSeF2 example seller",
            tax_id=seller_nip,
            country_code="PL",
            address_line_1="Przykładowa 1",
        )
        .buyer(
            name="KSeF2 example buyer",
            country_code="PL",
            address_line_1="Przykładowa 2",
        )
        .standard()
        .issue_date(date.today())
        .invoice_number(f"KSEF2-QUICKSTART-{uuid4().hex}")
        .rows()
        .add_line(
            name="Example service",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("10.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
    )
    return builder.to_xml().encode("utf-8")


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    seller_nip: str = SELLER_NIP


def run(config: ExampleConfig) -> None:
    client = Client(config.environment)
    seller_nip = config.seller_nip
    auth = client.authentication.with_test_certificate(nip=seller_nip)

    # Two sends, two invoices. Sending one document twice would print a second
    # reference number for an invoice KSeF rejects as 440 Duplikat faktury, so
    # waiting for each invoice to be processed is what makes a duplicate visible
    # instead of silent.
    with auth.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice(invoice_xml=build_invoice(seller_nip))
        status = session.wait_for_invoice_ready(
            invoice_reference_number=result.reference_number
        )
        print(status.ksef_number)

    session = auth.online_session(form_code=FormSchema.FA3)
    try:
        result = session.send_invoice(invoice_xml=build_invoice(seller_nip))
        status = session.wait_for_invoice_ready(
            invoice_reference_number=result.reference_number
        )
        print(status.ksef_number)
    finally:
        session.close()


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
