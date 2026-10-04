"""Schedule an export, save its state, and finish it later with `export(state=...)`.

Prerequisites:
- set KSEF2_EXAMPLE_SELLER_NIP to the TEST seller NIP

What it demonstrates:
- scheduling an export and persisting `ExportJob.resume_state()` as JSON
- getting the job back after a restart with `auth.invoices.export(state=...)`
- waiting for the package and saving the decrypted invoices

The saved state contains the key that decrypts the package. Store it as a
credential: encrypted, never logged, never committed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment
from ksef2.models import InvoicesFilter
from scripts.examples._common import example_seller_nip, repo_root


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    poll_interval: float = 2.0
    export_timeout: float = 120.0
    seller_nip: str | None = None
    download_dir: Path = field(
        default_factory=lambda: repo_root() / "downloads" / "export_resume"
    )


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    seller_nip = config.seller_nip or example_seller_nip()
    auth = client.authentication.with_test_certificate(nip=seller_nip)

    job = auth.invoices.export(
        InvoicesFilter.for_seller(
            date_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
            date_to=datetime.now(tz=timezone.utc),
        )
    )
    saved_state = job.resume_state().to_json()
    print(f"Export scheduled: {job.reference_number}")

    # ... the process may stop here; keep `saved_state` in secure storage ...

    resumed = auth.invoices.export(state=saved_state)
    package = resumed.wait(
        timeout=config.export_timeout,
        poll_interval=config.poll_interval,
    )
    for ksef_number, _xml in package.invoices():
        print(f"Exported invoice: {ksef_number}")

    for path in package.save(config.download_dir):
        print(f"Saved: {path}")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
