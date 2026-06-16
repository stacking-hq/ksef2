---
title: Invoices
description: Send, query, export, and download invoices with KSeF2 clients.
---

Use online sessions to send invoices and `auth.invoices` for metadata queries, exports, and downloads.

Async applications use the same entry points on `AsyncClient`; await network
operations and use `async with auth.online_session(...)` for session
lifecycle management.

## Send an Invoice

```python
from datetime import date
from pathlib import Path

from ksef2 import FormSchema
from ksef2.core.invoices import InvoiceTemplater

template_xml = Path("invoice-template.xml").read_text(encoding="utf-8")
invoice_xml = InvoiceTemplater.create(
    template_xml,
    {
        "#nip#": "5261040828",
        "#invoicing_date#": date.today().isoformat(),
        "#invoice_number#": "123/2026",
    },
)

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=invoice_xml)
    print(result.reference_number)

    status = session.wait_for_invoice_ready(
        invoice_reference_number=result.reference_number
    )
    print(status.ksef_number)
```

SDK endpoint: `POST /sessions/online/{referenceNumber}/invoices`

Async version:

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

## Session Invoice Operations

```python
status = session.get_invoice_status(invoice_reference_number="invoice-reference")
print(status.ksef_number, status.status.description)

ready = session.wait_for_invoice_ready(invoice_reference_number="invoice-reference")
print(ready.ksef_number)

invoices = session.list_invoices()
for invoice in invoices.invoices:
    print(invoice.reference_number, invoice.ksef_number, invoice.status.description)

failed = session.list_failed_invoices()
print(len(failed.invoices))
```

SDK endpoints:
- `GET /sessions/{referenceNumber}/invoices`
- `GET /sessions/{referenceNumber}/invoices/failed`
- `GET /sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}`

`wait_for_invoice_ready()` is an SDK helper built on top of `GET /sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}`.

UPO downloads also stay on the session client:

```python
upo_by_ref = session.get_invoice_upo_by_reference(
    invoice_reference_number="invoice-reference",
)
upo_by_ksef = session.get_invoice_upo_by_ksef_number(
    ksef_number="KSeF-number",
)
print(len(upo_by_ref), len(upo_by_ksef))
```

SDK endpoints:
- `GET /sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}/upo`
- `GET /sessions/{referenceNumber}/invoices/ksef/{ksefNumber}/upo`

## Download a Processed Invoice

Once you have a `ksef_number`, download the XML directly from `auth.invoices`:

```python
xml_bytes = auth.invoices.download_invoice(ksef_number="KSeF-number")
print(len(xml_bytes))
```

SDK endpoint: `GET /invoices/ksef/{ksefNumber}`

## Query Invoice Metadata

Metadata queries and exports use `InvoicesFilter`.
`amount_type` is required by the current public model.
Public filter literals use lowercase SDK values such as `"online"` and `"vat"`;
the SDK maps them to the schema-native enum values internally.

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

SDK endpoint: `POST /invoices/query/metadata`

`query_metadata` performs one KSeF request. To follow `hasMore` pagination and
the KSeF `isTruncated` date-range reset rule explicitly, iterate pages:

```python
for page in auth.invoices.query_metadata_pages(
    filters=filters,
    params=InvoiceMetadataParams(page_size=250, sort_order="asc"),
):
    print(len(page.invoices), page.has_more, page.is_truncated)
```

For the item-level pattern used by other offset-paginated SDK clients:

```python
for invoice in auth.invoices.all_metadata(filters=filters):
    print(invoice.ksef_number)
```

If you need to wait for invoices to become visible:

```python
result = auth.invoices.wait_for_invoices(filters=filters, timeout=120.0)
print(len(result.invoices))
```

## Export Invoices

```python
export = auth.invoices.schedule_export(filters=filters)
print(export.reference_number)

package = auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
    timeout=120.0,
    poll_interval=2.0,
)

paths = auth.invoices.fetch_package(
    package=package,
    export=export,
    target_directory="downloads",
)
for path in paths:
    print(path)
```

SDK endpoints:
- `POST /invoices/exports`
- `GET /invoices/exports/{referenceNumber}`

If you prefer to keep ZIP contents in memory:

```python
zip_parts = auth.invoices.fetch_package_bytes(package=package, export=export)
print(len(zip_parts))
```

Or perform the whole export flow in one call:

```python
zip_parts = auth.invoices.export_and_download(filters=filters)
print(len(zip_parts))
```

Async export:

```python
export = await auth.invoices.schedule_export(filters=filters)
package = await auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
)
zip_parts = await auth.invoices.fetch_package_bytes(package=package, export=export)
print(len(zip_parts))
```

## Examples

- [`scripts/examples/invoices/send_invoice.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/send_invoice.py)
- [`scripts/examples/invoices/send_query_export_download.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/send_query_export_download.py)
- [`scripts/examples/invoices/batch_export_to_pdf.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/batch_export_to_pdf.py)
- [`scripts/examples/invoices/download_purchase_invoices.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/download_purchase_invoices.py)
- [`scripts/examples/scenarios/download_and_export_to_pdf.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/scenarios/download_and_export_to_pdf.py)
- [`scripts/examples/scenarios/download_purchase_invoices.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/scenarios/download_purchase_invoices.py)

## Related

- [FA(3) Builder](fa3-builder.md)
- [Sessions](sessions.md)
- [Authentication](authentication.md)
- [Async Client](async-client.md)
