<div align="center">
  <a href="https://ksef2.stacking.me/sdk/intro/" title="ksef2 documentation">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-light.png">
      <img src="https://raw.githubusercontent.com/stacking-hq/ksef2/main/docs/assets/logo-dark.png" alt="ksef2" width="320">
    </picture>
  </a>

  <p><strong>Python SDK for Poland's KSeF v2 API.</strong></p>

  <p>
    <a href="https://github.com/stacking-hq/ksef2/blob/main/README.pl.md">Polski</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/coverage.json&query=$.message&label=KSeF%20API%20coverage&color=$.color" alt="KSeF API coverage">
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/test-coverage.yml"><img src="https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/stacking-hq/ksef2/main/test-coverage.json&query=$.message&label=Unit%20test%20coverage&color=$.color" alt="Unit test coverage"></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
    <a href="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml"><img src="https://github.com/stacking-hq/ksef2/actions/workflows/integration-tests.yml/badge.svg" alt="Integration tests"></a>
    <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit enabled"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT license"></a>
  </p>
</div>

## Overview

`ksef2` is a community-maintained Python SDK for Poland's KSeF v2 API. It
provides sync and async clients, typed request and response models, invoice
session helpers, FA(3) invoice building, and tooling for common TEST
environment workflows.

This project is not published, endorsed, or supported by Poland's Ministry of
Finance. Official KSeF documentation remains the source of truth for API
behavior.

The SDK currently targets KSeF OpenAPI version `2.6.0`.

## Install

```bash
pip install ksef2
```

or:

```bash
uv add ksef2
```

Requires Python 3.12 or newer.

Optional extras:

```bash
pip install "ksef2[pdf]"             # local invoice PDF rendering
pip install "ksef2[runtime-checks]"  # optional beartype runtime checks
```

Runtime checks are disabled unless `KSEF2_RUNTIME_CHECKS=1` is set.

## Quick Start

```python
from pathlib import Path

from ksef2 import Client, Environment, FormSchema

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip="5261040828")

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    print(result.reference_number)
```

For production or DEMO integrations, authenticate with a KSeF token or an
MCU-issued certificate. See the authentication workflow in the docs.

## Documentation

- Online docs: <https://ksef2.stacking.me/sdk/intro/>
- Quickstart: <https://ksef2.stacking.me/sdk/getting-started/quickstart/>
- Workflow guides: <https://ksef2.stacking.me/sdk/workflows/overview/>
- API reference: <https://ksef2.stacking.me/sdk/reference/api-signatures/>
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

## License

[MIT](https://github.com/stacking-hq/ksef2/blob/main/LICENSE.md)
