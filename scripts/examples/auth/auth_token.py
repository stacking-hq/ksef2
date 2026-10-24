"""Authenticate with a pre-generated KSeF token.

Prerequisites:
- replace `KSEF_TOKEN` with a valid token for the target context

What it demonstrates:
- token-based authentication
- inspecting issued access and refresh tokens
"""

from dataclasses import dataclass

from ksef2 import Client, Environment

KSEF_TOKEN = "<your-token-here>"
KSEF_NIP = "<nip-bound-to-token>"


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST
    ksef_token: str = KSEF_TOKEN
    nip: str = KSEF_NIP


def run(config: ExampleConfig) -> None:
    with Client(environment=config.environment) as client:
        print("Authenticating via KSeF token...")
        auth = client.authentication.with_token(
            ksef_token=config.ksef_token,
            nip=config.nip,
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
