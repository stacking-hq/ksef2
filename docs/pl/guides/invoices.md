---
title: Faktury
description: Wysyłaj, wyszukuj, eksportuj i pobieraj faktury przez ksef2.
---

Użyj sesji online do wysyłki XML. Użyj `auth.invoices` do metadanych, eksportów,
paczek i pobierania faktur po numerze KSeF.

## Wyślij fakturę

```python
from pathlib import Path

from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=Path("invoice.xml").read_bytes(),
        timeout=60.0,
    )
    print(status.ksef_number)
```

## Metadane

```python
from datetime import datetime, timedelta, timezone

from ksef2.domain.models import InvoicesFilter

filters = InvoicesFilter(
    role="seller",
    date_type="issue_date",
    date_from=datetime.now(tz=timezone.utc) - timedelta(days=7),
    date_to=datetime.now(tz=timezone.utc),
    amount_type="brutto",
)

for invoice in auth.invoices.all_metadata(filters=filters):
    print(invoice.ksef_number)
```

## Eksport i pobieranie

```python
zip_parts = auth.invoices.export_and_download(filters=filters)
print(len(zip_parts))
```

```python
xml_bytes = auth.invoices.download_invoice(ksef_number="KSeF-number")
print(len(xml_bytes))
```

## Referencja

- [Wysyłanie faktur](../workflows/sending-invoices.mdx)
- [Wyszukiwanie faktur](../workflows/querying-invoices.mdx)
- [Pobieranie faktur](../workflows/downloading-invoices.mdx)
- [Interactive sending API](../reference/api/interactive-sending.md)
- [Invoice retrieval API](../reference/api/invoice-retrieval.md)
- [Status and UPO API](../reference/api/status-upo.md)
- [Builder FA(3)](fa3-builder.md)
