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

`auth.invoices.search()` returns a `Pager` over `InvoiceMetadata` rows, not
invoice XML. Iterate it, or use `pages()`, `first_page()` and `wait()`.

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

```python
from ksef2.models import InvoicesFilter

filters = InvoicesFilter.for_buyer(
    date_type="permanent_storage",
    date_from=last_synced_at,
    restrict_to_permanent_storage_hwm_date=True,
)

page = auth.invoices.search(filters).first_page()

# QueryInvoicesMetadataResponse
# {
#   "has_more": false,
#   "is_truncated": false,
#   "permanent_storage_hwm_date": "2026-06-25T10:00:00Z",
#   "invoices": [
#     {
#       "ksef_number": "1234567890-20260625-...",
#       "invoice_number": "FV/42/2026",
#       "permanent_storage_date": "2026-06-25T09:58:21Z"
#     }
#   ]
# }
```

If a metadata page or export package is truncated, continue from the returned
last date, such as `last_permanent_storage_date`, rather than assuming your
requested end of the window was fully covered. Deduplicate persisted records by
`ksef_number` when windows overlap.

Export packages can also include `_metadata.json`, which helps reconcile the
downloaded XML package contents with the metadata rows you store.

## Related pages

- [Query invoices](../how-to-guides/query-invoices.md): Search invoice metadata with filters, pagination, and polling.
- [Download invoices](../how-to-guides/download-invoices.md): Download one invoice XML document or a larger export package.
- [Invoice lifecycle](invoice-lifecycle.md): See how invoice submission, processing, storage, and retrieval fit together.
- [Encryption](encryption.md): Understand how public KSeF certificates protect session and export keys.
