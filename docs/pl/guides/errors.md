---
title: Błędy
description: Klasy wyjątków, timeouty i obsługa błędów API.
---

Stabilne wyjątki importuj z `ksef2`.

```python
from ksef2 import KSeFApiError, KSeFTokenStatusTimeoutError
```

## Błędy API

`KSeFApiError` reprezentuje odpowiedź HTTP z błędem KSeF.

```python
try:
    auth.invoices.download_invoice(ksef_number="...")
except KSeFApiError as exc:
    print(exc.status_code, exc.exception_code, exc.message)
```

## Timeouty pollingu

Timeouty pollingu nie są odpowiedziami HTTP i nie mają `status_code`.

```python
try:
    token = auth.tokens.generate(
        permissions=["invoice_read"],
        description="Reporting",
        timeout=10.0,
    )
except KSeFTokenStatusTimeoutError as exc:
    print(exc.reference_number, exc.timeout)
```

W publicznym API używaj `timeout` w sekundach oraz `poll_interval`.
