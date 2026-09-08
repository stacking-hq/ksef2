"""Enable and revoke attachment permissions on TEST.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- enabling attachment permissions
- revoking them immediately and with an end date
"""

from dataclasses import dataclass
from datetime import date, timedelta

from ksef2 import Client, Environment
from scripts.examples._common import generate_example_nip


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        organization_nip = generate_example_nip()

        with client.testdata.temporal() as temp:
            print(f"Creating test subject with NIP: {organization_nip}")
            temp.create_subject(
                nip=organization_nip,
                subject_type="enforcement_authority",
                description="Attachments test",
            )

            print(f"Enabling attachments for NIP: {organization_nip}")
            client.testdata.enable_attachments(nip=organization_nip)
            print("  Attachments enabled")

            print(f"Revoking attachments for NIP: {organization_nip}")
            client.testdata.revoke_attachments(nip=organization_nip)
            print("  Attachments revoked immediately")

            print("Re-enabling attachments...")
            client.testdata.enable_attachments(nip=organization_nip)

            future_date = date.today() + timedelta(days=30)
            print(f"Revoking attachments with end date: {future_date}")
            client.testdata.revoke_attachments(
                nip=organization_nip,
                expected_end_date=future_date,
            )
            print(f"  Attachments will be revoked on {future_date}")

        print("Test data cleaned up.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
