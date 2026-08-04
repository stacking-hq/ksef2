"""Authenticate with an MCU-issued certificate on DEMO or PRODUCTION.

Prerequisites:
- set `KSEF_NIP`, `KSEF_CERT`, and `KSEF_KEY` before running
- use an MCU-issued signing certificate, not the TEST self-signed helper

What it demonstrates:
- loading MCU certificate material
- authenticating with `with_xades()` outside TEST
"""

from dataclasses import dataclass, field

from ksef2 import Client, Environment
from scripts.examples._common import required_env
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem


@dataclass
class ExampleConfig:
    environment: Environment = Environment.DEMO
    nip: str = field(default_factory=lambda: required_env("KSEF_NIP"))
    cert_path: str = field(default_factory=lambda: required_env("KSEF_CERT"))
    key_path: str = field(default_factory=lambda: required_env("KSEF_KEY"))


def run(config: ExampleConfig) -> None:
    cert = load_certificate_from_pem(config.cert_path)
    key = load_private_key_from_pem(config.key_path)
    with Client(config.environment) as client:
        print("Authenticating via XAdES (MCU certificate)...")
        auth = client.authentication.with_xades(
            nip=config.nip,
            cert=cert,
            private_key=key,
            verify_chain=False,
        )

        print(f"  Valid until: {auth.auth_tokens.access_token.valid_until}")
        print(f"  Valid until: {auth.auth_tokens.refresh_token.valid_until}")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
