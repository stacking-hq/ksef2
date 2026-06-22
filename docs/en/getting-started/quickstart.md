---
title: Quickstart
description: Send and query invoices with sync or async ksef2 clients.
---

This page shows the shape of the SDK in the TEST environment. You create a
client, authenticate, send one FA(3) invoice, then query recent invoice
metadata.

## Install

```bash
pip install ksef2
```

ksef2 requires Python 3.12 or newer.

## Send an invoice

Use `Client` in scripts and command-line tools. Use `AsyncClient` only when your
application already owns an event loop.

```python
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter

NIP = "5261040828"

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip=NIP)

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=Path("invoice.xml").read_bytes(),
        timeout=60.0,
    )
    print(status.ksef_number)

filters = InvoicesFilter(
    role="seller",
    date_type="issue_date",
    date_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
    date_to=datetime.now(tz=timezone.utc),
    amount_type="brutto",
)

export = auth.invoices.schedule_export(filters=filters)
package = auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
    timeout=120.0,
)

for path in auth.invoices.fetch_package(
    package=package,
    export=export,
    target_directory="downloads",
):
    print(path)
```

For repeated local or production work, create a CLI-compatible profile and use
the same profile from Python:

```python
from ksef2 import Client, Environment

client = Client(Environment.PRODUCTION)
auth = client.authentication.with_profile("prod-token")
```

## Async shape

The async client uses the same branches and method names. Await network calls
and use async context managers for client/session lifecycles.

```python
import asyncio
from pathlib import Path

from ksef2 import AsyncClient, Environment, FormSchema

NIP = "5261040828"


async def main() -> None:
    async with AsyncClient(Environment.TEST) as client:
        auth = await client.authentication.with_test_certificate(nip=NIP)

        async with auth.online_session(form_code=FormSchema.FA3) as session:
            status = await session.send_invoice_and_wait(
                invoice_xml=Path("invoice.xml").read_bytes(),
                timeout=60.0,
            )
            print(status.ksef_number)


asyncio.run(main())
```

## What happened

1. The root client selected the TEST environment.
2. `with_test_certificate()` created a TEST-only XAdES certificate and returned
   an authenticated client.
3. `online_session()` opened an invoice session with encryption material.
4. `send_invoice_and_wait()` sent XML and waited until KSeF assigned a number.
5. `auth.invoices` handled metadata export and package download outside the
   sending session.

## Related pages

- [Client setup](../workflows/client-setup.mdx)
- [Authentication workflow](../workflows/authentication.mdx)
- [Sending invoices](../workflows/sending-invoices.mdx)
- [Downloading invoices](../workflows/downloading-invoices.mdx)
- [API reference](../reference/api-signatures.md)
