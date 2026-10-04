"""Send an invoice, wait for processing, export matching invoices, and download the package.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP

What it demonstrates:
- invoice submission and waiting for processing
- seller-side invoice export
- saving the decrypted export package to disk
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.models import InvoicesFilter
from scripts.examples._common import (
    example_invoice_xml,
    example_seller_nip,
    repo_root,
)


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    poll_interval: float = 2.0
    status_timeout: float = 60.0
    export_timeout: float = 120.0
    seller_nip: str | None = None
    download_dir: Path = field(
        default_factory=lambda: repo_root() / "downloads" / "invoice_export"
    )


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    seller_nip = config.seller_nip or example_seller_nip()
    invoice_xml = example_invoice_xml(seller_nip=seller_nip)

    auth = client.authentication.with_test_certificate(nip=seller_nip)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        submission = session.send_invoice(invoice_xml)
        print(f"Invoice sent: {submission.reference_number}")

        status = submission.wait(
            timeout=config.status_timeout,
            poll_interval=config.poll_interval,
        )
        print(f"Invoice processed as KSeF number: {status.ksef_number}")

    job = auth.invoices.export(
        InvoicesFilter.for_seller(
            date_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
            date_to=datetime.now(tz=timezone.utc),
        )
    )
    print(f"Export scheduled: {job.reference_number}")

    package = job.wait(
        timeout=config.export_timeout,
        poll_interval=config.poll_interval,
    )
    for ksef_number, _xml in package.invoices():
        print(f"Exported invoice: {ksef_number}")

    for path in package.save(config.download_dir):
        print(f"Saved: {path} ({path.stat().st_size} bytes)")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
