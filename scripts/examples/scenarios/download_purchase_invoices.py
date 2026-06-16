"""Create seller and buyer test entities, then export purchase invoices for each buyer.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- creating temporary test subjects
- sending invoices to multiple buyers
- exporting and downloading buyer-side invoice packages
"""

import traceback
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.core import exceptions
from ksef2.core.invoices import InvoiceTemplater
from ksef2.core.tools import generate_nip
from ksef2.domain.models import InvoicesFilter
from scripts.examples._common import repo_root

DEFAULT_BUYER_COUNT = 3
DEFAULT_INVOICES_PER_BUYER = 2
DEFAULT_POLL_INTERVAL = 3.0
DEFAULT_EXPORT_TIMEOUT = 180.0


@dataclass
class ExampleConfig:
    buyer_count: int = DEFAULT_BUYER_COUNT
    invoices_per_buyer: int = DEFAULT_INVOICES_PER_BUYER
    poll_interval: float = DEFAULT_POLL_INTERVAL
    export_timeout: float = DEFAULT_EXPORT_TIMEOUT
    environment: Environment = Environment.TEST
    download_dir: Path = field(
        default_factory=lambda: repo_root() / "downloads" / "test"
    )
    template_path: Path = field(
        default_factory=lambda: (
            repo_root()
            / "docs"
            / "assets"
            / "sample_invoices"
            / "fa3"
            / "invoice-template-fa-3-with-custom-subject_2.xml"
        )
    )


def send_invoices(
    client: Client,
    seller_nip: str,
    buyers: list[str],
    config: ExampleConfig,
) -> None:
    """Authenticate as seller and send invoices to each buyer."""
    print(f"\n[seller {seller_nip}] Authenticating...")
    auth = client.authentication.with_test_certificate(nip=seller_nip)
    template_xml = config.template_path.read_text(encoding="utf-8")

    with auth.online_session(form_code=FormSchema.FA3) as session:
        for buyer_nip in buyers:
            for index in range(config.invoices_per_buyer):
                status = session.send_invoice_and_wait(
                    invoice_xml=InvoiceTemplater.create(
                        template_xml,
                        {
                            "#nip#": seller_nip,
                            "#subject2nip#": buyer_nip,
                            "#invoicing_date#": date.today().isoformat(),
                            "#invoice_number#": (
                                f"DEMO-{date.today():%Y%m%d}-{buyer_nip[-4:]}-{index + 1}"
                            ),
                        },
                    ),
                    timeout=60.0,
                    poll_interval=2.0,
                )
                print(
                    f"[seller] Sent invoice #{index + 1} to buyer {buyer_nip} -> "
                    f"{status.reference_number}"
                )

    print("[seller] All invoices sent and processed.")


def download_for_buyer(
    client: Client,
    buyer_nip: str,
    target_dir: Path,
    config: ExampleConfig,
) -> None:
    """Authenticate as buyer and download all purchase invoices."""
    print(f"\n[buyer {buyer_nip}] Authenticating...")
    auth = client.authentication.with_test_certificate(nip=buyer_nip)
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"[buyer {buyer_nip}] Scheduling export of purchase invoices...")
    export = auth.invoices.schedule_export(
        filters=InvoicesFilter(
            role="buyer",
            date_type="issue_date",
            date_from=datetime.now(tz=timezone.utc) - timedelta(days=90),
            date_to=datetime.now(tz=timezone.utc),
            amount_type="brutto",
        )
    )

    try:
        package = auth.invoices.wait_for_export_package(
            reference_number=export.reference_number,
            timeout=config.export_timeout,
            poll_interval=config.poll_interval,
        )
    except exceptions.KSeFExportTimeoutError:
        print(f"[buyer {buyer_nip}] Export timed out.")
        return

    for path in auth.invoices.fetch_package(
        package=package,
        export=export,
        target_directory=target_dir,
    ):
        print(
            f"[buyer {buyer_nip}] Downloaded: {path.name} ({path.stat().st_size:,} bytes)"
        )


def run(config: ExampleConfig) -> list[str]:
    client = Client(config.environment)
    seller_nip = generate_nip()
    buyer_nips = [generate_nip() for _ in range(config.buyer_count)]

    print("=" * 60)
    print(f"Seller NIP : {seller_nip}")
    print(f"Buyer NIPs : {', '.join(buyer_nips)}")
    print("=" * 60)

    failed: list[str] = []

    with client.testdata.temporal() as temp:
        temp.create_subject(
            nip=seller_nip,
            subject_type="enforcement_authority",
            description="Scenario seller",
        )
        for buyer_nip in buyer_nips:
            temp.create_subject(
                nip=buyer_nip,
                subject_type="enforcement_authority",
                description=f"Scenario buyer {buyer_nip}",
            )

        send_invoices(
            client=client,
            seller_nip=seller_nip,
            buyers=buyer_nips,
            config=config,
        )

        for buyer_nip in buyer_nips:
            try:
                download_for_buyer(
                    client=client,
                    buyer_nip=buyer_nip,
                    target_dir=config.download_dir / buyer_nip,
                    config=config,
                )
            except Exception:
                print(f"[buyer {buyer_nip}] ERROR - full traceback:")
                traceback.print_exc()
                failed.append(buyer_nip)

    return failed


def main() -> int:
    failed = run(ExampleConfig())
    if failed:
        print(f"\nFailed buyers: {', '.join(failed)}")
        return 1

    print("\nDone. All buyers succeeded. Test subjects cleaned up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
