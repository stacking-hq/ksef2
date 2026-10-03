---
title: Pobierz faktury
description: Pobieraj przetworzony XML faktur bezpośrednio albo przez szyfrowane paczki eksportu ksef2.
---

Użyj `auth.invoices`, gdy potrzebujesz treści faktury po przetworzeniu jej przez
KSeF. Przykłady poniżej zakładają, że masz już uwierzytelnionego klienta
`auth`.

## Pobierz jedną fakturę

Jeśli masz numer KSeF, bezpośrednie pobranie to najkrótsza droga.

```python
from pathlib import Path

ksef_number = "1234567890-20260625-..."

xml_bytes = auth.invoices.download(ksef_number)
Path("invoice.xml").write_bytes(xml_bytes)
```

Jeśli faktura została dopiero wysłana, KSeF może potrzebować czasu, zanim
przetworzony XML będzie dostępny. Podaj `timeout`, a `download()` będzie
odpytywać KSeF, aż dokument będzie dostępny.

```python
xml_bytes = auth.invoices.download(ksef_number, timeout=120.0, poll_interval=2.0)
Path("invoice.xml").write_bytes(xml_bytes)
```

## Zbuduj filtr eksportu

Eksportów używaj do większych pobrań. Eksporty korzystają z `InvoicesFilter`,
czyli tego samego kształtu filtra co zapytania o metadane.

```python
from datetime import datetime, timedelta, timezone

from ksef2.models import InvoicesFilter

now = datetime.now(tz=timezone.utc)

filters = InvoicesFilter.for_buyer(
    date_type="permanent_storage",
    date_from=now - timedelta(days=1),
    date_to=now,
    restrict_to_permanent_storage_hwm_date=True,
)
```

:::tip[Do synchronizacji w tle użyj HWM]
`restrict_to_permanent_storage_hwm_date=True` utrzymuje automatyczne eksporty
w granicy, którą KSeF raportuje jako kompletną. Zapisz
`permanent_storage_hwm_date` dla następnego okna synchronizacji.
:::

## Wyeksportuj wiele faktur

`export()` planuje eksport i zwraca `ExportJob`. Jego `wait()` odpytuje KSeF,
aż paczka będzie gotowa, pobiera i odszyfrowuje części, łączy je i zwraca obiekt
`ExportedInvoices`.

```python
job = auth.invoices.export(filters)
package = job.wait(timeout=300.0)

for ksef_number, xml in package.invoices():
    print(ksef_number, len(xml))

# Sparsowany _metadata.json (lista InvoiceMetadata) albo None, gdy go brak.
metadata = package.metadata

# Szczegóły paczki do synchronizacji przyrostowej.
print(package.package.is_truncated, package.package.permanent_storage_hwm_date)
```

### Zapis do plików

```python
from pathlib import Path

written = package.save(Path("downloads"))
```

`save()` rozpakowuje archiwum i odrzuca każdy wpis, którego ścieżka wychodziłaby
poza katalog docelowy. Surowe bajty ZIP są dostępne jako `package.archive`.

:::note[SDK odszyfrowuje części paczki]
KSeF zwraca zaszyfrowane adresy części paczki. `export()` ładuje poprawny
certyfikat szyfrowania KSeF i planuje eksport z lokalnym materiałem AES, a
`wait()` pobiera części i odszyfrowuje je przed zwróceniem wyniku.
:::

:::caution[Części paczki są tymczasowe]
Adresy paczki wygasają. Zapisz wypakowane XML-e faktur we własnym magazynie i
zachowaj `_metadata.json`, jeśli paczka go zawiera. Gdy KSeF zakończy eksport
błędem albo eksport wygaśnie, `wait()` rzuca `KSeFExportFailedError`.
:::

## Po wysyłce faktur

Trzymaj wysyłkę, przetwarzanie i pobieranie jako osobne fazy.

1. Wyślij XML faktury przez sesję online albo wsadową.

2. Polluj status sesji albo faktury do końcowego zaakceptowanego wyniku.

3. Zapisz zwrócone wartości `ksef_number`.

4. Pobierz jeden przetworzony dokument XML po `ksef_number` albo zbuduj filtr
   eksportu dla większego okna czasu.

## Następne przepływy

- [Wyszukaj faktury](query-invoices.md): Znajdź numery KSeF i metadane przed pobraniem treści faktury.
- [Wyślij faktury](send-invoices.md): Wyślij XML faktury przez sesję online albo wsadową.
- [Zapytania i eksporty](../concepts/querying-and-exports.md): Zrozum metadane, bezpośrednie pobieranie, paczki eksportu i synchronizację HWM.
- [Sprawdź certyfikaty szyfrowania](inspect-encryption-certificates.md): Sprawdź publiczne certyfikaty KSeF używane przez szyfrowane przepływy.
