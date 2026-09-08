"""Authenticate in TEST and refresh the access token.

Prerequisites:
- none; the script uses a generated TEST certificate identity

What it demonstrates:
- initial XAdES authentication
- refreshing an access token with the SDK helper
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
        print(
            f"  Access token valid until:  {auth.auth_tokens.access_token.valid_until}"
        )
        print(
            f"  Refresh token valid until: {auth.auth_tokens.refresh_token.valid_until}"
        )

        print("Refreshing access token...")
        refreshed = client.authentication.refresh(refresh_token=auth.refresh_token)
        print(f"  New access token valid until: {refreshed.access_token.valid_until}")
        print("  New access token issued successfully.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
