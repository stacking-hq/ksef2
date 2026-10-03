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
from ksef2.testdata import generate_nip


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    nip = generate_nip()

    print("Authenticating...")
    auth = client.authentication.with_test_certificate(nip=nip)

    print("Listing active authentication sessions...")
    sessions = auth.sessions.list().first_page()
    print(f"  Found {len(sessions)} session(s)")
    for item in sessions:
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
