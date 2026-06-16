---
title: Async Client
description: Use the async KSeF2 client in event-loop based applications.
---

Use `AsyncClient` when the application already runs in an event loop, for
example in FastAPI, aiohttp, background workers, or async CLI jobs.

The async API mirrors the sync SDK:

- `AsyncClient` is the async root client.
- `await client.authentication.with_token(...)` and
  `await client.authentication.with_xades(...)` return an authenticated async client.
- Authenticated entry points keep the same names: `online_session`, `batch`,
  `invoices`, `tokens`, `permissions`, `certificates`, `sessions`,
  `invoice_sessions`, and `limits`.
- Async session helpers use `async with`.

## Root Client

```python
from ksef2 import AsyncClient, Environment


async with AsyncClient(Environment.TEST) as client:
    certificates = await client.encryption.get_certificates()
    providers = await client.peppol.query()
    print(len(certificates), len(providers.providers))
```

If you pass your own `httpx.AsyncClient`, the SDK will not close it:

```python
import httpx

from ksef2 import AsyncClient, Environment


http_client = httpx.AsyncClient()
client = AsyncClient(Environment.TEST, http_client=http_client)
try:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
    print(auth.access_token)
finally:
    await client.close()
    await http_client.aclose()
```

## Authentication

TEST authentication with an SDK-generated certificate:

```python
from ksef2 import AsyncClient, Environment


async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
    print(auth.access_token)
```

KSeF token authentication:

```python
from ksef2 import AsyncClient


async with AsyncClient() as client:
    auth = await client.authentication.with_token(
        ksef_token="your-ksef-token",
        nip="5261040828",
    )
    print(auth.refresh_token)
```

Refreshing an access token:

```python
refreshed = await client.authentication.refresh(refresh_token=auth.refresh_token)
print(refreshed.access_token.token)
```

## Online Sessions

Invoice sending is still session-scoped because KSeF requires session-specific
encryption material.

```python
from pathlib import Path

from ksef2 import FormSchema


async with auth.online_session(form_code=FormSchema.FA3) as session:
    result = await session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    status = await session.wait_for_invoice_ready(
        invoice_reference_number=result.reference_number,
    )
    print(status.ksef_number)
```

You can persist the state and resume a session later:

```python
state = session.get_state()
resumed = auth.resume_online_session(state)
status = await resumed.get_status()
print(status.reference_number)
```

## Invoices

Metadata queries, exports, package downloads, and direct invoice downloads live
on `auth.invoices`.

```python
from datetime import datetime, timedelta, timezone

from ksef2.domain.models import InvoicesFilter, InvoiceMetadataParams


filters = InvoicesFilter(
    role="seller",
    date_type="issue_date",
    date_from=datetime.now(tz=timezone.utc) - timedelta(days=7),
    date_to=datetime.now(tz=timezone.utc),
    amount_type="brutto",
)

metadata = await auth.invoices.query_metadata(filters=filters)
print(len(metadata.invoices))

async for page in auth.invoices.query_metadata_pages(
    filters=filters,
    params=InvoiceMetadataParams(page_size=250, sort_order="asc"),
):
    print(len(page.invoices), page.has_more)

async for invoice in auth.invoices.all_metadata(filters=filters):
    print(invoice.ksef_number)

export = await auth.invoices.schedule_export(filters=filters)
package = await auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
)
zip_parts = await auth.invoices.fetch_package_bytes(package=package, export=export)
print(len(zip_parts))
```

Use `fetch_package(...)` to write decrypted ZIP parts to disk:

```python
paths = await auth.invoices.fetch_package(
    package=package,
    export=export,
    target_directory="downloads",
)
for path in paths:
    print(path)
```

## Batch Sessions

For end-to-end batch work, use `auth.batch`.

```python
from ksef2.domain.models.batch import BatchInvoice


prepared = await auth.batch.prepare_batch(
    invoices=[
        BatchInvoice(
            file_name="invoice-1.xml",
            content=b"<Invoice>...</Invoice>",
        )
    ],
)

state = await auth.batch.submit_prepared_batch(prepared_batch=prepared)
print(state.reference_number)
```

For explicit upload control:

```python
async with auth.batch.open_session(prepared_batch=prepared) as session:
    await session.upload_parts()
    status = await session.get_status()
    print(status.status.description)
```

## Pagination

Async pagination helpers return async iterators.

```python
async for page in auth.tokens.list_all():
    for token in page.tokens:
        print(token.reference_number)

async for page in auth.sessions.all(page_size=10):
    print(len(page.items))
```

## TEST Data

`client.testdata` is available only for `Environment.TEST`.

```python
async with AsyncClient(Environment.TEST) as client:
    async with client.testdata.temporal() as testdata:
        await testdata.create_subject(
            nip="1234567890",
            subject_type="vat_group",
            description="temporary async test subject",
        )
```

## Related

- [Authentication](authentication.md)
- [Invoices](invoices.md)
- [Sessions](sessions.md)
- [Test Data](testdata.md)
