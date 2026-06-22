"""Send a minimal invoice in the TEST environment.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP
- set KSEF2_EXAMPLE_INVOICE_XML to a FA(3) XML file valid for that seller

What it demonstrates:
- authenticating in TEST
- opening an online session
- sending an invoice with both context-manager and manual session handling
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
    client = Client(config.environment)
    seller_nip = config.seller_nip or example_seller_nip()
    invoice_path = config.invoice_path or example_invoice_xml_path()
    invoice_xml = invoice_path.read_bytes()

    auth = client.authentication.with_test_certificate(nip=seller_nip)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice(invoice_xml=invoice_xml)
        print(result.reference_number)

    session = auth.online_session(form_code=FormSchema.FA3)
    try:
        result = session.send_invoice(invoice_xml=invoice_xml)
        print(result.reference_number)
    finally:
        session.close()


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
