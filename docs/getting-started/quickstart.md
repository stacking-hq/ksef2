---
title: Quickstart
description: Send and query invoices with sync or async KSeF2 clients.
---

This page shows the shape of the SDK in the TEST environment. Use a real MCU
certificate for DEMO or PRODUCTION.

## Choose a client mode

Use the sync client in ordinary scripts and command-line tools. Use the async
client when your application already owns an event loop.

### Sync


```python
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter

NIP = "5261040828"

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip=NIP)

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    status = session.wait_for_invoice_ready(
        invoice_reference_number=result.reference_number,
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

### Async


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

        async with auth.online_session(form_code=FormSchema.FA3) as session:
            result = await session.send_invoice(
                invoice_xml=Path("invoice.xml").read_bytes()
            )
            status = await session.wait_for_invoice_ready(
                invoice_reference_number=result.reference_number,
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

        export = await auth.invoices.schedule_export(filters=filters)
        package = await auth.invoices.wait_for_export_package(
            reference_number=export.reference_number,
            timeout=120.0,
        )
        zip_parts = await auth.invoices.fetch_package_bytes(
            package=package,
            export=export,
        )
        print(len(zip_parts))


asyncio.run(main())
```


## What happened

1. The root client selected the TEST environment.
2. `with_test_certificate()` created a TEST-only XAdES certificate and returned
   an authenticated client.
3. `online_session()` opened a session with invoice-specific encryption data.
4. `wait_for_invoice_ready()` and `wait_for_export_package()` used timeout
   seconds and polling intervals rather than attempt counts.

## Related pages

- [Authentication](authentication.md)
- [Invoices](../guides/invoices.md)
- [Async client](../guides/async-client.md)
