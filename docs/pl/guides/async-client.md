---
title: Klient async
description: Używanie AsyncClient w aplikacjach z pętlą zdarzeń.
---

Użyj `AsyncClient`, gdy aplikacja działa już w pętli zdarzeń, na przykład w
FastAPI, aiohttp, workerach lub asynchronicznych narzędziach CLI.

```python
from ksef2 import AsyncClient, Environment


async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
    print(auth.access_token)
```

## Najważniejsze różnice

- Metody wykonujące żądania sieciowe są `await`.
- Sesje online i testdata działają z `async with`.
- Nazwy punktów wejścia są takie same jak w kliencie sync: `authentication`,
  `invoices`, `tokens`, `permissions`, `sessions`, `invoice_sessions`,
  `certificates`, `limits`, `batch`.

## Sesja online

```python
from pathlib import Path
from ksef2 import FormSchema

async with auth.online_session(form_code=FormSchema.FA3) as session:
    result = await session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    status = await session.wait_for_invoice_ready(
        invoice_reference_number=result.reference_number,
        timeout=60.0,
    )
    print(status.ksef_number)
```

## Paginacja async

```python
async for page in auth.tokens.list_all():
    for token in page.tokens:
        print(token.reference_number)
```

## Powiązane

- [Faktury](invoices.md)
- [Sesje](sessions.md)
- [Uwierzytelnianie](authentication.md)
