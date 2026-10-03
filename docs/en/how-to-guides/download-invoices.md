---
title: Download Invoices
description: Download processed invoice XML directly or through encrypted export packages with ksef2.
---

Use `auth.invoices` when you need invoice content after KSeF has processed it.
The examples below assume you already have an authenticated client named `auth`.

## Download one invoice

If you already have a KSeF number, direct download is the shortest path.

```python
from pathlib import Path

ksef_number = "1234567890-20260625-..."

xml_bytes = auth.invoices.download(ksef_number)
Path("invoice.xml").write_bytes(xml_bytes)
```

If the invoice was just sent, KSeF may need time before the processed XML is
downloadable. Pass `timeout` and `download()` polls until the document is
available.

```python
xml_bytes = auth.invoices.download(ksef_number, timeout=120.0, poll_interval=2.0)
Path("invoice.xml").write_bytes(xml_bytes)
```

## Build an export filter

Use exports for larger downloads. Exports use `InvoicesFilter`, the same filter
shape used by metadata queries.

```python
from datetime import datetime, timedelta, timezone

from ksef2.models import InvoicesFilter

now = datetime.now(tz=timezone.utc)

filters = InvoicesFilter.for_buyer(
    date_type="permanent_storage",
    date_from=now - timedelta(days=1),
    date_to=now,
    restrict_to_permanent_storage_hwm_date=True,
)
```

:::tip[Use HWM for background sync]
`restrict_to_permanent_storage_hwm_date=True` keeps unattended exports inside
the boundary KSeF reports as complete. Store `permanent_storage_hwm_date` for
the next sync window.
:::

## Export many invoices

`export()` schedules the export and returns an `ExportJob`. Its `wait()` polls
until the package is ready, downloads and decrypts the parts, joins them and
returns an `ExportedInvoices` object.

```python
job = auth.invoices.export(filters)
package = job.wait(timeout=300.0)

for ksef_number, xml in package.invoices():
    print(ksef_number, len(xml))

# Parsed _metadata.json (list of InvoiceMetadata), or None if absent.
metadata = package.metadata

# Package details for incremental sync.
print(package.package.is_truncated, package.package.permanent_storage_hwm_date)
```

### Save files

```python
from pathlib import Path

written = package.save(Path("downloads"))
```

`save()` extracts the archive and refuses any entry whose path would escape the
target directory. The raw ZIP bytes are available as `package.archive`.

:::note[The SDK decrypts package parts]
KSeF returns encrypted package part URLs. `export()` loads a valid KSeF
encryption certificate, schedules the export with local AES material, and
`wait()` downloads the parts and decrypts them before returning.
:::

:::caution[Package parts are temporary]
Package URLs expire. Store the extracted invoice XML in your own storage, and
keep `_metadata.json` when the package includes it. If KSeF fails the export or
it expires, `wait()` raises `KSeFExportFailedError`.
:::

## After sending invoices

Keep sending, processing, and retrieval as separate phases.

1. Send invoice XML through an online or batch session.

2. Poll session or invoice status until KSeF reports a final accepted result.

3. Persist the returned `ksef_number` values.

4. Download one processed XML document by `ksef_number`, or build an export
   filter for a larger time window.

## Next workflows

- [Query invoices](query-invoices.md): Find KSeF numbers and metadata before downloading invoice content.
- [Send invoices](send-invoices.md): Submit invoice XML through online or batch sessions.
- [Querying and exports](../concepts/querying-and-exports.md): Understand metadata, direct downloads, export packages, and HWM sync.
- [Inspect encryption certificates](inspect-encryption-certificates.md): Check the public KSeF certificates used by encrypted workflows.
