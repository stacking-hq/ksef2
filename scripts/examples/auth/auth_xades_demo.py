"""Authenticate with an MCU-issued certificate on DEMO or PRODUCTION.

Prerequisites:
- set `KSEF_NIP`, `KSEF_CERT`, and `KSEF_KEY`, or edit the defaults below
- use an MCU-issued signing certificate, not the TEST self-signed helper

What it demonstrates:
- loading MCU certificate material
- authenticating with `with_xades()` outside TEST
"""

import os
from dataclasses import dataclass, field

from ksef2 import Client, Environment
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem


@dataclass
class ExampleConfig:
    environment: Environment = Environment.DEMO
    nip: str = field(default_factory=lambda: os.environ.get("KSEF_NIP", "1234567890"))
    cert_path: str = field(
        default_factory=lambda: os.environ.get(
            "KSEF_CERT",
            f"{os.environ.get('KSEF_NIP', '1234567890')}.pem",
        )
    )
    key_path: str = field(
        default_factory=lambda: os.environ.get(
            "KSEF_KEY",
            f"{os.environ.get('KSEF_NIP', '1234567890')}.key",
        )
    )


def run(config: ExampleConfig) -> None:
    cert = load_certificate_from_pem(config.cert_path)
    key = load_private_key_from_pem(config.key_path)
    client = Client(config.environment)

    print("Authenticating via XAdES (MCU certificate)...")
    auth = client.authentication.with_xades(
        nip=config.nip,
        cert=cert,
        private_key=key,
        verify_chain=False,
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
