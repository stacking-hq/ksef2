"""Authenticate with a pre-generated KSeF token.

Prerequisites:
- replace `KSEF_TOKEN` with a valid token for the target context

What it demonstrates:
- token-based authentication
- inspecting issued access and refresh tokens
"""

from dataclasses import dataclass

from ksef2 import Client, Environment
from ksef2.testdata import generate_nip

KSEF_TOKEN = "<your-token-here>"


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    ksef_token: str = KSEF_TOKEN


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    nip = generate_nip()

    print("Authenticating via KSeF token...")
    auth = client.authentication.with_token(
        ksef_token=config.ksef_token,
        nip=nip,
    )

    print(f"Access token:  {auth.access_token[:40]}…")
    print(f"  Valid until: {auth.auth_tokens.access_token.valid_until}")
    print(f"Refresh token: {auth.refresh_token[:40]}…")
    print(f"  Valid until: {auth.auth_tokens.refresh_token.valid_until}")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
