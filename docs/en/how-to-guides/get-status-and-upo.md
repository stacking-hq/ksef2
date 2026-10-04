---
title: Get Status and UPO
description: Check online and batch session status, list session invoices, and download UPO documents.
---

Use this page after you have submitted invoice XML. The examples assume you
already have an authenticated client named `auth`.

Status calls return SDK models. UPO calls return XML bytes.

## Online invoice status

For online sending, `send_invoice()` returns a session invoice reference. Use
that reference to poll the invoice result and download invoice UPO.

```python
from pathlib import Path

from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    submission = session.send_invoice(invoice_xml)

    invoice_status = submission.wait(timeout=120.0, poll_interval=2.0)

    # SessionInvoiceStatusResponse
    # {
    #   "ordinal_number": 1,
    #   "reference_number": "20260625-ABCD-EF1234567890",
    #   "invoice_number": "FV/42/2026",
    #   "ksef_number": "1234567890-20260625-...",
    #   "status": {
    #     "code": 200,
    #     "description": "Processed"
    #   }
    # }

    upo_xml = submission.download_upo()
    Path("upo.xml").write_bytes(upo_xml)
```

`download_upo()` waits for processing itself, so calling it right after
`send_invoice()` works too. Pass `timeout` and `poll_interval` to control how long
it waits.

Inside the same session block, if you already have the KSeF number, you can
download invoice UPO by KSeF number instead:

```python
ksef_number = invoice_status.ksef_number
if ksef_number is None:
    raise RuntimeError("KSeF did not assign an invoice number.")

upo_xml = session.download_invoice_upo(ksef_number=ksef_number)
```

:::caution[Keep the invoice reference]
The invoice reference number is the durable handle for polling one invoice in
the session. Store it before waiting so another worker can inspect the result
if the original process stops.
:::

## Online session pages

Use session pages when you need to inspect everything submitted in an online
session instead of one invoice reference.

### Accepted

```python
page = session.list_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.reference_number, invoice.ksef_number)
```

### Failed

```python
page = session.list_failed_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.reference_number, invoice.status.code, invoice.status.details)
```

## Batch status and UPO

For batch sending, keep the returned `BatchSessionResumeState`. The batch service can
poll by state or by plain session reference number.

```python
from pathlib import Path

final_status = session.wait(timeout=300.0, poll_interval=2.0)

# SessionStatusResponse
# {
#   "status": {
#     "code": 200,
#     "description": "Processed"
#   },
#   "invoice_count": 10,
#   "successful_invoice_count": 9,
#   "failed_invoice_count": 1,
#   "upo": {
#     "pages": [
#       {
#         "reference_number": "upo-page-reference",
#         "download_url_expiration_date": "2026-06-26T10:00:00Z"
#       }
#     ]
#   }
# }

for number, upo_xml in enumerate(session.download_upo(), start=1):
    Path(f"batch-upo-{number}.xml").write_bytes(upo_xml)
```

:::note[UPO is an audit artifact]
Store UPO XML durably. It is the official confirmation document, not just a
temporary status response.
:::

## List accepted and failed batch invoices

Accepted and failed invoices are separate pages. Read both when reconciling a
batch.

### Accepted

```python
page = session.list_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.invoice_file_name, invoice.ksef_number, invoice.status.description)
```

### Failed

```python
page = session.list_failed_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.invoice_file_name, invoice.status.code, invoice.status.details)
```

When a page has `continuation_token`, pass it to the next call:

```python
page = session.list_invoices(page_size=100)

while page.continuation_token is not None:
    page = session.list_invoices(
        page_size=100,
        continuation_token=page.continuation_token,
    )
```

## Find sessions after restart

Use `auth.invoice_sessions` when you need to find online or batch sessions after
the original sender process has exited.

`list()` returns a `Pager`: iterate it for every session, call `.pages()` for
page-sized lists, or `.first_page()` to make a single request.

### One page

```python
sessions = auth.invoice_sessions.list(
    "online",
    statuses=["in_progress", "succeeded"],
).first_page()

for item in sessions:
    print(item.reference_number, item.status.code, item.total_invoice_count)
```

### All sessions

```python
for item in auth.invoice_sessions.list("batch"):
    print(item.reference_number, item.status.description)
```

## Recommended flow

1. Persist session references and invoice reference numbers when sending.

2. Poll the specific invoice, online session, or batch session that matches the
   question you are answering.

3. Store accepted and failed invoice details.

4. Download UPO XML and store it with your audit records.

5. Use `auth.invoice_sessions` to recover session references after process
   restart.

## Next workflows

- [Send invoices](send-invoices.md): Submit invoice XML through online or batch sessions before polling status.
- [Status and UPO](../concepts/status-and-upo.md): Understand status surfaces, UPO documents, polling, and local timeouts.
- [Download invoices](download-invoices.md): Fetch processed invoice XML after KSeF assigns a number.
- [Query invoices](query-invoices.md): Find processed invoices through metadata filters and pagination.
