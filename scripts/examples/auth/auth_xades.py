"""Authenticate with XAdES in the TEST environment.

Prerequisites:
- none; the script uses a generated TEST certificate identity

What it demonstrates:
- XAdES authentication in TEST
- inspecting issued access and refresh tokens
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

        print("Authenticating via XAdES...")
        auth = client.authentication.with_test_certificate(nip=nip)

        print(f"  Valid until: {auth.auth_tokens.access_token.valid_until}")
        print(f"  Valid until: {auth.auth_tokens.refresh_token.valid_until}")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
