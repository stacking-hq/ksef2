---
title: Invoices
description: Send, query, export, and download invoices with ksef2 clients.
---

Use online sessions to send invoice XML. Use `auth.invoices` for metadata
queries, exports, package download, and direct invoice download.

Async applications use the same entry points on `AsyncClient`; await network
operations and use `async with auth.online_session(...)` for session lifecycle.

## Send an invoice

```python
from pathlib import Path

from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=Path("invoice.xml").read_bytes(),
        timeout=60.0,
    )
    print(status.ksef_number)
```

If you need more control, call `send_invoice()` and poll the returned reference
number yourself.

```python
result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
status = session.wait_for_invoice_ready(
    invoice_reference_number=result.reference_number,
)
```

## Query metadata

```python
from datetime import datetime, timedelta, timezone

from ksef2.domain.models import InvoicesFilter, InvoiceMetadataParams

filters = InvoicesFilter(
    role="seller",
    date_type="issue_date",
    date_from=datetime.now(tz=timezone.utc) - timedelta(days=7),
    date_to=datetime.now(tz=timezone.utc),
    amount_type="brutto",
    invoicing_mode="online",
    invoice_types=["vat"],
)

result = auth.invoices.query_metadata(
    filters=filters,
    params=InvoiceMetadataParams(sort_order="asc"),
)
print(len(result.invoices))
```

Use iterator helpers when you want the SDK to follow pagination.

```python
for page in auth.invoices.query_metadata_pages(filters=filters):
    print(len(page.invoices), page.has_more)

for invoice in auth.invoices.all_metadata(filters=filters):
    print(invoice.ksef_number)
```

## Export and download

```python
zip_parts = auth.invoices.export_and_download(filters=filters)
print(len(zip_parts))
```

Use the lower-level calls when you want to persist package files as they arrive.

```python
export = auth.invoices.schedule_export(filters=filters)
package = auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
)

for path in auth.invoices.fetch_package(
    package=package,
    export=export,
    target_directory="downloads",
):
    print(path)
```

## Download by KSeF number

```python
xml_bytes = auth.invoices.download_invoice(ksef_number="KSeF-number")
print(len(xml_bytes))
```

## Async shape

```python
export = await auth.invoices.schedule_export(filters=filters)
package = await auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
)
zip_parts = await auth.invoices.fetch_package_bytes(package=package, export=export)
print(len(zip_parts))
```

## Reference

- [Sending invoices](../workflows/sending-invoices.mdx)
- [Querying invoices](../workflows/querying-invoices.mdx)
- [Downloading invoices](../workflows/downloading-invoices.mdx)
- [Interactive sending API](../reference/api/interactive-sending.md)
- [Invoice retrieval API](../reference/api/invoice-retrieval.md)
- [Status and UPO API](../reference/api/status-upo.md)
