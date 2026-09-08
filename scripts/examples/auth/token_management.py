"""Generate, inspect, and revoke a KSeF token in TEST.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- creating a temporary test subject
- generating a KSeF token
- checking token status and revoking it
"""

from dataclasses import dataclass

from ksef2 import Client, Environment
from scripts.examples._common import generate_example_nip


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        nip = generate_example_nip()

        print("Setting up test data...")
        with client.testdata.temporal() as td:
            td.create_subject(
                nip=nip,
                subject_type="enforcement_authority",
                description="Token management test",
            )

            print("Authenticating...")
            auth = client.authentication.with_test_certificate(nip=nip)

            print("Generating KSeF token...")
            result = auth.tokens.generate(
                permissions=[
                    "invoice_read",
                    "invoice_write",
                ],
                description="Example API token",
            )
            print(f"  Reference: {result.reference_number}")

            print("Waiting for token activation...")
            status = auth.tokens.wait_for_activation(
                reference_number=result.reference_number
            )
            print(f"  Status: {status.status}")

            print("Revoking token...")
            auth.tokens.revoke(reference_number=result.reference_number)

            print("Verifying revocation...")
            status = auth.tokens.status(reference_number=result.reference_number)
            print(f"  Status: {status.status}")

        print("Done, test data cleaned up.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
