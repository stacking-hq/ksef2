<div align="center">
<a href="https://github.com/artpods56/ksef2" title="KSeF Toolkit">
  <img src="https://raw.githubusercontent.com/artpods56/ksef2/master/docs/assets/logo.png" alt="KSeF Toolkit" width="50%">
</a>

**Python SDK for Poland's KSeF (Krajowy System e-Faktur) v2 API.**

![API Coverage](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/artpods56/ksef2/master/coverage.json&query=$.message&label=KSeF%20API%20coverage&color=$.color)
[![Unit Test Coverage](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/artpods56/ksef2/master/test-coverage.json&query=$.message&label=Unit%20test%20coverage&color=$.color)](https://github.com/artpods56/ksef2/actions/workflows/test-coverage.yml)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Integration Tests](https://github.com/artpods56/ksef2/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/artpods56/ksef2/actions/workflows/integration-tests.yml) \
[![beartype](https://raw.githubusercontent.com/beartype/beartype-assets/main/badge/bear-ified.svg)](https://github.com/beartype/beartype)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## Installation

```bash
pip install ksef2
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add ksef2
```

Requires Python 3.12+.

PDF rendering is optional. Install the `pdf` extra only when you need local
invoice PDF visualization:

```bash
pip install "ksef2[pdf]"
uv add "ksef2[pdf]"
```

## Supported OpenAPI Version

The SDK currently supports KSeF OpenAPI version `2.6.0`.

## Quick Start

```python
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter, InvoiceMetadataParams

NIP = "5261040828"
client = Client(Environment.TEST)

# Authenticate (XAdES — TEST environment)
auth = client.authentication.with_test_certificate(nip=NIP)

with auth.online_session(form_code=FormSchema.FA3) as session:
    # Send an invoice
    result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    print(result.reference_number)

    # Wait until KSeF finishes processing it
    status = session.wait_for_invoice_ready(
        invoice_reference_number=result.reference_number
    )
    print(status.status.description)

# Export invoices (no session required)
export = auth.invoices.schedule_export(
    filters=InvoicesFilter(
        role="seller",
        date_type="issue_date",
        date_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
        date_to=datetime.now(tz=timezone.utc),
        amount_type="brutto",
    ),
)

# Download the exported package
package = auth.invoices.wait_for_export_package(reference_number=export.reference_number)
for path in auth.invoices.fetch_package(
    package=package,
    export=export,
    target_directory="downloads",
):
    print(f"Downloaded: {path}")
```
> Runnable TEST examples:
> [`scripts/examples/quickstart.py`](scripts/examples/quickstart.py) and
> [`scripts/examples/invoices/send_query_export_download.py`](scripts/examples/invoices/send_query_export_download.py)

## Async Quick Start

Use `AsyncClient` when your application already runs inside an event loop.
The async API mirrors the sync client shape: authenticate through
`client.authentication`, then use the returned authenticated client for
sessions, invoices, tokens, permissions, limits, certificates, and batch work.

```python
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import AsyncClient, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter

NIP = "5261040828"


async def main() -> None:
    async with AsyncClient(Environment.TEST) as client:
        auth = await client.authentication.with_test_certificate(nip=NIP)

        async with await auth.online_session(form_code=FormSchema.FA3) as session:
            result = await session.send_invoice(
                invoice_xml=Path("invoice.xml").read_bytes()
            )
            status = await session.wait_for_invoice_ready(
                invoice_reference_number=result.reference_number
            )
            print(status.status.description)

        export = await auth.invoices.schedule_export(
            filters=InvoicesFilter(
                role="seller",
                date_type="issue_date",
                date_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
                date_to=datetime.now(tz=timezone.utc),
                amount_type="brutto",
            ),
        )
        package = await auth.invoices.wait_for_export_package(
            reference_number=export.reference_number
        )
        zip_parts = await auth.invoices.fetch_package_bytes(
            package=package,
            export=export,
        )
        print(len(zip_parts))


asyncio.run(main())
```

See [`docs/guides/async-client.md`](docs/guides/async-client.md) for async usage patterns.

## Error Handling

Catch stable SDK exception classes from the package root, for example
`KSeFApiError`, `KSeFRateLimitError`, and the polling timeout errors. See
[`docs/guides/errors.md`](docs/guides/errors.md) for the exception hierarchy,
KSeF `ExceptionCode` handling, retry patterns, and timeout semantics.

## Features

- **Typed public API** for authentication, sessions, invoices, tokens, permissions, limits, certificates, and PEPPOL
- **Sync and async clients** with matching high-level entry points through `Client` and `AsyncClient`
- **FA(3) invoice builder** exposed through `ksef2.fa3` for typed invoice construction and XML rendering
- **XAdES and KSeF token authentication** through a single `Client.authentication` entry point
- **Online and batch sessions** with resumable session state for long-running jobs
- **Built-in encryption helpers** for invoice sending and export package decryption
- **TEST environment tooling** including self-signed certificates and disposable test data contexts
- **Runnable examples and guide docs** for the common KSeF workflows

## Root Client

`Client` and `AsyncClient` expose both authenticated and public entry points:

- `client.authentication` for XAdES and KSeF-token authentication
- `client.encryption` for public KSeF encryption certificates
- `client.peppol` for public PEPPOL provider queries
- `client.testdata` for TEST-only data setup and cleanup helpers

Async methods are awaited, and async session/testdata helpers are used with
`async with`. For example, `client.authentication.with_token(...)` becomes
`await client.authentication.with_token(...)`, and
`auth.online_session(...)` becomes `async with await auth.online_session(...)`.

## Logging

The SDK exposes `structlog` loggers via `ksef2.logging`, but it does not configure
global logging on import. Applications can either configure `structlog`
themselves or use the provided helper:

```python
from ksef2.logging import configure_logging, get_logger

configure_logging(level="INFO")

logger = get_logger("my_app")
logger.info("Starting KSeF sync", environment="test")
```

SDK internals use the same logger factory, so once the application configures
`structlog`, events emitted by `ksef2` follow the same handlers and rendering.

### XAdES on DEMO / PRODUCTION (MCU certificate)

The TEST environment accepts self-signed certificates generated by the SDK.
DEMO and PRODUCTION require a certificate issued by MCU — use the provided helpers to load it:

```python
from ksef2 import Client, Environment
from ksef2.core.xades import (
    load_certificate_and_key_from_p12,
    load_certificate_from_pem,
    load_private_key_from_pem,
)

cert = load_certificate_from_pem("cert.pem")  # downloaded from MCU
key = load_private_key_from_pem("key.pem")

auth = Client(Environment.DEMO).authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=key,
)

cert, key = load_certificate_and_key_from_p12("cert.p12", password=b"secret")
```

### Token Authentication

Use this when you already have a KSeF token issued for the target context:

```python
from ksef2 import Client

client = Client()  # uses production environment by default

auth = client.authentication.with_token(
    ksef_token="your-ksef-token",
    nip="5261040828",
)
print(auth.access_token)
```

## Authenticated Client

After `with_xades()` or `with_token()`, you get an `AuthenticatedClient`. Its main entry points are:

- `auth.online_session()` and `auth.batch_session()` for invoice sessions
- `auth.batch` for end-to-end batch package preparation, upload, and status polling
- `auth.invoices` for metadata queries, exports, downloads, and package fetches
- `auth.tokens` for KSeF authorization token lifecycle management
- `auth.permissions` for grant, revoke, and query operations
- `auth.certificates` for certificate enrollment, retrieval, query, and revocation
- `auth.sessions` for active authentication session management
- `auth.invoice_sessions` for historical online and batch invoice sessions
- `auth.limits` for TEST-environment limit inspection and overrides

Invoice sending stays on `auth.online_session()` because it depends on an opened KSeF session and its session-specific encryption keys. Batch ZIP preparation and upload live on `auth.batch`, while metadata queries, exports, and downloads live on `auth.invoices` because they only require the authenticated bearer context.

Common examples:

```python
from datetime import datetime, timedelta, timezone

from ksef2.domain.models import InvoicesFilter

token = auth.tokens.generate(
    permissions=["invoice_read", "invoice_write"],
    description="API integration token",
)
print(token.reference_number, token.token)

limits = auth.limits.get_context_limits()
print(limits.online_session.max_invoices)

sessions = auth.sessions.query(page_size=10)
print(len(sessions.items))

metadata_filters = InvoicesFilter(
    role="seller",
    date_type="issue_date",
    date_from=datetime.now(tz=timezone.utc) - timedelta(days=7),
    date_to=datetime.now(tz=timezone.utc),
    amount_type="brutto",
)
metadata = auth.invoices.query_metadata(
    filters=metadata_filters,
)
print(len(metadata.invoices))

for page in auth.invoices.query_metadata_pages(
    filters=metadata_filters,
    params=InvoiceMetadataParams(page_size=250, sort_order="asc"),
):
    print(len(page.invoices), page.has_more)
```

For the full API surface, see the guide docs below.

## FA(3) Builder

If you want to generate FA(3) invoices inside the SDK, use the public `ksef2.fa3` namespace:

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, VatRate

xml_text = (
    FA3InvoiceBuilder()
    .header(system_info="my app")
    .seller(
        name="ACME S.A.",
        tax_id="1234567890",
        country_code="PL",
        address_line_1="ul. Przykladowa 123",
    )
    .buyer(
        name="XYZ GmbH",
        country_code="DE",
        address_line_1="Unter den Linden 1",
    )
    .standard()
        .issue_date(date(2026, 3, 29))
        .invoice_number("FV/2026/03/0001")
        .rows()
            .add_line(
                name="Consulting service",
                quantity=Decimal("1"),
                unit_of_measure="h",
                unit_price_net=Decimal("100.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
    .done()
    .to_xml()
)
```

See [`docs/guides/fa3-builder.md`](docs/guides/fa3-builder.md) for the full builder guide and the runnable examples in [`scripts/examples/invoices`](scripts/examples/invoices).

To build an invoice and generate a PDF visualization locally:

```bash
uv run --extra pdf -m scripts.examples.invoices.build_fa3_invoice
```

This writes both `output/fa3_invoice.xml` and `output/fa3_invoice.pdf`.

## Examples

Run examples as modules with `uv run -m ...`; direct execution by file path is not supported.

- [`scripts/examples/quickstart.py`](scripts/examples/quickstart.py) - minimal TEST-environment invoice send
- [`scripts/examples/auth/auth_xades.py`](scripts/examples/auth/auth_xades.py) - XAdES authentication
- [`scripts/examples/auth/auth_token.py`](scripts/examples/auth/auth_token.py) - KSeF token authentication
- [`scripts/examples/invoices/send_batch.py`](scripts/examples/invoices/send_batch.py) - staged batch upload with explicit session lifecycle
- [`scripts/examples/invoices/submit_batch.py`](scripts/examples/invoices/submit_batch.py) - one-shot batch submission flow
- [`scripts/examples/invoices/send_query_export_download.py`](scripts/examples/invoices/send_query_export_download.py) - send, inspect, export, and download invoices
- [`scripts/examples/invoices/build_fa3_invoice.py`](scripts/examples/invoices/build_fa3_invoice.py) - build an FA(3) invoice, validate the XML, and generate a PDF visualization with the `pdf` extra
- [`scripts/examples/invoices/build_fa3_invoice_builder.py`](scripts/examples/invoices/build_fa3_invoice_builder.py) - use the nested FA(3) builder DSL and generate XML plus a PDF visualization with the `pdf` extra
- [`scripts/examples/invoices/build_fa3_invoice_sample_1.py`](scripts/examples/invoices/build_fa3_invoice_sample_1.py) - recreate the first official FA(3) sample with the public builder
- [`scripts/examples/peppol/query_providers.py`](scripts/examples/peppol/query_providers.py) - query public PEPPOL providers
- [`scripts/examples/scenarios/download_purchase_invoices.py`](scripts/examples/scenarios/download_purchase_invoices.py) - multi-buyer purchase-invoice export scenario
- [`scripts/examples/session/session_resume.py`](scripts/examples/session/session_resume.py) - persist and resume an online session

## Development

```bash
just sync          # Install all dependencies (including dev)
just test          # Run unit tests
just test-coverage # Run unit tests with coverage and update test-coverage.json
just release-check # Run the pre-release verification suite and build artifacts
just regenerate-models  # Regenerate OpenAPI models
```

### Other commands

```bash
just integration   # Run integration tests (requires KSEF credentials in .env)
just coverage       # Calculate API coverage (updates coverage.json)
just fetch-spec     # Fetch latest OpenAPI spec from KSeF
```

## API Coverage

The SDK covers **73 of 73** KSeF API endpoints (100%). See feature docs for details:

- [Authentication](docs/guides/authentication.md) — XAdES, token auth, session management
- [Async Client](docs/guides/async-client.md) — async authentication, sessions, exports, batch, and testdata
- [Encryption](docs/guides/encryption.md) — public KSeF encryption certificates
- [Invoices](docs/guides/invoices.md) — send, download, query, export
- [Sessions](docs/guides/sessions.md) — online/batch sessions, resume support
- [Tokens](docs/guides/tokens.md) — generate and manage KSeF authorization tokens
- [Permissions](docs/guides/permissions.md) — grant/query permissions for persons and entities
- [Certificates](docs/guides/certificates.md) — enroll, query, revoke KSeF certificates
- [Limits](docs/guides/limits.md) — query and modify API rate limits
- [PEPPOL](docs/guides/peppol.md) — query registered PEPPOL providers
- [Test Data](docs/guides/testdata.md) — create test subjects, manage test environment

## Stability And Releases

The SDK is still in the pre-`1.0.0` stabilization phase.

- Track release notes in [CHANGELOG.md](CHANGELOG.md)
- Run `just release-check` before publishing a release
- Expect `0.x` minor releases to contain public API cleanup when needed

## License

[MIT](LICENSE.md)
