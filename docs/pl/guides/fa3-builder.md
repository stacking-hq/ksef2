---
title: Builder FA(3)
description: Budowanie typowanych faktur FA(3) i renderowanie XML.
---

Publiczny facade znajduje się w `ksef2.fa3`.

```python
from ksef2.fa3 import FA3InvoiceBuilder

xml = (
    FA3InvoiceBuilder()
    .header(invoice_number="FV/1/2026")
    .seller(nip="5261040828", name="Sprzedawca")
    .buyer(nip="1234567890", name="Nabywca")
    .standard()
    .done()
    .to_xml()
)
```

## Stan roboczy

Builder potrafi zrzucić i odtworzyć stan:

```python
draft = builder.dump_state()
restored = FA3InvoiceBuilder.from_state(draft)
```

## Modele

Jeżeli masz gotowe modele domenowe, możesz używać metod `*_model()` zamiast
podawać pojedyncze pola.

```python
from ksef2.fa3 import InvoiceEntity

builder.seller_model(InvoiceEntity(nip="5261040828", name="Sprzedawca"))
```
