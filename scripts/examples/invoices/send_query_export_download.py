"""Send an invoice, wait for processing, export matching invoices, and download the package.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- invoice submission and status polling
- seller-side invoice export
- downloading export packages to disk
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.core.invoices import InvoiceTemplater
from ksef2.core.tools import generate_nip
from ksef2.domain.models import InvoicesFilter
from scripts.examples._common import repo_root


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    poll_interval: float = 2.0
    status_timeout: float = 60.0
    export_timeout: float = 240.0
    template_path: Path = field(
        default_factory=lambda: (
            repo_root()
            / "docs"
            / "assets"
            / "sample_invoices"
            / "fa3"
            / "invoice-template_v3.xml"
        )
    )
    download_dir: Path = field(
        default_factory=lambda: repo_root() / "downloads" / "invoice_export"
    )


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    seller_nip = generate_nip()

    with client.testdata.temporal() as temp:
        temp.create_subject(
            nip=seller_nip,
            subject_type="enforcement_authority",
            description="README lifecycle example",
        )

        auth = client.authentication.with_test_certificate(nip=seller_nip)
        template_xml = config.template_path.read_text(encoding="utf-8")
        invoice_xml = InvoiceTemplater.create(
            template_xml,
            {
                "#nip#": seller_nip,
                "#invoicing_date#": date.today().isoformat(),
                "#invoice_number#": f"DEMO-{datetime.now(tz=timezone.utc):%Y%m%d%H%M%S}",
            },
        )

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
