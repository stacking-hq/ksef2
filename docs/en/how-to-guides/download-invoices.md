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

### Resume after a restart

`job.resume_state()` returns an `ExportResumeState` with the reference number and
the key that decrypts the package. Save its JSON, and `export(state=...)` gives
the `ExportJob` back, so `wait()` still works.

```python
job = auth.invoices.export(filters)
saved = job.resume_state().to_json()   # store as a credential, never log it

# after a restart
job = auth.invoices.export(state=saved)
package = job.wait(timeout=300.0)
```

Pass exactly one of `filters` or `state`. `to_dict()`, `from_json()` and
`from_dict()` work like the session states; `model_dump()` and `repr()` redact the
key.

### Save and restore a completed export

`ExportResumeState` is for an export that has not finished. Once `wait()` returns,
store `package.archive` as plain ZIP or TarGz bytes in your own storage. Restore
those bytes with `ExportedInvoices.from_archive()`.

```python
from pathlib import Path

from ksef2.clients import ExportedInvoices

archive_path = Path("export.zip")
archive_path.write_bytes(package.archive)

# in another process
restored = ExportedInvoices.from_archive(archive_path.read_bytes())
for ksef_number, xml in restored.invoices():
    print(ksef_number, len(xml))

written = restored.save(Path("downloads"))
```

The factory defaults to `compression="zip"`. For TarGz exports, store the archive
bytes in a `.tar.gz` file and pass `compression="tar_gz"` when restoring. Use the
same compression format as the original export; the factory does not detect it.

Construction does not open or validate the archive. `metadata` reads
`_metadata.json` on first access and caches the result: `None` means the file is
absent, and `[]` means it contains no invoices. Invalid archives fail when read
or extracted; invalid metadata raises `KSeFValidationError` when accessed.
`save()` rejects unsafe paths, links and special files before writing anything.

The archive already contains decrypted invoice data. Protect it in your storage.
No encryption key or network access is needed to restore it. Package status and
presigned download URLs are not stored in the archive, so `restored.package` is
`None`. `await job.wait()` returns the same `ExportedInvoices` class, so sync and
async callers save and restore archives in the same way.

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

## Download a batch under rate limits

You do not need a fixed sleep between `download()` calls, and you do not need
to log in again after a `401`. The SDK honors KSeF's `Retry-After` up to
`RetryConfig.max_retry_after` (default 120 seconds), retries transient
failures, and refreshes the access token once after a `401`.

The one case the SDK hands back to you: KSeF asked to wait longer than the
ceiling. Then `download()` raises `KSeFRateLimitError` immediately, without
sleeping, and `error.retry_after` carries the true header value.

A single `download()` still blocks when the header is short enough to honor. If
KSeF repeats the same `Retry-After`, that one call waits up to
`(max_attempts - 1) * max_retry_after` before it raises, which is 240 seconds
with the defaults. Budget for that in a long batch.

```python
from pathlib import Path

from ksef2 import KSeFRateLimitError

downloads = Path("downloads")
try:
    for ksef_number in ksef_numbers:
        xml_bytes = auth.invoices.download(ksef_number)
        downloads.joinpath(f"{ksef_number}.xml").write_bytes(xml_bytes)
except KSeFRateLimitError as error:
    # KSeF asked to wait more than RetryConfig.max_retry_after seconds.
    # The SDK did not sleep. Schedule the remaining numbers for
    # error.retry_after seconds from now instead of retrying in a loop.
    print(f"slow down, resume in {error.retry_after} seconds")
```

See [Operations](../reference/operations.md) for the full `429` and `401`
behavior and what stays the app's job.

## Next workflows

- [Query invoices](query-invoices.md): Find KSeF numbers and metadata before downloading invoice content.
- [Send invoices](send-invoices.md): Submit invoice XML through online or batch sessions.
- [Querying and exports](../concepts/querying-and-exports.md): Understand metadata, direct downloads, export packages, and HWM sync.
- [Inspect encryption certificates](inspect-encryption-certificates.md): Check the public KSeF certificates used by encrypted workflows.


## Export a PDF with a verification QR

Install the optional dependencies with `pip install 'ksef2[pdf]'` and the native
libraries required by [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).

```python
from ksef2 import Environment
from ksef2.renderers import InvoicePDFExporter, PDFPageSize

exporter = InvoicePDFExporter(
    page_size=PDFPageSize.A4,
    verification_environment=Environment.TEST,
)
output = exporter.export_to_file(
    "invoice.xml",
    "invoice.pdf",
    ksef_number="9999999999-20260215-ABCDEF123456-AB",
)
```

Use the actual assigned KSeF number for the invoice. Supplying `ksef_number`
adds a locally generated SVG QR and displays that number below it. Omitting it
keeps the existing PDF output without a QR. The same keyword works with
`export_from_path()` and `export_from_string()`. `verification_environment` is
required; select the environment that issued the invoice.
The QR identifies the seller NIP, issue date and SHA-256 of the **original XML
bytes**, encoded as unpadded Base64URL, according to the
[Ministry's verification QR specification](https://github.com/CIRFMF/ksef-docs/blob/main/kody-qr.md).
Use bytes when calling `export_from_string()`; a string is encoded as UTF-8.
Reserializing an invoice changes its hash. Rendering does not check its acceptance
or verify that the supplied KSeF number belongs to it.

This option supports invoices that already have an assigned KSeF number. It does
not generate the offline certificate QR, sign URLs, or replace custom PDF layouts.

`PDFPageSize` supports `A4`, `A4_LANDSCAPE`, `A3`, `A3_LANDSCAPE`, `LETTER` and
`LETTER_LANDSCAPE`. With no `page_size`, the existing stylesheet setting remains,
normally A4 landscape. An explicit page size takes precedence over `html_overrides`
CSS; the other CSS rules still apply. Large invoice tables may need landscape
orientation or custom CSS to fit on a portrait page.
