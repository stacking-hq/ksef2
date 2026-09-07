"""Submit a batch with one high-level call and inspect the processed session in TEST.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP
- set KSEF2_EXAMPLE_INVOICE_XML to a FA(3) XML file valid for that seller

What it demonstrates:
- preparing an XML invoice in memory
- submitting a batch with `auth.batch.submit_batch()`
- polling until the batch session completes
- listing processed invoices and downloading the collective UPO
"""

from dataclasses import dataclass
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.models import BatchInvoice
from scripts.examples._common import example_invoice_xml_path, example_seller_nip


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    poll_interval: float = 2.0
    status_timeout: float = 120.0
    seller_nip: str | None = None
    invoice_path: Path | None = None


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        seller_nip = config.seller_nip or example_seller_nip()
        invoice_path = config.invoice_path or example_invoice_xml_path()
        invoice_xml = invoice_path.read_bytes()

        auth = client.authentication.with_test_certificate(nip=seller_nip)
        invoices = [BatchInvoice(file_name=invoice_path.name, content=invoice_xml)]

        state = auth.batch.submit_batch(
            invoices=invoices,
            form_code=FormSchema.FA3,
        )
        print(f"Submitted batch session: {state.reference_number}")

        status = auth.batch.wait_for_completion(
            session=state,
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

        invoices_page = auth.batch.list_invoices(session=state)
        for invoice in invoices_page.invoices:
            print(
                "Invoice result: "
                f"ref={invoice.reference_number} "
                f"ksef={invoice.ksef_number} "
                f"status={invoice.status.code} {invoice.status.description}"
            )

        if status.upo and status.upo.pages:
            for upo_page in status.upo.pages:
                upo_xml = auth.batch.get_upo(
                    session=state,
                    upo_reference_number=upo_page.reference_number,
                )
                print(
                    "Downloaded collective UPO page "
                    f"{upo_page.reference_number} of size {len(upo_xml)} bytes"
                )


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
