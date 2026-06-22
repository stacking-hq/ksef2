<h1 align="center">ksef2 SDK</h1>

<h3 align="center">
  Typed Python SDK for automating KSeF 2.0 invoicing workflows.
</h3>

<p align="center">
  Built against the published KSeF OpenAPI specification and checked daily so
  the SDK stays aligned with API changes.<br>
  100% endpoint coverage, sync and async clients, low-level endpoint access,
  and tools for authentication, sessions, exports, tokens, permissions, and
  certificates.
</p>

<div align="center">
  <br>
  <a href="https://docs.stacking.me/ksef2/sdk/intro/" title="ksef2 documentation">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-light.png">
      <img src="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-dark.png" alt="ksef2" width="320">
    </picture>
  </a>
  <br>
  <br>
  <p>
    <img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/coverage.json&query=$.message&label=KSeF%20API%20coverage&color=$.color" alt="KSeF API coverage">
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/test-coverage.yml"><img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/test-coverage.json&query=$.message&label=Unit%20test%20coverage&color=$.color" alt="Unit test coverage"></a>
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml"><img src="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml/badge.svg" alt="Integration tests"></a><br>
    <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit enabled"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT license"></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  </p>
  <p>
    Languages:
    <a href="https://github.com/stacking-hq/ksef2/blob/main/README.md">English</a> ·
    <a href="https://github.com/stacking-hq/ksef2/blob/main/README.pl.md">Polski</a>
  </p>
</div>

## What is ksef2?

`ksef2` is a community-maintained Python SDK for Poland's KSeF v2 API. It is
designed for developers building custom integrations, automations, back-office
tools, and invoice-processing pipelines around KSeF without hand-writing HTTP
requests, polling loops, or encryption handling.

This project is not published, endorsed, or supported by Poland's Ministry of
Finance. Official KSeF [documentation](https://api-test.ksef.mf.gov.pl/docs/v2/)
remains the source of truth for API behavior.

The SDK currently targets KSeF OpenAPI version `2.6.1`.

## Install

```bash
# standard pip installation
pip install ksef2

# install with uv inside an application project
uv add ksef2
```


Requires Python 3.12 or newer.

Optional extras:
```bash
pip install "ksef2[pdf]"             # local invoice PDF rendering
pip install "ksef2[runtime-checks]"  # optional beartype runtime checks
```

Runtime checks are disabled unless `KSEF2_RUNTIME_CHECKS=1` is set.

The CLI is distributed separately under [`stacking-hq/ksef2-cli`](https://github.com/stacking-hq/ksef2-cli).
Install it when you want terminal workflows,
scriptable commands, or local profiles:

```bash
uv tool install ksef2-cli
# or
pipx install ksef2-cli
```

## Authenticate

Use the authentication method that matches the environment you are working with.

```python
from ksef2 import Client, Environment
from ksef2.xades import (
    load_certificate_from_pem,
    load_private_key_from_pem
)

client = Client(Environment.TEST)

# local TEST workflows can use an SDK-generated certificate.
test = client.authentication.with_test_certificate(nip="5261040828")

# token authentication works when you already have a KSeF token.
token = client.authentication.with_token(
    ksef_token="your-ksef-token",
    nip="5261040828",
)

# DEMO and PRODUCTION can authenticate with an MCU-issued XAdES certificate.
cert = load_certificate_from_pem("company.pem")
key = load_private_key_from_pem("company.key")

xades = Client(Environment.DEMO).authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=key,
)

# you can also use CLI profiles to avoid handling certificates and tokens directly in your code
profile = client.authentication.with_profile("test-company")
```

### ksef2-cli profiles

The separate [`ksef2-cli`](https://github.com/stacking-hq/ksef2-cli) package
provides local profiles for repeated CLI work. Profiles store non-secret
defaults such as environment, NIP, authentication method, certificate paths, and
the environment variable that contains a secret.

CLI profile setup:

```bash
ksef2 profile create prod-token \
  --env production \
  --nip 5261040828 \
  --token-env KSEF2_TOKEN

# profile create activates the new profile by default, use this to switch between contexts
ksef2 profile use prod-token

# example usage of the cli
ksef2 --profile prod-token invoices metadata \
  --role seller \
  --date-from 2026-01-01T00:00:00Z
```

These commands add a profile to the local `ksef2-cli` configuration at
`~/.config/ksef2-cli/config.toml`:

```toml
# ksef2-cli local profiles
# CLI options override the selected profile for one invocation.
# Store token and password secrets in environment variables.
active_profile = "prod-token"

[profiles.prod-token]
environment = "production"
nip = "5261040828"

[profiles.prod-token.auth]
type = "token"
token_env = "KSEF2_TOKEN"
```

Use defined profiles in the SDK:

```python
from ksef2 import Client, Environment
from ksef2.profiles import Profile, ProfileStore, TokenProfileAuth

store = ProfileStore.default()
store.save(
    "prod-token",
    Profile(
        environment=Environment.PRODUCTION,
        nip="5261040828",
        auth=TokenProfileAuth(token_env="KSEF2_TOKEN"),
    ),
    activate=True,
    overwrite=True,
)

# match the profile and client environments.
client = Client(Environment.PRODUCTION)

# defaults to the currently active profile in the CLI configuration.
active = client.authentication.with_profile()

# or specify which profile to use explicitly.
seller = client.authentication.with_profile("prod-token")
```

## Send and download an invoice

```python
from pathlib import Path

from ksef2 import Client, Environment, FormSchema

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip="5261040828")

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=Path("invoice.xml").read_bytes(),
        timeout=60.0,
    )

invoice_xml = auth.invoices.wait_for_invoice_download(
    ksef_number=status.ksef_number,
    timeout=120.0,
)

Path("downloads").mkdir(exist_ok=True)
Path("downloads/invoice.xml").write_bytes(invoice_xml)
print(status.ksef_number)
```

Use `auth.invoices` for metadata queries, exports, package downloads, and direct
invoice downloads after KSeF assigns invoice numbers.

## Documentation

- Online docs: <https://docs.stacking.me/ksef2/sdk/intro/>
- Quickstart: <https://docs.stacking.me/ksef2/sdk/getting-started/quickstart/>
- Workflow guides: <https://docs.stacking.me/ksef2/sdk/workflows/overview/>
- API reference: <https://docs.stacking.me/ksef2/sdk/reference/api-signatures/>
- Source docs: [`docs/en`](https://github.com/stacking-hq/ksef2/tree/main/docs/en) and [`docs/pl`](https://github.com/stacking-hq/ksef2/tree/main/docs/pl)
- Runnable examples: [`scripts/examples`](https://github.com/stacking-hq/ksef2/tree/main/scripts/examples)

## Development

```bash
just sync
just test
just release-check
```

Additional development tasks live in the `justfile`, including integration
tests, API coverage checks, OpenAPI model regeneration, and release tooling.

## Contributing

Issues and pull requests are welcome. Before opening a PR, run the focused test
or docs build that covers your change, and update both source docs and examples
when behavior changes.

For SDK docs, edit the source catalog under `docs/en` and `docs/pl`. The public
documentation site syncs from those files.

## License

[MIT](https://github.com/stacking-hq/ksef2/blob/main/LICENSE.md)
