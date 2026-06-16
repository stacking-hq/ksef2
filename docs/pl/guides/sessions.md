---
title: Sesje
description: Sesje online, batch i wznawianie pracy.
---

KSeF wymaga sesji dla wysyłki faktur. SDK przechowuje stan potrzebny do
wznowienia sesji i pobrania statusów.

## Sesja online

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    print(session.reference_number)
    state = session.get_state()
```

Wznowienie:

```python
session = auth.resume_online_session(state)
status = session.get_status()
```

SDK nie waliduje po stronie serwera, czy zapisany `access_token` jest nadal
ważny. Jeżeli token wygasł, uwierzytelnij się ponownie.

Wznowienie odtwarza lokalny obiekt SDK z zapisanego stanu. Nie odświeża tokenu
i nie odpytuje KSeF podczas tworzenia obiektu. Walidacja po stronie serwera
nastąpi dopiero przy następnym wywołaniu API.

## Sesja batch

```python
from ksef2.domain.models.batch import BatchInvoice

prepared = auth.batch.prepare_batch(
    invoices=[BatchInvoice(file_name="invoice.xml", content=b"<Invoice />")]
)
state = auth.batch.submit_prepared_batch(prepared_batch=prepared)
status = auth.batch.wait_for_completion(session=state, timeout=120.0)
```

## Historia sesji

```python
for page in auth.invoice_sessions.all(session_type="online"):
    print(len(page.items))
```
