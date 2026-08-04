"""List and terminate authentication sessions in the TEST environment.

Prerequisites:
- none; the script uses a generated TEST certificate identity

What it demonstrates:
- authenticating in TEST
- listing auth sessions
- terminating the current auth session
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

        print("Authenticating...")
        auth = client.authentication.with_test_certificate(nip=nip)

        print("Listing active authentication sessions...")
        sessions = auth.sessions.query()
        print(f"  Found {len(sessions.items)} session(s)")
        for item in sessions.items:
            print(f"  {item.reference_number} current={item.is_current}")

        print("Terminating current session...")
        auth.sessions.terminate_current()
        print("  Current session terminated.")
        print("Session management complete.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
