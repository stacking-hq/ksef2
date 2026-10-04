---
title: Wyszukiwanie i eksport paczek
description: Metadane faktur, pobieranie pojedynczych dokumentów, eksporty paczek i synchronizacja przyrostowa.
---

Pobieranie faktur w KSeF to trzy różne zadania:

- metadane odpowiadają na pytanie „jakie faktury pasują do filtra?”;
- pobieranie pojedyncze zwraca przetworzony XML dla podanego numeru KSeF;
- eksport przygotowuje paczkę do pobrania dla większego zestawu faktur.

KSeF najlepiej traktować jako system wymiany i źródło oficjalnych zapisów
faktur, a nie jako bazę danych pod każdym ekranem aplikacji. W większości
integracji stabilny wzorzec to odpytać albo wyeksportować dane z KSeF, zapisać
wynik lokalnie i zasilać widoki operacyjne z własnego magazynu.

## Metadane znajdują faktury

`auth.invoices.search()` zwraca `Pager` po wierszach `InvoiceMetadata`, a nie po
XML faktury. Iteruj go albo użyj `pages()`, `first_page()` i `wait()`.

Metadane są przydatne do list, uzgodnień, pollingu po wysyłce i decyzji, co
pobrać później. Wiersz metadanych może zawierać identyfikatory, daty, dane
stron, kwoty, pola schematu, hashe, flagi załączników i tryb fakturowania.

Filtr opisuje widok, który KSeF ma przeszukać:

- `role`, na przykład `seller` albo `buyer`;
- `date_type`, `date_from` i `date_to`;
- opcjonalne `amount_min` i `amount_max` oraz `amount_type`, gdy używasz zakresu kwot;
- identyfikatory takie jak `seller_nip`, `buyer_nip`, `invoice_number` albo `ksef_number`;
- opcjonalne dane faktury, takie jak `invoice_types`, `invoice_schema`, `has_attachment` i `invoicing_mode`.

:::tip[Typ kwoty należy do zakresu kwot]
Ustaw `amount_type` tylko wtedy, gdy używasz `amount_min` albo `amount_max`.
SDK waliduje, że filtry zakresu wskazują pole kwoty KSeF, którego dotyczą.
:::

## Bezpośrednie pobieranie zwraca jeden XML

`auth.invoices.download()` pobiera jeden przetworzony dokument XML po
`ksef_number`.

Ta ścieżka jest celowo wąska. Użyj jej, gdy masz już numer KSeF z wyniku sesji,
zapytania o metadane, przepływu UPO albo własnej bazy. Jeśli faktura została
właśnie zaakceptowana, ale KSeF jeszcze nie udostępnił XML-a,
`auth.invoices.download(ksef_number, timeout=...)` polluje do gotowości
dokumentu albo do lokalnego timeoutu.

## Eksporty tworzą szyfrowane paczki

Eksport jest asynchroniczny. `auth.invoices.export()` przyjmuje ten sam kształt
`InvoicesFilter`, którego używają zapytania o metadane, i zwraca `ExportJob`.
Jego `wait()` odpytuje KSeF, aż paczka będzie gotowa, pobiera i odszyfrowuje
części, łączy je i zwraca obiekt `ExportedInvoices`.

```text
InvoicesFilter
  -> auth.invoices.export()
    -> ExportJob
      -> job.wait()
        -> ExportedInvoices: invoices(), metadata, archive, save()
```

:::caution[Traktuj uchwyty eksportu jak dane wrażliwe]
`ExportJob` trzyma lokalny materiał klucza AES potrzebny do odszyfrowania
paczki. Aby przetrwać restart, zapisz `job.resume_state().to_json()` jak
poświadczenie i przekaż do `auth.invoices.export(state=...)`; nigdy go nie loguj.
:::

## HWM jest granicą synchronizacji

Dla automatycznej synchronizacji kluczowym pojęciem jest HWM: High Water Mark.
Gdy KSeF zwraca `permanent_storage_hwm_date`, informuje, że dane faktur w
trwałym zapisie są kompletne do tej granicy.

Niezawodny kształt synchronizacji wygląda tak:

```text
ostatni zapisany permanent_storage_date
  -> query/export z restrict_to_permanent_storage_hwm_date=True
    -> lokalny zapis metadanych i treści faktur
      -> zapis permanent_storage_hwm_date jako początku następnego okna
```

Użyj `date_type="permanent_storage"`, gdy celem jest synchronizacja
przyrostowa. Użyj `restrict_to_permanent_storage_hwm_date=True`, żeby KSeF
ograniczył wynik do bezpiecznej, zakończonej granicy.

```python
from ksef2.models import InvoicesFilter

filters = InvoicesFilter.for_buyer(
    date_type="permanent_storage",
    date_from=last_synced_at,
    restrict_to_permanent_storage_hwm_date=True,
)

page = auth.invoices.search(filters).first_page()

# QueryInvoicesMetadataResponse
# {
#   "has_more": false,
#   "is_truncated": false,
#   "permanent_storage_hwm_date": "2026-06-25T10:00:00Z",
#   "invoices": [
#     {
#       "ksef_number": "1234567890-20260625-...",
#       "invoice_number": "FV/42/2026",
#       "permanent_storage_date": "2026-06-25T09:58:21Z"
#     }
#   ]
# }
```

Jeśli strona metadanych albo paczka eksportu jest ucięta, kontynuuj od
zwróconej ostatniej daty, na przykład `last_permanent_storage_date`, zamiast
zakładać, że pokryto cały żądany koniec okna. Przy nakładających się oknach
deduplikuj zapisane rekordy po `ksef_number`.

Paczki eksportu mogą też zawierać `_metadata.json`, co pomaga uzgodnić pobraną
zawartość XML z wierszami metadanych przechowywanymi lokalnie.

## Powiązane strony

- [Wyszukaj faktury](../how-to-guides/query-invoices.md): Szukaj metadanych faktur filtrami, paginacją i pollingiem.
- [Pobierz faktury](../how-to-guides/download-invoices.md): Pobierz jeden dokument XML albo większą paczkę eksportu.
- [Cykl życia faktury](invoice-lifecycle.md): Zobacz, jak łączą się wysyłka, przetwarzanie, zapis i pobieranie faktur.
- [Szyfrowanie](encryption.md): Zrozum, jak publiczne certyfikaty KSeF chronią klucze sesji i eksportów.
