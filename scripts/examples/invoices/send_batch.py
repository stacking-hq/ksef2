"""Prepare a batch ZIP, upload it, and inspect the processed session in TEST.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP

What it demonstrates:
- preparing multiple FA(3) invoices for a batch session, each with its own invoice
  number, because KSeF rejects a repeated number from one seller with 440
  Duplikat faktury
- opening a batch session and uploading encrypted parts
- closing the session and waiting until processing completes
- listing processed invoices and downloading the collective UPO
"""

from dataclasses import dataclass

from ksef2 import Client, Environment, FormSchema
from scripts.examples._common import example_batch_invoices, example_seller_nip


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    invoice_count: int = 2
    poll_interval: float = 2.0
    status_timeout: float = 120.0
    seller_nip: str | None = None


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    seller_nip = config.seller_nip or example_seller_nip()

    auth = client.authentication.with_test_certificate(nip=seller_nip)
    invoices = example_batch_invoices(
        seller_nip=seller_nip,
        count=config.invoice_count,
    )

    prepared_batch = auth.batch.prepare(invoices, form_code=FormSchema.FA3)
    print(
        "Prepared batch with "
        f"{len(prepared_batch.invoices)} invoice(s) and "
        f"{len(prepared_batch.parts)} encrypted part(s)"
    )

    with auth.batch_session(prepared_batch=prepared_batch) as session:
        print(f"Opened batch session: {session.reference_number}")
        session.upload_parts()
        print("Uploaded all batch parts")

    print("Closed batch session and started processing")

    status = session.wait(
        timeout=config.status_timeout,
        poll_interval=config.poll_interval,
    )
    print(
        "Batch session completed: "
        f"{status.status.code} {status.status.description} "
        f"(total={status.invoice_count}, ok={status.successful_invoice_count}, "
        f"failed={status.failed_invoice_count})"
    )

    if status.failed_invoice_count:
        print("Batch completed with failed invoices; inspect the status output.")

    invoices_page = session.list_invoices()
    for invoice in invoices_page.invoices:
        print(
            "Invoice result: "
            f"ref={invoice.reference_number} "
            f"ksef={invoice.ksef_number} "
            f"status={invoice.status.code} {invoice.status.description}"
        )

    for number, upo_xml in enumerate(session.download_upo(), start=1):
        print(f"Downloaded collective UPO page {number} of size {len(upo_xml)} bytes")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
