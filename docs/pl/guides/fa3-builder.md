---
title: Budowanie XML FA(3)
description: Buduj XML faktury FA(3) typowanymi metodami SDK.
---

Użyj `ksef2.fa3`, gdy chcesz budować XML FA(3) w Pythonie, zamiast pisać go ręcznie.

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import InvoiceBuilder, VatRate

builder = (
    InvoiceBuilder()
    .header(system_info="my app")
    .seller(
        name="ACME S.A.",
        tax_id="5261040828",
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

`to_xml()` domyślnie zwraca zwarty zapis. Przekaż `pretty_print=True`, żeby dostać wcięcia ułatwiające czytanie XML.

## Przebieg

1. Utwórz `InvoiceBuilder`.
2. Uzupełnij `header(...)`, `seller(...)` i `buyer(...)`.
3. Wybierz typ faktury, na przykład `standard()` albo `correction()`.
4. Dodaj sekcje, na przykład `rows()`, `payment()` albo `annotations()`.
5. Zakończ przez `build()`, `to_spec()` albo `to_xml()`.

## Wczytywanie wersji roboczych

`KsefInvoiceDraft` i `InvoiceBuilder.from_state_json()` odrzucają nieznane pola w zagnieżdżonych sekcjach błędem `KSeFValidationError`.
Na przykład `qty` zamiast `quantity` wskazuje ścieżkę `body.rows.0.qty`.
Schemat `KsefInvoiceDraft.model_json_schema()` również zabrania nieznanych pól modeli zagnieżdżonych.
Wiersze częściowe nadal mogą pomijać `quantity`, a metadane załączników mogą zawierać własne klucze.

## Wyślij XML

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    submission = session.send_invoice(builder.to_xml())
    status = submission.wait()
    print(status.ksef_number)
```

## Opis API

- [Opis API FA(3)](../reference/api/fa3.md)
- [Faktury](invoices.md)
