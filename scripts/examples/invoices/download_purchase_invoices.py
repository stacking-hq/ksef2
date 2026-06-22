"""Download purchase invoices for multiple entities.

For each NIP the script authenticates with the certificate
downloaded from MCU, schedules an export of all purchase invoices in the
requested date range, and saves the resulting ZIP packages to disk.

Directory layout expected for certificates (files downloaded from KSeF/MCU)::

certs/
    1111111111.pem   # certificate - <NIP>.pem
    1111111111.key   # private key  - <NIP>.key
    2222222222.pem
    2222222222.key
    ...

Usage:
uv run -m scripts.examples.invoices.download_purchase_invoices
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem
from ksef2.domain.models import InvoicesFilter
from scripts.examples._common import repo_root


@dataclass
class ExampleConfig:
    environment: Environment = Environment.PRODUCTION
    nips: list[str] = field(
        default_factory=lambda: [
            "1111111111",
            "2222222222",
        ]
    )
    cert_dir: Path = Path("certs")
    download_dir: Path = field(default_factory=lambda: repo_root() / "downloads")
    date_to: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    export_timeout: float = 180.0
    poll_interval: float = 3.0

    @property
    def date_from(self) -> datetime:
        return self.date_to - timedelta(days=90)


def download_for_nip(client: Client, nip: str, config: ExampleConfig) -> None:
    print(f"[{nip}] Authenticating...")

    cert = load_certificate_from_pem(config.cert_dir / f"{nip}.pem")
    key = load_private_key_from_pem(config.cert_dir / f"{nip}.key")

    auth = client.authentication.with_xades(
        nip=nip,
        cert=cert,
        private_key=key,
        verify_chain=False,
    )

    target_dir = config.download_dir / nip
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{nip}] Scheduling export of purchase invoices...")
    export = auth.invoices.schedule_export(
        filters=InvoicesFilter(
            role="buyer",
            date_type="issue_date",
            date_from=config.date_from,
            date_to=config.date_to,
            amount_type="brutto",
        )
    )

    package = auth.invoices.wait_for_export_package(
        reference_number=export.reference_number,
        timeout=config.export_timeout,
        poll_interval=config.poll_interval,
    )

    for path in auth.invoices.fetch_package(
        package=package,
        export=export,
        target_directory=target_dir,
    ):
        print(f"[{nip}] Downloaded: {path} ({path.stat().st_size:,} bytes)")

    print(f"[{nip}] Done.")


def run(config: ExampleConfig) -> None:
    config.download_dir.mkdir(parents=True, exist_ok=True)
    client = Client(config.environment)

    for nip in config.nips:
        download_for_nip(client, nip, config)

    print("Done.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
