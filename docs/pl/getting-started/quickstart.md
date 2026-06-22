---
title: Quickstart
description: Wyślij i pobierz faktury klientem ksef2.
---

Ten przykład pokazuje podstawowy przepływ w środowisku TEST: klient,
uwierzytelnienie, wysyłka faktury FA(3) i eksport metadanych.

## Instalacja

```bash
pip install ksef2
```

ksef2 wymaga Pythona 3.12 lub nowszego.

## Wyślij fakturę

```python
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter

NIP = "5261040828"

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip=NIP)

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(
        invoice_xml=Path("invoice.xml").read_bytes(),
        timeout=60.0,
    )
    print(status.ksef_number)

filters = InvoicesFilter(
    role="seller",
    date_type="issue_date",
    date_from=datetime.now(tz=timezone.utc) - timedelta(days=1),
    date_to=datetime.now(tz=timezone.utc),
    amount_type="brutto",
)

export = auth.invoices.schedule_export(filters=filters)
package = auth.invoices.wait_for_export_package(
    reference_number=export.reference_number,
    timeout=120.0,
)

for path in auth.invoices.fetch_package(
    package=package,
    export=export,
    target_directory="downloads",
):
    print(path)
```

Przy powtarzalnej pracy lokalnej lub produkcyjnej utwórz profil kompatybilny z
CLI i użyj tego samego profilu z Pythona:

```python
from ksef2 import Client, Environment

client = Client(Environment.PRODUCTION)
auth = client.authentication.with_profile("prod-token")
```

## Wersja async

```python
import asyncio
from pathlib import Path

from ksef2 import AsyncClient, Environment, FormSchema


async def main() -> None:
    async with AsyncClient(Environment.TEST) as client:
        auth = await client.authentication.with_test_certificate(nip="5261040828")

        async with auth.online_session(form_code=FormSchema.FA3) as session:
            status = await session.send_invoice_and_wait(
                invoice_xml=Path("invoice.xml").read_bytes(),
                timeout=60.0,
            )
            print(status.ksef_number)


asyncio.run(main())
```

## Co dalej

- [Konfiguracja klienta](../workflows/client-setup.mdx)
- [Uwierzytelnianie](../workflows/authentication.mdx)
- [Wysyłanie faktur](../workflows/sending-invoices.mdx)
- [Pobieranie faktur](../workflows/downloading-invoices.mdx)
- [Referencja API](../reference/api-signatures.md)
