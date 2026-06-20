---
title: Builder FA(3)
description: Buduj XML faktury FA(3) typowanymi pomocnikami SDK.
---

Użyj `ksef2.fa3`, gdy chcesz budować XML FA(3) w Pythonie zamiast pisać XML
ręcznie.

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
    .buyer(name="XYZ GmbH", country_code="DE", address_line_1="Unter den Linden 1")
    .standard()
        .issue_date(date(2026, 3, 29))
        .invoice_number("FV/2026/03/0001")
        .rows()
            .add_line(
                name="Consulting service",
                quantity=Decimal("10"),
                unit_of_measure="h",
                unit_price_net=Decimal("100.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
    .done()
)

xml_text = builder.to_xml()
```

## Przepływ

1. Utwórz `FA3InvoiceBuilder`.
2. Uzupełnij `header(...)`, `seller(...)` i `buyer(...)`.
3. Wybierz typ faktury, np. `standard()` albo `correction()`.
4. Dodaj sekcje, np. `rows()`, `payment()` albo `annotations()`.
5. Zakończ przez `build()`, `to_spec()` albo `to_xml()`.

## Wyślij XML

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=builder.to_xml().encode("utf-8"),
    )
    print(status.ksef_number)
```

## Referencja

- [FA(3) API reference](../reference/api/fa3.md)
- [Faktury](invoices.md)
