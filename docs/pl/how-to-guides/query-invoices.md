---
title: Wyszukaj faktury
description: Wyszukuj metadane faktur przez filtry, paginację i polling ksef2.
---

Użyj `auth.invoices`, gdy potrzebujesz metadanych faktur poza sesją wysyłki.
Przykłady poniżej zakładają, że masz już uwierzytelnionego klienta `auth`.

## Zbuduj wąski filtr

Zacznij od pytania biznesowego: jaka rola, jakie pole daty i jaki przedział
czasu mają zostać przeszukane przez KSeF?

```python
from datetime import datetime, timedelta, timezone

from ksef2.models import InvoicesFilter

now = datetime.now(tz=timezone.utc)

filters = InvoicesFilter.for_seller(
    date_from=now - timedelta(days=7),
    date_to=now,
    invoice_types=["vat"],
    invoicing_mode="online",
)
```

`InvoicesFilter` normalizuje każdą przyjętą datę do UTC przed porównaniem i
mapowaniem requestu. Wartości z jawnym offsetem zachowują swój moment. Wartości
bez strefy są interpretowane jako czas lokalny Europe/Warsaw; niejednoznaczne
albo nieistniejące godziny zmiany czasu muszą zawierać jawny offset.

:::tip[Do synchronizacji użyj dat trwałego zapisu]
`issue_date` jest zwykle właściwe dla okresów księgowych. Dla automatycznej
synchronizacji przyrostowej użyj `date_type="permanent_storage"` oraz
`restrict_to_permanent_storage_hwm_date=True`.
:::

## Pobierz jedną stronę

`auth.invoices.search()` zwraca leniwy obiekt `Pager`; nic nie jest pobierane,
dopóki go nie użyjesz. Wywołaj `first_page()`, gdy potrzebujesz jednej strony
dla ekranu, uzgodnienia albo diagnostyki.

```python
from ksef2.models import InvoiceMetadataParams

pager = auth.invoices.search(
    filters,
    InvoiceMetadataParams(page_size=25, sort_order="asc"),
)

for invoice in pager.first_page():
    print(invoice.ksef_number, invoice.invoice_number)
```

## Przejdź po wynikach

Iteruj po pagerze, by dostać wiersze faktur, albo wywołaj `pages()`, gdy ważna
jest każda strona. Pager sam obsługuje granice stron i obcięcia w KSeF.

### Strony

```python
params = InvoiceMetadataParams(page_size=100, sort_order="asc")

for page in auth.invoices.search(filters, params).pages():
    print(f"page={len(page)}")

    for invoice in page:
        print(invoice.ksef_number, invoice.permanent_storage_date)
```

### Faktury

```python
params = InvoiceMetadataParams(page_size=100, sort_order="asc")

for invoice in auth.invoices.search(filters, params):
    print(invoice.ksef_number, invoice.invoice_number)
```

## Znajdź konkretną fakturę

Jeśli znasz własny numer faktury, dodaj go do filtra. Jeśli masz już numer KSeF,
preferuj filtrowanie po `ksef_number` albo bezpośrednie pobranie faktury.

```python
filters = InvoicesFilter.for_seller(
    date_from=now - timedelta(days=30),
    date_to=now,
    invoice_number="FV/42/2026",
)

page = auth.invoices.search(filters).first_page()
```

```python
filters = InvoicesFilter.for_seller(
    date_type="permanent_storage",
    date_from=now - timedelta(days=30),
    date_to=now,
    ksef_number="1234567890-20260625-...",
)

page = auth.invoices.search(filters).first_page()
```

## Poczekaj po wysyłce

Przetwarzanie w KSeF jest asynchroniczne. Jeśli przepływ wysyła fakturę i od
razu potrzebuje jej widoczności w API pobierania, odpytuj wąskim filtrem.

```python
filters = InvoicesFilter.for_seller(
    date_from=now - timedelta(days=1),
    date_to=now,
    invoice_number="FV/42/2026",
)

pager = auth.invoices.search(filters).wait(timeout=120.0, poll_interval=2.0)

for invoice in pager:
    print(invoice.ksef_number, invoice.invoice_number)
```

:::caution[Odpytywanie czeka na dowolne dopasowanie]
`wait()` zwraca wynik, gdy co najmniej jeden wiersz pasuje do filtra. Utrzymaj
filtr na tyle konkretny, żeby pierwsze dopasowanie było fakturą, na którą
czekasz. Jeśli nic nie pojawi się na czas, rzuca `KSeFInvoiceQueryTimeoutError`.
:::

## Zalecany przepływ

1. Wybierz rolę podmiotu, jako który wyszukujesz.

2. Wybierz pole daty pasujące do zadania: widok księgowy, widok przetwarzania
   albo synchronizacja przyrostowa.

3. Zbuduj wąski `InvoicesFilter`.

4. Pobierz jedną stronę dla pracy interaktywnej albo użyj iteratorów dla zadań w
   tle.

5. Zapisz wartości `ksef_number` do późniejszego bezpośredniego pobierania albo
   uzgodnienia eksportów.

## Następne przepływy

- [Pobierz faktury](download-invoices.md): Pobierz XML faktury bezpośrednio albo przez szyfrowaną paczkę eksportu.
- [Wyślij faktury](send-invoices.md): Wyślij XML faktury przez sesję online albo wsadową przed wyszukiwaniem wyniku.
- [Zapytania i eksporty](../concepts/querying-and-exports.md): Zrozum metadane, bezpośrednie pobieranie, paczki eksportu i synchronizację HWM.
