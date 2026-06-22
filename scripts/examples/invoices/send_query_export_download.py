"""Send an invoice, wait for processing, export matching invoices, and download the package.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP
- set KSEF2_EXAMPLE_INVOICE_XML to a FA(3) XML file valid for that seller

What it demonstrates:
- invoice submission and status polling
- seller-side invoice export
- downloading export packages to disk
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter
from scripts.examples._common import (
    example_invoice_xml_path,
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
    invoice_path: Path | None = None
    download_dir: Path = field(
        default_factory=lambda: repo_root() / "downloads" / "invoice_export"
    )


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    seller_nip = config.seller_nip or example_seller_nip()
    invoice_path = config.invoice_path or example_invoice_xml_path()
    invoice_xml = invoice_path.read_bytes()

    auth = client.authentication.with_test_certificate(nip=seller_nip)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice(invoice_xml=invoice_xml)
        print(f"Invoice sent: {result.reference_number}")

        status = session.wait_for_invoice_ready(
            invoice_reference_number=result.reference_number,
            timeout=config.status_timeout,
            poll_interval=config.poll_interval,
        )
        print(f"Invoice processed as KSeF number: {status.ksef_number}")

    export = auth.invoices.schedule_export(
        filters=InvoicesFilter(
            role="seller",
            date_type="issue_date",
            date_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
            date_to=datetime.now(tz=timezone.utc),
            amount_type="brutto",
        )
    )
    print(f"Export scheduled: {export.reference_number}")

    package = auth.invoices.wait_for_export_package(
        reference_number=export.reference_number,
        timeout=config.export_timeout,
        poll_interval=config.poll_interval,
    )
    print(f"Export package ready with {len(package.parts)} part(s)")

    for path in auth.invoices.fetch_package(
        package=package,
        export=export,
        target_directory=config.download_dir,
    ):
        print(f"Downloaded: {path} ({path.stat().st_size} bytes)")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
