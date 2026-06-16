---
title: FA(3) Builder
description: Build FA(3) invoice XML with typed SDK helpers.
---

Use `ksef2.fa3` to build typed FA(3) invoices inside the SDK.
Import the builder and the commonly used enums directly from that namespace.

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, VatRate

invoice = (
    FA3InvoiceBuilder()
    .header(system_info="my app")
    .seller(
        name="ACME S.A.",
        tax_id="1234567890",
        country_code="PL",
        address_line_1="ul. Przykladowa 123",
        address_line_2="Warszawa",
    )
    .buyer(
        name="XYZ GmbH",
        country_code="DE",
        address_line_1="Unter den Linden 1",
        address_line_2="10115 Berlin",
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
    .build()
)
```

`build()` returns a `KsefInvoice` domain model.
If you want XML directly, call `to_xml()` on the builder instead.

## Import

```python
from ksef2.fa3 import FA3InvoiceBuilder, KsefInvoice, VatRate
```

## Builder Flow

The builder uses a nested DSL.
Each `.done()` returns to the previous level.

Typical flow:

1. Create the root builder.
2. Fill in `header(...)`, `seller(...)`, and `buyer(...)`.
3. Choose the invoice kind.
4. Add nested sections such as `rows()`, `payment()`, `transaction()`, or `annotations()`.
5. Finish with `build()`, `to_spec()`, or `to_xml()`.

Example with payment and annotations:

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, VatRate

builder = FA3InvoiceBuilder()
_ = (
    builder.header(system_info="my app")
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
        .issue_date(date(2026, 3, 29))
        .invoice_number("FV/2026/03/0001")
        .rows()
            .add_line(
                name="Consulting service",
                quantity=Decimal("1"),
                unit_of_measure="h",
                unit_price_net=Decimal("100.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
        .payment()
            .via("bank_transfer")
            .due_on(date(2026, 4, 12))
            .bank_account("PL10101010101010101010101010")
        .done()
        .annotations()
            .split_payment()
        .done()
    .done()
)

invoice = builder.build()
xml_text = builder.to_xml()
```

## Invoice Kinds

Use one of these body selectors:

- `standard()`
- `simplified()`
- `correction()`
- `advance()`
- `settlement()`
- `correction_advance()`
- `correction_settlement()`

## Output Forms

The same builder can produce the invoice in three forms:

- `build()` -> `KsefInvoice`
- `to_spec()` -> FA(3) `Faktura` model
- `to_xml()` -> XML string

```python
invoice = builder.build()
spec = builder.to_spec()
xml_text = builder.to_xml()
```

## XML And PDF Output

The SDK ships with a runnable example that:

1. builds an FA(3) invoice with `FA3InvoiceBuilder`
2. renders the invoice to XML
3. validates the XML against the FA(3) XSD
4. generates a PDF visualization from the XML

Run it from the repository root:

```bash
uv run --extra pdf -m scripts.examples.invoices.build_fa3_invoice
```

The example writes:

- `output/fa3_invoice.xml`
- `output/fa3_invoice.pdf`

If you want the same flow while keeping the builder object around, use:

```bash
uv run --extra pdf -m scripts.examples.invoices.build_fa3_invoice_builder
```

The PDF is a visualization of the generated XML, which is helpful for previewing invoice content before sending it to KSeF.

## Saving Drafts

You can persist the current builder state as a `KsefInvoiceDraft` and load it back later.
This works for incomplete drafts as well as fully populated invoices.

```python
from ksef2.fa3 import FA3InvoiceBuilder, KsefInvoiceDraft

builder = FA3InvoiceBuilder()
_ = (
    builder.header(system_info="my app")
    .seller(
        name="ACME S.A.",
        tax_id="1234567890",
        country_code="PL",
        address_line_1="ul. Przykladowa 123",
    )
)

draft = builder.dump_state()
json_text = builder.dump_state_json(indent=2)

same_draft = KsefInvoiceDraft.model_validate_json(json_text)
restored_builder = FA3InvoiceBuilder.from_state(same_draft)
restored_from_json = FA3InvoiceBuilder.from_state_json(json_text)
```

If you already have a built invoice and want to reopen it in the builder, use `from_invoice(...)`:

```python
invoice = builder.build()
restored_builder = FA3InvoiceBuilder.from_invoice(invoice)
```

## Sending The Built Invoice

You can send the generated XML through an online session:

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=builder.to_xml())
    print(result.reference_number)
```

## Common Types

`ksef2.fa3` also re-exports the models and enums that are commonly used with the builder:

- `KsefInvoice`
- `KsefInvoiceDraft`
- `InvoiceHeader`
- `InvoiceEntity`
- `InvoiceAddress`
- `InvoiceThirdParty`
- `ContactInfo`
- `VatRate`
- `VatClassification`
- `VatTreatment`
- `SaleCategory`
- `TaxRegime`
- `InvoiceSummaryOverrides`

## Examples

- [`scripts/examples/invoices/build_fa3_invoice.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/build_fa3_invoice.py)
- [`scripts/examples/invoices/build_fa3_invoice_builder.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/build_fa3_invoice_builder.py)
- [`scripts/examples/invoices/build_fa3_invoice_sample_1.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/invoices/build_fa3_invoice_sample_1.py)
- [`tests/integration/builders/fa3/test_standard_invoice.py`](https://github.com/stacking-hq/ksef2/blob/main/tests/integration/builders/fa3/test_standard_invoice.py)

## Related

- [Invoices](invoices.md)
- [Authentication](authentication.md)
