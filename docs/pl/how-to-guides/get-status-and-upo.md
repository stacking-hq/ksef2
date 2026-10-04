---
title: Sprawdź status i UPO
description: Sprawdzaj status sesji online i batch, listuj faktury sesji i pobieraj dokumenty UPO.
---

Użyj tej strony po wysłaniu XML faktury. Przykłady zakładają, że masz już
uwierzytelnionego klienta `auth`.

Wywołania statusu zwracają modele SDK. Wywołania UPO zwracają bajty XML.

## Status faktury online

Przy wysyłce online `send_invoice()` zwraca referencję faktury w sesji. Użyj tej
referencji do pollingu wyniku faktury i pobrania UPO faktury.

```python
from pathlib import Path

from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    submission = session.send_invoice(invoice_xml)

    invoice_status = submission.wait(timeout=120.0, poll_interval=2.0)

    # SessionInvoiceStatusResponse
    # {
    #   "ordinal_number": 1,
    #   "reference_number": "20260625-ABCD-EF1234567890",
    #   "invoice_number": "FV/42/2026",
    #   "ksef_number": "1234567890-20260625-...",
    #   "status": {
    #     "code": 200,
    #     "description": "Processed"
    #   }
    # }

    upo_xml = submission.download_upo()
    Path("upo.xml").write_bytes(upo_xml)
```

`download_upo()` samo czeka na przetworzenie, więc wywołanie tuż po
`send_invoice()` też działa. Przekaż `timeout` i `poll_interval`, aby sterować
czasem oczekiwania.

W tym samym bloku sesji, jeśli masz już numer KSeF, możesz pobrać UPO faktury
po numerze KSeF:

```python
ksef_number = invoice_status.ksef_number
if ksef_number is None:
    raise RuntimeError("KSeF did not assign an invoice number.")

upo_xml = session.download_invoice_upo(ksef_number=ksef_number)
```

:::caution[Zachowaj referencję faktury]
Referencja faktury jest trwałym uchwytem do pollingu jednej faktury w sesji.
Zapisz ją przed czekaniem, żeby inny worker mógł sprawdzić wynik, jeśli
pierwotny proces się zatrzyma.
:::

## Strony sesji online

Użyj stron sesji, gdy chcesz sprawdzić wszystko, co wysłano w sesji online, a
nie jedną referencję faktury.

### Przyjęte

```python
page = session.list_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.reference_number, invoice.ksef_number)
```

### Odrzucone

```python
page = session.list_failed_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.reference_number, invoice.status.code, invoice.status.details)
```

## Status batch i UPO

Przy wysyłce batch zachowaj zwrócony `BatchSessionResumeState`. Serwis batch może
pollować po stanie albo po samym numerze referencyjnym sesji.

```python
from pathlib import Path

final_status = session.wait(timeout=300.0, poll_interval=2.0)

# SessionStatusResponse
# {
#   "status": {
#     "code": 200,
#     "description": "Processed"
#   },
#   "invoice_count": 10,
#   "successful_invoice_count": 9,
#   "failed_invoice_count": 1,
#   "upo": {
#     "pages": [
#       {
#         "reference_number": "upo-page-reference",
#         "download_url_expiration_date": "2026-06-26T10:00:00Z"
#       }
#     ]
#   }
# }

for number, upo_xml in enumerate(session.download_upo(), start=1):
    Path(f"batch-upo-{number}.xml").write_bytes(upo_xml)
```

:::note[UPO jest artefaktem audytowym]
Zapisuj XML UPO trwale. To oficjalny dokument potwierdzenia, a nie tylko
tymczasowa odpowiedź statusu.
:::

## Listuj faktury przyjęte i odrzucone w batchu

Faktury przyjęte i odrzucone są na osobnych stronach. Przeczytaj oba zestawy
przy uzgadnianiu batcha.

### Przyjęte

```python
page = session.list_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.invoice_file_name, invoice.ksef_number, invoice.status.description)
```

### Odrzucone

```python
page = session.list_failed_invoices(page_size=100)

for invoice in page.invoices:
    print(invoice.invoice_file_name, invoice.status.code, invoice.status.details)
```

Gdy strona ma `continuation_token`, przekaż go do następnego wywołania:

```python
page = session.list_invoices(page_size=100)

while page.continuation_token is not None:
    page = session.list_invoices(
        page_size=100,
        continuation_token=page.continuation_token,
    )
```

## Znajdź sesje po restarcie

Użyj `auth.invoice_sessions`, gdy musisz znaleźć sesje online albo batch po
zakończeniu pierwotnego procesu wysyłki.

`list()` zwraca `Pager`: iteruj po nim, by dostać każdą sesję, wywołaj
`.pages()` dla list wielkości strony albo `.first_page()`, by wykonać jedno
żądanie.

### Jedna strona

```python
sessions = auth.invoice_sessions.list(
    "online",
    statuses=["in_progress", "succeeded"],
).first_page()

for item in sessions:
    print(item.reference_number, item.status.code, item.total_invoice_count)
```

### Wszystkie sesje

```python
for item in auth.invoice_sessions.list("batch"):
    print(item.reference_number, item.status.description)
```

## Zalecany przepływ

1. Zapisz referencje sesji i faktur podczas wysyłki.

2. Polluj konkretną fakturę, sesję online albo sesję batch zgodnie z pytaniem,
   na które odpowiadasz.

3. Zapisz szczegóły faktur przyjętych i odrzuconych.

4. Pobierz XML UPO i zapisz go razem z danymi audytowymi.

5. Użyj `auth.invoice_sessions`, żeby odzyskać referencje sesji po restarcie
   procesu.

## Następne przepływy

- [Wyślij faktury](send-invoices.md): Wyślij XML faktury przez sesję online albo batch przed pollingiem statusu.
- [Status i UPO](../concepts/status-and-upo.md): Zrozum powierzchnie statusu, dokumenty UPO, polling i lokalne timeouty.
- [Pobierz faktury](download-invoices.md): Pobierz przetworzony XML faktury po nadaniu numeru KSeF.
- [Wyszukaj faktury](query-invoices.md): Znajdź przetworzone faktury filtrami metadanych i paginacją.
