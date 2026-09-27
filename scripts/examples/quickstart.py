"""Send a minimal invoice in the TEST environment.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP

What it demonstrates:
- authenticating in TEST
- opening an online session
- sending an invoice with both context-manager and manual session handling
"""

from dataclasses import dataclass
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from scripts.examples._common import (
    example_invoice_source_path,
    example_invoice_xml,
    example_seller_nip,
)


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    seller_nip: str | None = None
    invoice_path: Path | None = None


def run(config: ExampleConfig) -> None:
    client = Client(config.environment)
    seller_nip = config.seller_nip or example_seller_nip()
    source_path = example_invoice_source_path(config.invoice_path)

    # Each send needs its own invoice, so each gets its own <P_2>: KSeF keys an
    # invoice on seller plus number and rejects the repeat with 440 Duplikat
    # faktury. Reusing one document here prints two reference numbers while the
    # second invoice never lands, because this example does not poll status.
    first_invoice = example_invoice_xml(seller_nip=seller_nip, source_path=source_path)
    second_invoice = example_invoice_xml(seller_nip=seller_nip, source_path=source_path)

    auth = client.authentication.with_test_certificate(nip=seller_nip)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice(invoice_xml=first_invoice)
        print(result.reference_number)

    session = auth.online_session(form_code=FormSchema.FA3)
    try:
        result = session.send_invoice(invoice_xml=second_invoice)
        print(result.reference_number)
    finally:
        session.close()


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
