---
title: Szybki start
description: Wygeneruj fakturę TEST, wyślij ją do KSeF, pobierz UPO i sprawdź zwrócony XML.
---

Ten przykład przeprowadza jedną fakturę TEST przez pełny scenariusz w SDK:
zbudowanie faktury FA(3), uwierzytelnienie certyfikatem TEST, wysłanie faktury
w sesji online, pobranie UPO oraz przetworzonego XML faktury z KSeF.

## Instalacja

Wybierz preferowaną metodę instalacji:

### Instalacja przez pip

```bash
pip install ksef2
```

### Instalacja przez uv

```bash
uv add ksef2
```

ksef2 wymaga Pythona 3.12 lub nowszego.

## Przykład kodu

Skopiuj poniższy kod do pliku `quickstart.py`.

```python title="quickstart.py"
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.fa3 import FA3InvoiceBuilder, VatRate

SELLER_NIP = "5261040828"
DOWNLOADS = Path("downloads")

invoice_number = f"QS/{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
invoice_xml = (
    FA3InvoiceBuilder()
    .header(system_info="ksef2 quickstart")
    .seller(
        name="Demo Seller Sp. z o.o.",
        tax_id=SELLER_NIP,
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
        .invoice_number(invoice_number)
        .rows()
            .add_line(
                name="Consulting service",
                quantity=Decimal("1"),
                unit_price_net=Decimal("100.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
    .done()
    .to_xml()
    .encode("utf-8")
)

DOWNLOADS.mkdir(exist_ok=True)
(DOWNLOADS / "generated-invoice.xml").write_bytes(invoice_xml)

with Client(Environment.TEST) as client:
    auth = client.authentication.with_test_certificate(nip=SELLER_NIP)

    with auth.online_session(form_code=FormSchema.FA3) as session:
        submission = session.send_invoice(invoice_xml)
        print(f"Sent invoice: {submission.reference_number}")

        status = submission.wait(timeout=120.0)
        print("Invoice status:")
        print(status.model_dump_json(indent=2))

        upo_xml = submission.download_upo()
        (DOWNLOADS / "upo.xml").write_bytes(upo_xml)
        print("Saved downloads/upo.xml")

    if status.ksef_number is None:
        raise RuntimeError("KSeF did not assign an invoice number.")

    downloaded_xml = auth.invoices.download(status.ksef_number, timeout=120.0)
    (DOWNLOADS / "processed-invoice.xml").write_bytes(downloaded_xml)
    print("Saved downloads/processed-invoice.xml")
```

Uruchom skrypt:

```bash
python quickstart.py
# albo
uv run quickstart.py
```

Skrypt zapisze trzy lokalne pliki:

- `downloads/generated-invoice.xml`
- `downloads/upo.xml`
- `downloads/processed-invoice.xml`

Po zakończeniu sprawdź wygenerowany XML, UPO oraz XML zwrócony przez KSeF.
Wygenerowany i przetworzony XML powinny opisywać tę samą fakturę; zachowaj
przetworzony XML jako kopię zwróconą przez KSeF.

:::note[Dlaczego używamy certyfikatu TEST?]
Ten przykład używa `with_test_certificate()`, bo w `Environment.TEST`
wymaga najmniej przygotowania. Tokeny, XAdES i profile są opisane w poradniku
uwierzytelniania.
:::

## Co robi ten przykład

1. `FA3InvoiceBuilder` utworzył minimalny XML FA(3) z nazwami pól SDK, takimi
   jak `invoice_number`, `tax_id` i `unit_price_net`.

2. `Client(Environment.TEST)` wybrał adresy bazowe środowiska TEST KSeF i
   zarządzał zasobami HTTP używanymi przez SDK.

3. `with_test_certificate()` uwierzytelniło kontekst TEST wskazany przez
   `SELLER_NIP`.

4. `online_session(FormSchema.FA3)` otworzyło sesję online do wysłania faktury
   FA(3).

5. `send_invoice()` wysłało fakturę i zwróciło uchwyt `InvoiceSubmission` z
   numerem referencyjnym faktury w sesji.

6. `submission.wait()` cyklicznie sprawdzało status, aż KSeF nadał numer
   faktury.

7. `submission.download_upo()` pobrało XML UPO, a `auth.invoices.download()`
   pobrało przetworzony XML faktury.

## Dostosuj skrypt

Zmień pola faktury albo dodaj kolejne pozycje, gdy dopasowujesz skrypt. Aby
przenieść ten sam kształt do DEMO albo PRODUCTION, zmień główne `Environment` i
użyj credentiala przypisanego do tego środowiska.

Do codziennej pracy lokalnej utwórz profil kompatybilny z CLI i zastąp linię
uwierzytelnienia wywołaniem `client.authentication.with_profile("test-company")`.
Profil musi wskazywać to samo środowisko co klient główny.

## Powiązane strony

- [Konfiguracja klienta](../how-to-guides/client-setup.md): Utwórz klienta synchronicznego albo asynchronicznego i zarządzaj cyklem życia zasobów.
- [Uwierzytelnianie](../how-to-guides/authenticate.md): Uwierzytelnij się tokenem, XAdES, certyfikatem TEST albo profilem.
- [Profile](../how-to-guides/profiles.md): Użyj lokalnego profilu zgodnego z CLI po pierwszym uruchomieniu w środowisku TEST.
- [Zbuduj faktury FA(3)](../how-to-guides/build-fa3-invoices.md): Generuj poprawny XML FA(3) za pomocą fluent buildera.
- [Wysyłanie faktur](../how-to-guides/send-invoices.md): Wysyłaj faktury online albo w trybie batch i śledź stan przetwarzania.
- [Pobieranie faktur](../how-to-guides/download-invoices.md): Pobieraj XML faktury bezpośrednio albo przez pakiety eksportu.
- [Kontrakt publicznego API](../reference/public-api.md): Przejrzyj stabilne publiczne importy dla kodu aplikacyjnego.
