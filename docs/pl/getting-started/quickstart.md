---
title: Szybki start
description: Wygeneruj fakturę w środowisku testowym, wyślij ją do KSeF, pobierz UPO i sprawdź zwrócony XML.
---

W tym przykładzie przejdziesz cały proces dla jednej faktury w środowisku testowym: zbudujesz fakturę FA(3), uwierzytelnisz się certyfikatem testowym, wyślesz fakturę w sesji interaktywnej, pobierzesz UPO (Urzędowe Poświadczenie Odbioru) oraz XML faktury przetworzonej przez KSeF.

## Instalacja

Wybierz sposób instalacji.

### Instalacja przez pip

```bash
pip install ksef2
```

### Instalacja przez uv

```bash
uv add ksef2
```

ksef2 wymaga Pythona 3.12 lub nowszego.

Aby renderować PDF, zainstaluj opcjonalny dodatek przez `pip install 'ksef2[pdf]'`
lub `uv add 'ksef2[pdf]'`. WeasyPrint wymaga również bibliotek systemowych; zobacz
[poradnik renderowania PDF](../how-to-guides/download-invoices.md).

## Przykład kodu

Skopiuj poniższy kod do pliku `quickstart.py`.

```python title="quickstart.py"
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.fa3 import InvoiceBuilder, VatRate

SELLER_NIP = "5261040828"
DOWNLOADS = Path("downloads")

invoice_number = f"QS/{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
invoice_xml = (
    InvoiceBuilder()
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

Po zakończeniu sprawdź wygenerowany XML, UPO oraz XML zwrócony przez KSeF. Wygenerowany i przetworzony XML powinny opisywać tę samą fakturę. Przetworzony XML zachowaj jako kopię zwróconą przez KSeF.

:::note[Dlaczego używamy certyfikatu TEST?]
Ten przykład używa `with_test_certificate()`, bo w `Environment.TEST` wymaga najmniej przygotowania. Tokeny, XAdES i profile są opisane w poradniku uwierzytelniania.
:::

## Co robi ten przykład

1. `InvoiceBuilder` tworzy minimalny XML FA(3). Nazwy pól, takie jak `invoice_number`, `tax_id` i `unit_price_net`, pochodzą z SDK.

2. `Client(Environment.TEST)` wybiera adresy środowiska testowego KSeF i zarządza połączeniami HTTP używanymi przez SDK.

3. `with_test_certificate()` uwierzytelnia kontekst logowania środowiska testowego wskazany przez `SELLER_NIP`.

4. `online_session(form_code=FormSchema.FA3)` otwiera sesję interaktywną do wysłania faktury FA(3).

5. `send_invoice()` wysyła fakturę i zwraca obiekt `InvoiceSubmission` z numerem referencyjnym faktury w sesji.

6. `submission.wait()` sprawdza status, dopóki KSeF nie nada fakturze numeru KSeF.

7. `submission.download_upo()` pobiera XML UPO, a `auth.invoices.download()` pobiera przetworzony XML faktury.

## Dostosuj skrypt

Zmień pola faktury albo dodaj kolejne pozycje, gdy dopasowujesz skrypt do swojego przypadku. Aby uruchomić skrypt w środowisku przedprodukcyjnym (Demo) lub produkcyjnym, zmień `Environment` i użyj danych uwierzytelniających wydanych dla tego środowiska.

Do codziennej pracy lokalnej utwórz profil zgodny z CLI i zastąp linię uwierzytelnienia wywołaniem `client.authentication.with_profile("test-company")`. Profil musi wskazywać to samo środowisko co klient główny.

## Powiązane strony

- [Konfiguracja klienta](../how-to-guides/client-setup.md): klient synchroniczny albo asynchroniczny i zamykanie zasobów.
- [Uwierzytelnianie](../how-to-guides/authenticate.md): token KSeF, XAdES, certyfikat testowy albo profil.
- [Profile](../how-to-guides/profiles.md): lokalny profil zgodny z CLI po pierwszym uruchomieniu w środowisku testowym.
- [Budowanie faktur FA(3)](../how-to-guides/build-fa3-invoices.md): poprawny XML FA(3) budowany łańcuchem metod.
- [Wysyłanie faktur](../how-to-guides/send-invoices.md): sesja interaktywna albo wsadowa i śledzenie przetwarzania.
- [Pobieranie faktur](../how-to-guides/download-invoices.md): XML faktury bezpośrednio albo z paczki eksportu.
- [Interfejs publiczny](../reference/public-api.md): stabilne publiczne importy dla kodu aplikacji.
