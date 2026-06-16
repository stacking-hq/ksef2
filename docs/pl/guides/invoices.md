---
title: Faktury
description: Wysyłka, statusy, metadane, eksporty i pobieranie faktur.
---

Faktury wysyłasz w sesjach online. Zapytania metadanych, eksporty i pobieranie
faktur są dostępne na `auth.invoices`.

## Wysłanie faktury

```python
from pathlib import Path
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    status = session.wait_for_invoice_ready(
        invoice_reference_number=result.reference_number,
        timeout=60.0,
    )
    print(status.ksef_number)
```

## Statusy i UPO

```python
status = session.get_invoice_status(invoice_reference_number="invoice-reference")
print(status.status.description)

upo = session.get_invoice_upo_by_ksef_number(ksef_number="KSeF-number")
print(len(upo))
```

## Metadane

```python
from datetime import datetime, timedelta, timezone
from ksef2.domain.models import InvoicesFilter, InvoiceMetadataParams

filters = InvoicesFilter(
    role="seller",
    date_type="issue_date",
    date_from=datetime.now(tz=timezone.utc) - timedelta(days=7),
    date_to=datetime.now(tz=timezone.utc),
    amount_type="brutto",
)

for page in auth.invoices.query_metadata_pages(
    filters=filters,
    params=InvoiceMetadataParams(page_size=250, sort_order="asc"),
):
    print(len(page.invoices), page.has_more)
```

## Eksport

```python
export = auth.invoices.schedule_export(filters=filters)
package = auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
    timeout=120.0,
    poll_interval=2.0,
)

paths = auth.invoices.fetch_package(
    package=package,
    export=export,
    target_directory="downloads",
)
```

## Async

Te same punkty wejścia istnieją na `AsyncClient`; operacje sieciowe wymagają
`await`, a sesje używają `async with`.
