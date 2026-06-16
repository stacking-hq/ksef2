---
title: Quickstart
description: Pierwszy przepływ KSeF2 w wersji sync i async.
---

Przykład używa środowiska TEST. Dla DEMO lub PRODUKCJI użyj certyfikatu
wystawionego przez MCU.

## Wybierz tryb klienta

Klienta sync używaj w zwykłych skryptach i narzędziach CLI. Klienta async używaj
w aplikacjach, które już zarządzają pętlą zdarzeń.

### Sync


```python
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter

NIP = "5261040828"

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip=NIP)

with auth.online_session(form_code=FormSchema.FA3) as session:
    result = session.send_invoice(invoice_xml=Path("invoice.xml").read_bytes())
    status = session.wait_for_invoice_ready(
        invoice_reference_number=result.reference_number,
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
```

### Async


```python
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import AsyncClient, Environment, FormSchema
from ksef2.domain.models import InvoicesFilter

NIP = "5261040828"


async def main() -> None:
    async with AsyncClient(Environment.TEST) as client:
        auth = await client.authentication.with_test_certificate(nip=NIP)

        async with auth.online_session(form_code=FormSchema.FA3) as session:
            result = await session.send_invoice(
                invoice_xml=Path("invoice.xml").read_bytes()
            )
            status = await session.wait_for_invoice_ready(
                invoice_reference_number=result.reference_number,
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
        export = await auth.invoices.schedule_export(filters=filters)
        package = await auth.invoices.wait_for_export_package(
            reference_number=export.reference_number,
            timeout=120.0,
        )
        print(package.reference_number)


asyncio.run(main())
```


## Co się wydarzyło

1. Klient wybrał środowisko TEST.
2. `with_test_certificate()` utworzyło testowy certyfikat XAdES.
3. `online_session()` otworzyło sesję z materiałem szyfrującym.
4. Metody `wait_for_*` użyły `timeout` w sekundach oraz `poll_interval`.

## Powiązane strony

- [Uwierzytelnianie](authentication.md)
- [Faktury](../guides/invoices.md)
- [Klient async](../guides/async-client.md)
