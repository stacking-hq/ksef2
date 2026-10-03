---
title: Query Invoices
description: Query invoice metadata with ksef2 filters, pagination helpers, and polling.
---

Use `auth.invoices` when you need invoice metadata outside a sending session.
The examples below assume you already have an authenticated client named `auth`.

## Build a narrow filter

Start with the business question: which role, which date field, and which time
window should KSeF search?

```python
from datetime import datetime, timedelta, timezone

from ksef2.models import InvoicesFilter

now = datetime.now(tz=timezone.utc)

filters = InvoicesFilter.for_seller(
    date_from=now - timedelta(days=7),
    date_to=now,
    invoice_types=["vat"],
    invoicing_mode="online",
)
```

`InvoicesFilter` normalizes every accepted datetime to UTC before comparison and
request mapping. Values with an explicit offset preserve their instant. Naive
values are interpreted as Europe/Warsaw local time; ambiguous or nonexistent
daylight-saving times must include an explicit offset.

:::tip[Use permanent storage dates for sync]
`issue_date` is usually the right choice for accounting periods. For
unattended incremental sync, use `date_type="permanent_storage"` and
`restrict_to_permanent_storage_hwm_date=True`.
:::

## Query one page

Use `query_metadata()` when you need one page for a screen, reconciliation step,
or diagnostic check.

```python
from ksef2.models import InvoiceMetadataParams

page = auth.invoices.query_metadata(
    filters=filters,
    params=InvoiceMetadataParams(page_size=25, sort_order="asc"),
)

# QueryInvoicesMetadataResponse
# {
#   "has_more": false,
#   "is_truncated": false,
#   "permanent_storage_hwm_date": null,
#   "invoices": [
#     {
#       "ksef_number": "1234567890-20260625-...",
#       "invoice_number": "FV/42/2026",
#       "issue_date": "2026-06-25",
#       "gross_amount": 1230.0,
#       "currency": "PLN",
#       "invoice_type": "vat"
#     }
#   ]
# }

for invoice in page.invoices:
    print(invoice.ksef_number, invoice.invoice_number)
```

`has_more` means another page exists. `is_truncated` means the result hit a KSeF
window boundary and should continue from the returned lifecycle date rather than
from a normal page offset.

## Iterate through results

Use the page iterator when each page matters. Use the item iterator when your
job only needs invoice rows.

### Pages

```python
params = InvoiceMetadataParams(page_size=100, sort_order="asc")

for page in auth.invoices.query_metadata_pages(filters=filters, params=params):
    print(f"page={len(page.invoices)} has_more={page.has_more}")

    for invoice in page.invoices:
        print(invoice.ksef_number, invoice.permanent_storage_date)
```

### Invoices

```python
params = InvoiceMetadataParams(page_size=100, sort_order="asc")

for invoice in auth.invoices.all_metadata(filters=filters, params=params):
    print(invoice.ksef_number, invoice.invoice_number)
```

## Find a specific invoice

If you know your own invoice number, include it in the filter. If you already
have a KSeF number, prefer filtering by `ksef_number` or download the invoice
directly.

```python
filters = InvoicesFilter.for_seller(
    date_from=now - timedelta(days=30),
    date_to=now,
    invoice_number="FV/42/2026",
)

page = auth.invoices.query_metadata(filters=filters)
```

```python
filters = InvoicesFilter.for_seller(
    date_type="permanent_storage",
    date_from=now - timedelta(days=30),
    date_to=now,
    ksef_number="1234567890-20260625-...",
)

page = auth.invoices.query_metadata(filters=filters)
```

## Wait after sending

KSeF processing is asynchronous. If a workflow sends an invoice and immediately
needs it to become visible in retrieval APIs, poll with a narrow filter.

```python
filters = InvoicesFilter.for_seller(
    date_from=now - timedelta(days=1),
    date_to=now,
    invoice_number="FV/42/2026",
)

result = auth.invoices.wait_for_invoices(
    filters=filters,
    timeout=120.0,
    poll_interval=2.0,
)

# QueryInvoicesMetadataResponse
# {
#   "has_more": false,
#   "is_truncated": false,
#   "permanent_storage_hwm_date": null,
#   "invoices": [
#     {
#       "ksef_number": "1234567890-20260625-...",
#       "invoice_number": "FV/42/2026"
#     }
#   ]
# }
```

:::caution[Polling waits for any match]
`wait_for_invoices()` returns when at least one row matches the filter. Keep
the filter specific enough that the first match is the invoice you are waiting
for.
:::

## Recommended flow

1. Choose the subject role you are querying as.

2. Pick the date field that matches the job: accounting view, processing view,
   or incremental sync.

3. Build a narrow `InvoicesFilter`.

4. Fetch one page for interactive work, or use iterators for background jobs.

5. Store `ksef_number` values for later direct downloads or export
   reconciliation.

## Next workflows

- [Download invoices](download-invoices.md): Download invoice XML directly or through an encrypted export package.
- [Send invoices](send-invoices.md): Submit invoice XML through online or batch sessions before querying the result.
- [Querying and exports](../concepts/querying-and-exports.md): Understand metadata, direct downloads, export packages, and HWM sync.
