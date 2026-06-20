---
title: FA(3) Builder
description: Build FA(3) invoice XML with typed SDK helpers.
---

Use `ksef2.fa3` when you want to build FA(3) invoice XML in Python instead of
hand-writing XML.

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, VatRate

builder = (
    FA3InvoiceBuilder()
    .header(system_info="my app")
    .seller(
        name="ACME S.A.",
        tax_id="1234567890",
        country_code="PL",
        address_line_1="ul. Przykladowa 123",
    )
    .buyer(
        name="XYZ GmbH",
        country_code="DE",
        address_line_1="Unter den Linden 1",
    )
    .standard()
        .issue_place("Warszawa")
        .issue_date(date(2026, 3, 29))
        .invoice_number("FV/2026/03/0001")
        .rows()
            .add_line(
                name="Consulting service",
                supply_date=date(2026, 3, 29),
                unit_of_measure="h",
                quantity=Decimal("10"),
                unit_price_net=Decimal("100.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
    .done()
)

xml_text = builder.to_xml()
```

The usual flow is:

1. Create the root builder.
2. Fill in `header(...)`, `seller(...)`, and `buyer(...)`.
3. Choose the invoice kind.
4. Add nested sections such as `rows()`, `payment()`, or `annotations()`.
5. Finish with `build()`, `to_spec()`, or `to_xml()`.

Each `.done()` returns to the previous builder level.

## Invoice kinds

- `standard()`
- `simplified()`
- `correction()`
- `advance()`
- `settlement()`
- `correction_advance()`
- `correction_settlement()`

## Output forms

```python
invoice = builder.build()     # KsefInvoice
spec = builder.to_spec()      # FA(3) Faktura model
xml_text = builder.to_xml()   # XML string
```

## Save and load drafts

Persist the builder state when a user can leave an invoice unfinished.

```python
from ksef2.fa3 import FA3InvoiceBuilder, KsefInvoiceDraft

draft = builder.dump_state()
json_text = builder.dump_state_json(indent=2)

same_draft = KsefInvoiceDraft.model_validate_json(json_text)
restored = FA3InvoiceBuilder.from_state(same_draft)
restored_from_json = FA3InvoiceBuilder.from_state_json(json_text)
```

## Send the XML

Send builder output through the same online-session flow as hand-written XML.

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=builder.to_xml().encode("utf-8"),
    )
    print(status.ksef_number)
```

## Reference

- [FA(3) API reference](../reference/api/fa3.md)
- [Invoices](invoices.md)
