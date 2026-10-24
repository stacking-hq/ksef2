---
title: Querying and Exports
description: Understand invoice metadata, direct downloads, export handles, package downloads, and incremental sync.
---

Invoice retrieval has three different jobs:

- metadata queries answer "which invoices exist for this subject and filter?";
- direct downloads answer "give me the processed XML for this KSeF number";
- exports answer "prepare a downloadable package for this larger set of invoices".

KSeF is best treated as the exchange system and source of official invoice
records, not as the database behind every screen in your application. For most
integrations, the stable pattern is to query or export from KSeF, persist the
result locally, and serve operational views from your own store.

## Metadata finds invoices

`auth.invoices.search()` returns an `InvoiceSearchPager` over `InvoiceMetadata`
rows. Iterate it, or use `pages()`, `first_page()`, `page(cursor)` and `wait()`.
These retain the generic `Pager` contracts. `page(cursor)` reads one page and
returns the `next_cursor` that resumes the same search later, even in another
process. Only a `next_cursor` of `None` ends a search: a page can come back
empty and still name the page after it. Use `responses()` for complete typed pages or
`first_response()` for a single `QueryInvoicesMetadataResponse` with pagination
flags and `permanent_storage_hwm_date`.

Metadata is useful for lists, reconciliation, polling after submission, and
deciding what to download later. A metadata row can include identifiers, dates,
party data, amounts, schema fields, hashes, attachment flags, and invoice mode.

The filter describes the view KSeF should search:

- `role`, such as `seller` or `buyer`;
- `date_type`, `date_from`, and `date_to`;
- optional `amount_min` and `amount_max`, with `amount_type` when an amount range is used;
- identifiers such as `seller_nip`, `buyer_nip`, `invoice_number`, or `ksef_number`;
- optional invoice data such as `invoice_types`, `invoice_schema`, `has_attachment`, and `invoicing_mode`.

:::tip[Amount type belongs to amount ranges]
Set `amount_type` only when you use `amount_min` or `amount_max`. The SDK
validates that range filters name the KSeF amount field they apply to.
:::

## Direct download gets one XML document

`auth.invoices.download()` downloads one processed invoice XML document
by `ksef_number`.

This path is intentionally narrow. Use it when you already have the KSeF number
from a session result, metadata query, UPO workflow, or your own database. If
the invoice was just accepted and KSeF has not exposed the XML yet,
`auth.invoices.download(ksef_number, timeout=...)` polls until the document is
downloadable or the local timeout expires.

## Exports produce encrypted packages

Exports are asynchronous. `auth.invoices.export()` takes the same `InvoicesFilter`
shape used for metadata queries and returns an `ExportJob`. Its `wait()` polls
until the package is ready, downloads and decrypts the parts, joins them and
returns an `ExportedInvoices` object.

```text
InvoicesFilter
  -> auth.invoices.export()
    -> ExportJob
      -> job.wait()
        -> ExportedInvoices: invoices(), metadata, archive, save()
```

:::caution[Treat export handles as sensitive]
The `ExportJob` holds the local AES key material needed to decrypt the
package. To survive a restart, persist `job.resume_state().to_json()` as a
credential and pass it to `auth.invoices.export(state=...)`; never log it.
:::

## Every asynchronous handle saves its state

An export is not the only operation that outlives the call that started it. The
handles for a generated token, a certificate enrollment, a permission operation
and a submitted invoice save and resume the same way: `resume_state()` returns
the state, `to_json()` writes it, and one method on the client reads it back.

| Handle | Save with | Resume with |
| --- | --- | --- |
| `ExportJob` | `job.resume_state()` | `auth.invoices.export(state=...)` |
| `GeneratedToken` | `token.resume_state()` | `auth.tokens.generation(state)` |
| `CertificateEnrollment` | `enrollment.resume_state()` | `auth.certificates.enrollment(state)` |
| `PermissionOperation` | `operation.resume_state()` | `auth.permissions.operation(state)` |
| `InvoiceSubmission` | `submission.resume_state()` | `session.submission(state=...)` |

Only `ExportResumeState` carries secrets. The other four states hold the KSeF
reference number, and the submission state also names the session the invoice
went into, so their `to_dict()` and `to_json()` output is ordinary data rather
than a credential. In particular `GeneratedTokenResumeState` never contains the
one-time token: persist that secret separately, as above.

A resumed handle polls the same reference number the original one did. It does
not invent data that was not stored, so a resumed token has no `token` and a
resumed enrollment has no `timestamp`.

## HWM is the sync boundary

For unattended synchronization, the important concept is HWM: High Water Mark.
When KSeF returns `permanent_storage_hwm_date`, it is telling you that
permanent-storage invoice data is complete up to that boundary.

The reliable sync shape is:

```text
last persisted permanent_storage_date
  -> query/export with restrict_to_permanent_storage_hwm_date=True
    -> persist metadata and invoice content locally
      -> store permanent_storage_hwm_date as the next starting boundary
```

Use `date_type="permanent_storage"` when your goal is incremental sync. Use
`restrict_to_permanent_storage_hwm_date=True` so KSeF clips the result to the
safe completed boundary.

The example assumes an authenticated `auth`, a saved `last_synced_at`, and your
`persist_metadata(invoice)` and `save_checkpoint(datetime)` storage functions.
Make metadata writes durable and deduplicate by `ksef_number`. Save the checkpoint
only after every page has been consumed and persisted successfully.

```python
from datetime import timedelta

from ksef2.models import InvoiceMetadataParams, InvoicesFilter

filters = InvoicesFilter.for_buyer(
    date_type="permanent_storage",
    date_from=last_synced_at,
    date_to=last_synced_at + timedelta(days=100),
    restrict_to_permanent_storage_hwm_date=True,
)

next_checkpoint = None
for page in auth.invoices.search(
    filters, InvoiceMetadataParams(sort_order="asc")
).responses():
    for invoice in page.invoices:
        persist_metadata(invoice)
    if not page.has_more and not page.is_truncated:
        next_checkpoint = page.permanent_storage_hwm_date

if next_checkpoint is not None:
    save_checkpoint(next_checkpoint)
```

An empty, completed response can still provide a checkpoint. If KSeF omits
the HWM, or the final response is truncated, keep the previous checkpoint.
In async code, use `async for page in pager.responses()`,
`page = await pager.first_response()` and
`page = await pager.page(cursor)` to read one page and its cursor.

`responses()` follows metadata page and truncation boundaries automatically.
For a truncated export package, continue from its `last_permanent_storage_date`
rather than assuming the requested window was fully covered. Deduplicate
persisted records by `ksef_number` when windows overlap.

Export packages can also include `_metadata.json`, which helps reconcile the
downloaded XML package contents with the metadata rows you store.

## Related pages

- [Query invoices](../how-to-guides/query-invoices.md): Search invoice metadata with filters, pagination, and polling.
- [Download invoices](../how-to-guides/download-invoices.md): Download one invoice XML document or a larger export package.
- [Invoice lifecycle](invoice-lifecycle.md): See how invoice submission, processing, storage, and retrieval fit together.
- [Encryption](encryption.md): Understand how public KSeF certificates protect session and export keys.
