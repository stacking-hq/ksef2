"""Send one invoice in TEST, wait for processing, and download it back.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP
- set KSEF2_EXAMPLE_INVOICE_XML to a FA(3) XML file valid for that seller

What it demonstrates:
- invoice submission in an online session
- waiting for processing and downloading by KSeF number
"""

from dataclasses import dataclass
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from scripts.examples._common import example_invoice_xml_path, example_seller_nip


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    seller_nip: str | None = None
    invoice_path: Path | None = None


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    seller_nip = config.seller_nip or example_seller_nip()
    invoice_path = config.invoice_path or example_invoice_xml_path()
    invoice_xml = invoice_path.read_bytes()

    auth = client.authentication.with_test_certificate(nip=seller_nip)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice(invoice_xml=invoice_xml)

        print(f"Invoice has been sent, reference number: {result.reference_number}")

        status = session.wait_for_invoice_ready(
            invoice_reference_number=result.reference_number
        )

        if status.ksef_number:
            downloaded_invoice = auth.invoices.wait_for_invoice_download(
                ksef_number=status.ksef_number
            )
            print(f"Downloaded invoice of size {len(downloaded_invoice)} bytes")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
