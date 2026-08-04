"""Block and unblock authentication contexts on TEST.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- blocking a TEST auth context
- unblocking the context again
"""

from dataclasses import dataclass

from ksef2 import Client, Environment
from ksef2.models import AuthContextIdentifier
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
                description="Block context test",
            )

            context_id = AuthContextIdentifier(
                type="nip",
                value=organization_nip,
            )

            print(f"Blocking context for NIP: {organization_nip}")
            client.testdata.block_context(context=context_id)
            print("  Context blocked - authentication is now disabled")

            print(f"Unblocking context for NIP: {organization_nip}")
            client.testdata.unblock_context(context=context_id)
            print("  Context unblocked - authentication is now enabled")

        print("Test data cleaned up.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
