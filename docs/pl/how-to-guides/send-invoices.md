---
title: Wyślij faktury
description: Wyślij XML FA(3) przez sesje online albo sesje wsadowe ksef2.
---

Użyj `auth.online_session(...)` do interaktywnej wysyłki i `auth.batch` dla
większych zestawów plików. Przykłady poniżej zakładają, że masz już
uwierzytelnionego klienta `auth`.

## Zacznij od bajtów XML

API wysyłki przyjmują bajty XML faktury. Te bajty mogą pochodzić z ERP, pliku
albo buildera FA(3) z SDK.

### Z pliku

```python
from pathlib import Path

invoice_xml = Path("invoice.xml").read_bytes()
```

### Z buildera

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import FA3InvoiceBuilder, VatRate

invoice_xml = (
    FA3InvoiceBuilder()
    .header(system_info="ksef2 send guide")
    .seller(
        name="Demo Seller Sp. z o.o.",
        tax_id="5261040828",
        country_code="PL",
        address_line_1="Prosta 1",
        address_line_2="00-001 Warszawa",
    )
    .buyer(
        name="Demo Buyer Sp. z o.o.",
        country_code="PL",
        address_line_1="Kwiatowa 2",
        address_line_2="00-002 Warszawa",
    )
    .standard()
        .issue_date(date.today())
        .issue_place("Warszawa")
        .invoice_number("FV/42/2026")
        .rows()
            .add_line(
                name="Usługa konsultingowa",
                quantity=Decimal("1"),
                unit_price_net=Decimal("100.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
    .done()
    .to_xml()
    .encode("utf-8")
)
```

## Wyślij w sesji online

Sesji online użyj, gdy wysyłasz jedną fakturę albo mały interaktywny zestaw.
Context manager zamyka zdalną sesję online po wyjściu z bloku.

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    submission = session.send_invoice(invoice_xml)

    # InvoiceSubmission handle
    # submission.reference_number == "20260625-ABCD-EF1234567890"

    status = submission.wait(timeout=120.0, poll_interval=2.0)

    # SessionInvoiceStatusResponse
    # {
    #   "reference_number": "20260625-ABCD-EF1234567890",
    #   "ksef_number": "1234567890-20260625-...",
    #   "invoice_number": "FV/42/2026",
    #   "status": {
    #     "code": 200,
    #     "description": "Processed"
    #   }
    # }
```

`send_invoice()` oznacza tylko, że KSeF przyjął zaszyfrowany payload do sesji.
`submission.wait()` czeka na wynik konkretnej faktury i zwraca numer KSeF
po udanym przetworzeniu. Działa też po zamknięciu sesji, a `session.wait()`
zwraca końcowy status zamkniętej sesji.

:::tip[Dla prostych skryptów połącz wywołania]
`session.send_invoice(invoice_xml).wait()` wykonuje wysyłkę i polling, gdy nie
potrzebujesz osobno uchwytu.
:::

## Zachowaj uchwyty sesji

Zapisz uchwyty przed długim pollingiem albo przed przekazaniem pracy innemu
procesowi.

```python
with auth.online_session(form_code=FormSchema.FA3) as session:
    session_state_json = session.resume_state().to_json()
    submission = session.send_invoice(invoice_xml)
    invoice_reference_number = submission.reference_number

# Zapisz session_state_json i invoice_reference_number w bezpiecznym magazynie.
# Nie loguj session_state_json, bo zawiera dane szyfrowania sesji.
```

## Wyślij batch

Batcha użyj, gdy chcesz wysłać wiele plików XML jako jeden przepływ KSeF.
Serwis wysokiego poziomu przygotowuje paczkę ZIP, szyfruje części, otwiera
sesję batch, wysyła części, zamyka sesję i zwraca zamkniętego klienta `BatchSessionClient`. Wywołaj potem
jego `wait()`, `list_failed_invoices()` i `download_upo()`. `auth.batch.prepare()`
i `submit()` przyjmują elementy `bytes`, `str`, `Path` lub `BatchInvoice`.

### Z plików

```python
from pathlib import Path

from ksef2 import FormSchema

prepared = auth.batch.prepare(
    [Path("invoice-1.xml"), Path("invoice-2.xml")],
    form_code=FormSchema.FA3,
)

session = auth.batch.submit(prepared)

# session.reference_number == "20260625-BATCH-..."
```

### Z bajtów

```python
from pathlib import Path

from ksef2 import FormSchema
from ksef2.models import BatchInvoice

session = auth.batch.submit(
    [
        BatchInvoice(
            file_name="invoice-1.xml",
            content=Path("invoice-1.xml").read_bytes(),
        ),
        BatchInvoice(
            file_name="invoice-2.xml",
            content=Path("invoice-2.xml").read_bytes(),
        ),
    ],
    form_code=FormSchema.FA3,
)

# session.reference_number == "20260625-BATCH-..."
```

## Poczekaj na zakończenie batcha

Po wysłaniu batcha polluj sesję batch i sprawdź faktury przyjęte oraz odrzucone.

```python
final_status = session.wait(timeout=300.0, poll_interval=2.0)

# SessionStatusResponse
# {
#   "status": {
#     "code": 200,
#     "description": "Processed"
#   },
#   "invoice_count": 2,
#   "successful_invoice_count": 2,
#   "failed_invoice_count": 0,
#   "upo": {
#     "pages": [
#       {
#         "reference_number": "upo-page-reference"
#       }
#     ]
#   }
# }

accepted = session.list_invoices(page_size=100)
failed = session.list_failed_invoices(page_size=100)
```

:::caution[Sukces batcha nadal wymaga sprawdzenia]
Status batcha podsumowuje sesję. Sprawdź strony faktur przyjętych i odrzuconych,
zanim uznasz, że każda faktura z paczki osiągnęła oczekiwany wynik biznesowy.
:::

## Zalecany przepływ

1. Uwierzytelnij się w kontekście sprzedawcy.

2. Wczytaj XML faktury z własnego systemu albo zbuduj go przez
   `FA3InvoiceBuilder`.

3. Użyj sesji online dla małej interaktywnej wysyłki albo `auth.batch` dla
   większych zestawów.

4. Zapisz zwrócone referencje sesji i faktur przed pollingiem.

5. Odpytuj status, zapisz wyniki przyjęte i odrzucone, a potem pobierz UPO albo
   XML faktury z kolejnych stron.

## Następne przepływy

- [Sprawdź status i UPO](get-status-and-upo.md): Polluj sesje online i batch, sprawdzaj wyniki i pobieraj XML UPO.
- [Zbuduj faktury FA(3)](build-fa3-invoices.md): Wygeneruj poprawny XML FA(3), gdy aplikacja jeszcze go nie ma.
- [Wyszukaj faktury](query-invoices.md): Znajdź przetworzone faktury filtrami metadanych i paginacją.
- [Pobierz faktury](download-invoices.md): Pobierz przetworzony XML faktury po nadaniu numeru KSeF.
