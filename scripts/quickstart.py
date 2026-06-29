from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.fa3 import FA3InvoiceBuilder, VatRate


SELLER_NIP = "5261040828"
DOWNLOADS = Path("downloads")

invoice_number = f"QS/{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
invoice_xml = (
    FA3InvoiceBuilder()
    .header(system_info="ksef2 quickstart")
    .seller(
        name="Demo Seller Sp. z o.o.",
        tax_id=SELLER_NIP,
        country_code="PL",
        address_line_1="Prosta 1",
        address_line_2="00-001 Warszawa",
    )
    .buyer(
        name="Demo Buyer Sp. z o.o.",
        country_code="PL",
        address_line_1="Kwiatowa 2",
        address_line_2="00-002 Warszawa",
    )
    .standard()
    .issue_date(date.today())
    .issue_place("Warszawa")
    .invoice_number(invoice_number)
    .rows()
    .add_line(
        name="Consulting service",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        vat_rate=VatRate.VAT_23,
    )
    .done()
    .done()
    .to_xml()
    .encode("utf-8")
)

DOWNLOADS.mkdir(exist_ok=True)
(DOWNLOADS / "generated-invoice.xml").write_bytes(invoice_xml)

with Client(Environment.TEST) as client:
    auth = client.authentication.with_test_certificate(nip=SELLER_NIP)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        sent = session.send_invoice(invoice_xml=invoice_xml)
        print("Sent invoice:")
        print(sent.model_dump_json(indent=2))

        status = session.wait_for_invoice_ready(
            invoice_reference_number=sent.reference_number,
            timeout=120.0,
        )
        print("Invoice status:")
        print(status.model_dump_json(indent=2))

        upo_xml = session.get_invoice_upo_by_reference(
            invoice_reference_number=sent.reference_number,
        )
        (DOWNLOADS / "upo.xml").write_bytes(upo_xml)
        print("Saved downloads/upo.xml")

    if status.ksef_number is None:
        raise RuntimeError("KSeF did not assign an invoice number.")

    downloaded_xml = auth.invoices.wait_for_invoice_download(
        ksef_number=status.ksef_number,
        timeout=120.0,
    )
    (DOWNLOADS / "processed-invoice.xml").write_bytes(downloaded_xml)
    print("Saved downloads/processed-invoice.xml")
