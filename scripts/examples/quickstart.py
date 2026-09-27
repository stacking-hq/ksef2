"""Send a minimal invoice in the TEST environment.

Needs no setup; run it as-is:

    uv run -m scripts.examples.quickstart

What it demonstrates:
- authenticating in TEST
- opening an online session
- sending an invoice with both context-manager and manual session handling
"""

from dataclasses import dataclass

from ksef2 import Client, Environment, FormSchema
from scripts.examples._common import example_invoice_xml

# KSeF TEST accepts any well-formed NIP together with a generated test
# certificate, so the quickstart needs no configuration. Pass
# ExampleConfig(seller_nip=...) to submit as another subject, for example the
# subject your own TEST credentials belong to.
SELLER_NIP = "5261040828"


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    seller_nip: str = SELLER_NIP


def run(config: ExampleConfig) -> None:
    client = Client(config.environment)
    seller_nip = config.seller_nip
    auth = client.authentication.with_test_certificate(nip=seller_nip)

    # Two sends, two invoices. KSeF keys an invoice on seller plus <P_2> and
    # rejects a repeat with 440 Duplikat faktury, and this example does not poll
    # invoice status, so one document sent twice would print a reference number
    # for an invoice that never landed.
    with auth.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice(
            invoice_xml=example_invoice_xml(seller_nip=seller_nip)
        )
        print(result.reference_number)

    session = auth.online_session(form_code=FormSchema.FA3)
    try:
        result = session.send_invoice(
            invoice_xml=example_invoice_xml(seller_nip=seller_nip)
        )
        print(result.reference_number)
    finally:
        session.close()


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
