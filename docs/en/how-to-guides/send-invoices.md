---
title: Send Invoices
description: Send FA(3) XML through ksef2 online sessions or batch sessions.
---

Use `auth.online_session(...)` for interactive submission and `auth.batch` for
larger file sets. The examples below assume you already have an authenticated
client named `auth`.

## Start with XML bytes

The send APIs accept invoice XML bytes. Those bytes can come from your ERP, a
file, or the SDK's FA(3) builder.

### From file

```python
from pathlib import Path

invoice_xml = Path("invoice.xml").read_bytes()
```

### From builder

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, VatRate

invoice_xml = (
    FA3InvoiceBuilder()
    .header(system_info="ksef2 send guide")
    .seller(
        name="Demo Seller Sp. z o.o.",
        tax_id="5261040828",
        country_code="PL",
        address_line_1="Prosta 1",
        address_line_2="00-001 Warszawa",
    )
    .buyer(
        name="Demo Buyer Sp. z o.o.",
        country_code="PL",
        address_line_1="Kwiatowa 2",
        address_line_2="00-002 Warszawa",
    )
    .standard()
        .issue_date(date.today())
        .issue_place("Warszawa")
        .invoice_number("FV/42/2026")
        .rows()
            .add_line(
                name="Consulting service",
                quantity=Decimal("1"),
                unit_price_net=Decimal("100.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
    .done()
    .to_xml()
    .encode("utf-8")
)
```

## Send in an online session

Use an online session when you want to submit one invoice or a small interactive
set. The session context manager closes the remote online session when the block
exits.

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    submission = session.send_invoice(invoice_xml)

    # InvoiceSubmission handle
    # submission.reference_number == "20260625-ABCD-EF1234567890"

    status = submission.wait(timeout=120.0, poll_interval=2.0)

    # SessionInvoiceStatusResponse
    # {
    #   "reference_number": "20260625-ABCD-EF1234567890",
    #   "ksef_number": "1234567890-20260625-...",
    #   "invoice_number": "FV/42/2026",
    #   "status": {
    #     "code": 200,
    #     "description": "Processed"
    #   }
    # }
```

`send_invoice()` only means KSeF accepted the encrypted payload into the session.
`submission.wait()` waits for the per-invoice result and returns the KSeF
number when processing succeeds. It also works after the session is closed, and
`session.wait()` returns the terminal status of the closed session.

:::tip[Chain it for simple scripts]
`session.send_invoice(invoice_xml).wait()` performs the submit-and-poll
sequence when you do not need the handle separately.
:::

## Keep session handles

Persist the handles before long polling or before handing work to another
process.

```python
with auth.online_session(form_code=FormSchema.FA3) as session:
    session_state_json = session.resume_state().to_json()
    submission = session.send_invoice(invoice_xml)
    invoice_reference_number = submission.reference_number

# Store session_state_json and invoice_reference_number in secure storage.
# Do not log session_state_json because it contains session encryption data.
```

## Send a batch

Use a batch when you need to submit many XML files as one KSeF batch workflow.
The high-level batch service prepares the ZIP package, encrypts package parts,
opens the batch session, uploads the parts, closes the session, and returns the closed
`BatchSessionClient`. Call its `wait()`, `list_failed_invoices()` and
`download_upo()` next. `auth.batch.prepare()` and `submit()` take `bytes`, `str`,
`Path` or `BatchInvoice` items.

### From paths

```python
from pathlib import Path

from ksef2 import FormSchema

prepared = auth.batch.prepare(
    [Path("invoice-1.xml"), Path("invoice-2.xml")],
    form_code=FormSchema.FA3,
)

session = auth.batch.submit(prepared)

# session.reference_number == "20260625-BATCH-..."
```

### From bytes

```python
from pathlib import Path

from ksef2 import FormSchema
from ksef2.models import BatchInvoice

session = auth.batch.submit(
    [
        BatchInvoice(
            file_name="invoice-1.xml",
            content=Path("invoice-1.xml").read_bytes(),
        ),
        BatchInvoice(
            file_name="invoice-2.xml",
            content=Path("invoice-2.xml").read_bytes(),
        ),
    ],
    form_code=FormSchema.FA3,
)

# session.reference_number == "20260625-BATCH-..."
```

## Wait for batch completion

After the batch is submitted, poll the batch session and inspect accepted and
failed invoices.

```python
final_status = session.wait(timeout=300.0, poll_interval=2.0)

# SessionStatusResponse
# {
#   "status": {
#     "code": 200,
#     "description": "Processed"
#   },
#   "invoice_count": 2,
#   "successful_invoice_count": 2,
#   "failed_invoice_count": 0,
#   "upo": {
#     "pages": [
#       {
#         "reference_number": "upo-page-reference"
#       }
#     ]
#   }
# }

accepted = session.list_invoices(page_size=100)
failed = session.list_failed_invoices(page_size=100)
```

:::caution[Batch success still needs inspection]
A batch status summarizes the session. Inspect accepted and failed invoice
pages before deciding that every invoice in the package reached the expected
business outcome.
:::

## Recommended flow

1. Authenticate for the seller context.

2. Load invoice XML from your system or build it with `FA3InvoiceBuilder`.

3. Use an online session for small interactive sending or `auth.batch` for
   larger sets.

4. Persist the returned session and invoice references before polling.

5. Poll status, store accepted and failed results, then download UPO or invoice
   XML from the follow-up pages.

## Next workflows

- [Get status and UPO](get-status-and-upo.md): Poll online and batch sessions, inspect results, and download UPO XML.
- [Build FA(3) invoices](build-fa3-invoices.md): Generate valid FA(3) XML when your application does not already have one.
- [Query invoices](query-invoices.md): Find processed invoices through metadata filters and pagination.
- [Download invoices](download-invoices.md): Download processed invoice XML after KSeF assigns a number.
