---
title: Obsługa błędów
description: Łap wyjątki SDK, sprawdzaj odpowiedzi KSeF i obsługuj timeouty pollingu.
---

Używaj wyjątków SDK dla błędów zwróconych przez KSeF oraz błędów, które SDK
potrafi sklasyfikować. `httpx.HTTPError` łap osobno dla problemów transportu,
gdy SDK nie sparsowało odpowiedzi KSeF.

## Łap błędy SDK i transportu osobno

```python
import httpx

from ksef2 import KSeFApiError, KSeFException

try:
    result = auth.invoices.query_metadata(filters=filters)
except KSeFApiError as exc:
    print(exc.status_code)
    print(exc.exception_code)
except KSeFException as exc:
    print(exc.context)
except httpx.HTTPError as exc:
    print(f"Network or transport failure: {exc}")
```

Łap konkretne wyjątki SDK przed `KSeFException`. `KSeFException` jest klasą
bazową dla błędów sklasyfikowanych przez SDK: odpowiedzi API, walidacji,
szyfrowania, cyklu życia sesji i timeoutów pollingu.

## Sprawdzaj szczegóły odpowiedzi API

`KSeFApiError` jest rzucany dla odpowiedzi KSeF 4xx i 5xx. Udostępnia:

- `status_code`: kod HTTP zwrócony przez KSeF;
- `exception_code`: znormalizowany `ExceptionCode`, jeśli KSeF zwrócił znany
  kod wyjątku;
- `response`: sparsowany model błędu KSeF, jeśli body dało się sparsować.

```python
from ksef2 import ExceptionCode, KSeFApiError

try:
    xml = auth.invoices.download_invoice(ksef_number=ksef_number)
except KSeFApiError as exc:
    if exc.exception_code is ExceptionCode.NOT_PROCESSED_YET:
        print("KSeF zna fakturę, ale nie jest jeszcze gotowa.")
    if exc.response is not None:
        print(exc.response.model_dump_json(indent=2))
```

Sparsowany model `response` zachowuje kształt payloadu KSeF. Używaj
`model_dump()` albo `model_dump_json()` do logowania strukturalnych diagnostyk.

## Obsługuj limity

Odpowiedzi KSeF `429` rzucają `KSeFRateLimitError`. Jeśli KSeF wyśle nagłówek
`Retry-After`, SDK udostępni go jako `retry_after`.

```python
from time import sleep

from ksef2 import KSeFRateLimitError

try:
    page = auth.invoices.query_metadata(filters=filters)
except KSeFRateLimitError as exc:
    delay = exc.retry_after if exc.retry_after is not None else 5
    sleep(delay)
```

W workerach tła połącz `retry_after` z polityką kolejki albo retry zamiast
usypiać request handler.

## Obsługuj timeouty pollingu

Operacje, które odpytują KSeF, rzucają wyjątki timeout SDK po przekroczeniu
parametru `timeout`. To nie są timeouty HTTP. Oznaczają, że SDK odpytywało KSeF,
ale KSeF nie osiągnął oczekiwanego stanu w czasie.

| Operacja | Wyjątek timeout |
| --- | --- |
| Polling uwierzytelniania | `KSeFAuthPollingTimeoutError` |
| Polling aktywacji tokenu | `KSeFTokenStatusTimeoutError` |
| Przetwarzanie faktury online | `KSeFInvoiceProcessingTimeoutError` |
| Widoczność metadanych faktur | `KSeFInvoiceQueryTimeoutError` |
| Gotowość pobrania faktury | `KSeFInvoiceDownloadTimeoutError` |
| Gotowość paczki eksportu | `KSeFExportTimeoutError` |
| Zakończenie sesji batch | `KSeFBatchSessionTimeoutError` |

Większość wyjątków timeout zawiera właściwy numer referencyjny oraz `timeout`.

```python
from ksef2 import KSeFInvoiceProcessingTimeoutError

try:
    status = session.wait_for_invoice_ready(
        invoice_reference_number=reference_number,
        timeout=60.0,
    )
except KSeFInvoiceProcessingTimeoutError as exc:
    print(exc.invoice_reference_number)
    print(exc.timeout)
```

Zapisuj referencje sesji i faktur przed pollingiem. Kolejny worker może wznowić
sprawdzanie statusu, nawet jeśli pierwszy proces przekroczy timeout.

## Ponawiaj `NOT_PROCESSED_YET`

Część niższopoziomowych wywołań KSeF może zwrócić
`ExceptionCode.NOT_PROCESSED_YET`, gdy zasób istnieje, ale nie jest jeszcze
gotowy. Wysokopoziomowe helpery wait obsługują to tam, gdzie jest to część
workflow, na przykład `wait_for_invoice_download()`.

```python
xml = auth.invoices.wait_for_invoice_download(
    ksef_number=ksef_number,
    timeout=120.0,
    poll_interval=2.0,
)
```

Jeśli wywołujesz niższe poziomy bezpośrednio, traktuj `NOT_PROCESSED_YET` jako
stan ponawialny tylko dla operacji, w których KSeF dokumentuje asynchroniczną
dostępność. Nie ponawiaj błędów walidacji albo autoryzacji jak opóźnień
przetwarzania.

## Zalecany przepływ

1. Łap najwęższy wyjątek SDK, na który workflow potrafi zareagować.
2. Używaj `KSeFApiError.response` do strukturalnych diagnostyk.
3. Używaj `KSeFRateLimitError.retry_after` do planowania ponowień.
4. Traktuj timeouty pollingu SDK jako wznawialny stan workflow, nie utracone
   zadanie.
5. Łap `httpx.HTTPError` osobno dla błędów sieci, TLS, DNS i połączenia.

## Referencja

- [Klient](client.md)
- [Status i UPO](../workflows/status-upo.mdx)
- [Errors reference](../reference/api/errors.md)
