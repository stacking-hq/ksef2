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

`auth.invoices.search()` returns a lazy `Pager`; nothing is requested until you
use it. Call `first_page()` when you need one page for a screen, reconciliation
step, or diagnostic check.

```python
from ksef2.models import InvoiceMetadataParams

pager = auth.invoices.search(
    filters,
    InvoiceMetadataParams(page_size=25, sort_order="asc"),
)

for invoice in pager.first_page():
    print(invoice.ksef_number, invoice.invoice_number)
```

## Iterate through results

Iterate the pager for invoice rows, or call `pages()` when each page matters.
The pager follows KSeF page and truncation boundaries for you.

### Pages

```python
params = InvoiceMetadataParams(page_size=100, sort_order="asc")

for page in auth.invoices.search(filters, params).pages():
    print(f"page={len(page)}")

    for invoice in page:
        print(invoice.ksef_number, invoice.permanent_storage_date)
```

### Invoices

```python
params = InvoiceMetadataParams(page_size=100, sort_order="asc")

for invoice in auth.invoices.search(filters, params):
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

page = auth.invoices.search(filters).first_page()
```

```python
filters = InvoicesFilter.for_seller(
    date_type="permanent_storage",
    date_from=now - timedelta(days=30),
    date_to=now,
    ksef_number="1234567890-20260625-...",
)

page = auth.invoices.search(filters).first_page()
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

pager = auth.invoices.search(filters).wait(timeout=120.0, poll_interval=2.0)

for invoice in pager:
    print(invoice.ksef_number, invoice.invoice_number)
```

:::caution[Polling waits for any match]
`wait()` returns when at least one row matches the filter. Keep the filter
specific enough that the first match is the invoice you are waiting for. If
nothing appears in time it raises `KSeFInvoiceQueryTimeoutError`.
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
