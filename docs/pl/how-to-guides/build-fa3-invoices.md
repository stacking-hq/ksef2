---
title: Budowanie faktur FA(3)
description: Pełny model faktury FA(3) i XML z buildera o składni łańcuchowej.
---

Użyj `InvoiceBuilder`, gdy aplikacja ma dane faktury jako obiekty Pythona i SDK ma złożyć z nich typowany model FA(3) oraz XML. Builder korzysta z publicznych nazw pól SDK, a potem tworzy ten sam agregat `KsefInvoice`, którego używają mapowania FA(3).

:::tip[Builder obejmuje zaawansowane rodzaje faktur]
`InvoiceBuilder` to publiczny, zagnieżdżony builder faktur zwykłych, uproszczonych, korekt, zaliczek, rozliczeń zaliczek, korekt zaliczek i korekt rozliczeń. Bezpośrednio złóż `KsefInvoice` tylko wtedy, gdy masz już instancje modeli albo świadomie pomijasz składnię buildera.
:::

## Budowa buildera

Builder ma trzy poziomy:

| Poziom | Co zawiera | Typowe metody |
| --- | --- | --- |
| Faktura | Nagłówek, sprzedawcę, nabywcę, podmioty trzecie, stopkę, załącznik i wynik końcowy. | `header()`, `seller()`, `buyer()`, `third_party()`, `footer()`, `attachment()`, `build()`, `to_xml()` |
| Treść | Rodzaj faktury FA(3) i pola wspólne treści. | `standard()`, `simplified()`, `correction()`, `advance()`, `settlement()`, `correction_advance()`, `correction_settlement()` |
| Sekcje zagnieżdżone | Powtarzalne albo opcjonalne szczegóły treści. | `rows()`, `payment()`, `annotations()`, `correction()`, `order()`, `advance()`, `settlement()`, `transaction()` |

Każdy zagnieżdżony builder wraca do rodzica przez `.done()`. Builder faktury może zwrócić publiczny model przez `build()`, wygenerowany model schemy FA(3) przez `to_spec()` albo tekst XML przez `to_xml()`.

## Zbuduj fakturę zwykłą

Najpierw ustaw strony faktury na builderze faktury, wybierz ścieżkę `.standard()`, a potem uzupełnij sekcje zagnieżdżone.

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import InvoiceBuilder, VatRate

builder = (
    InvoiceBuilder()
    .header(system_info="ksef2 builder guide")
    .seller(
        name="Demo Seller Sp. z o.o.",
        tax_id="5261040828",
        country_code="PL",
        address_line_1="Prosta 1",
        address_line_2="00-001 Warszawa",
    )
    .buyer(
        name="Demo Buyer Sp. z o.o.",
        tax_id="5250001009",
        country_code="PL",
        address_line_1="Kwiatowa 2",
        address_line_2="00-002 Warszawa",
    )
    .standard()
    .issue_date(date(2026, 6, 24))
    .issue_place("Warszawa")
    .invoice_number("FV/1/2026")
    .rows()
    .add_line(
        name="Usługa wdrożeniowa",
        quantity=Decimal("2"),
        unit_price_net=Decimal("150.00"),
        vat_rate=VatRate.VAT_23,
    )
    .add_line(
        name="Pakiet wsparcia",
        quantity=Decimal("1"),
        unit_price_net=Decimal("50.00"),
        vat_rate=VatRate.VAT_8,
    )
    .done()
    .payment()
    .via("bank_transfer")
    .due_on(date(2026, 7, 8))
    .bank_account("PL10101010101010101010101010")
    .done()
    .annotations()
    .split_payment()
    .done()
    .done()
)
```

Wywołaj `build()`, gdy potrzebujesz typowanego publicznego modelu faktury.

```python
invoice = builder.build()

print(invoice.body.invoice_number)
# FV/1/2026
print(invoice.total_net)
# 350.00
print(invoice.total_vat)
# 73.00
print(invoice.total_gross)
# 423.00
```

## Wybierz rodzaj faktury

Po `header()`, `seller()` i `buyer()` wybierz jeden selektor treści:

| Selektor | Zastosowanie | Typowe sekcje zagnieżdżone |
| --- | --- | --- |
| `standard()` | Zwykłe faktury VAT. | `rows()`, `payment()`, `annotations()`, `transaction()`, `settlement()` |
| `simplified()` | Faktury uproszczone. | `rows()`, `payment()`, `annotations()`, `settlement()` |
| `correction()` | Korekty wcześniejszych faktur. | `rows()`, `correction()`, `payment()`, `annotations()` |
| `advance()` | Faktury zaliczkowe. | `order()`, `payment()`, `advance()`, `annotations()`, `transaction()` |
| `settlement()` | Faktury rozliczające zaliczki. | `rows()`, `payment()`, `advance()`, `settlement()`, `transaction()` |
| `correction_advance()` | Korekty faktur zaliczkowych. | `order()`, `correction()`, `advance()`, `payment()` |
| `correction_settlement()` | Korekty faktur rozliczających. | `rows()`, `correction()`, `advance()`, `settlement()`, `payment()` |

Wszystkie selektory treści mają wspólne metody, między innymi `currency()`, `issue_date()`, `issue_place()`, `invoice_number()`, `date_of_supply()`, `billing_period()`, `add_description()`, `mark_fp()`, `related_party_transaction()` i `summary_overrides()`.

Dla faktury w walucie innej niż PLN ustaw `vat_currency_exchange_rate()` razem z `currency()`. `build()` zgłasza czytelny `ValueError`, gdy faktura w obcej walucie nie ma kursu VAT.

## Dodaj pozycje faktury

Użyj `rows().add_line()` dla zwykłych danych aplikacji. Builder wylicza brakujące sumy pozycji z `quantity`, jednej ceny jednostkowej i klasyfikacji VAT. Przekaż `unit_price_net` albo `unit_price_gross`, ale nie oba naraz.

Builder zaokrągla kwoty netto i VAT każdej pozycji do dwóch miejsc po przecinku, a następnie dodaje je do sum faktury. W przykładzie `10 000 × 1,5 × 10,01` obliczenie dla każdej pozycji daje 150 200,00 netto i 34 500,00 VAT. Obliczenie od sum daje 150 150,00 netto i 34 546,00 VAT. Builder stosuje kwoty pozycji wymagane przez FA(3), więc jego sumy mogą różnić się od obliczenia, które zaokrągla tylko raz na poziomie faktury.

```python
builder = (
    InvoiceBuilder()
    .header(system_info="rows example")
    .seller(
        name="Demo Seller Sp. z o.o.",
        tax_id="5261040828",
        country_code="PL",
        address_line_1="Prosta 1",
    )
    .buyer(
        name="Demo Buyer Sp. z o.o.",
        tax_id="5250001009",
        country_code="PL",
        address_line_1="Kwiatowa 2",
    )
    .standard()
        .issue_date(date(2026, 6, 24))
        .invoice_number("FV/2/2026")
        .rows()
            .add_line(
                name="Usługa w cenie brutto",
                quantity=Decimal("2"),
                unit_price_gross=Decimal("123.00"),
                vat_rate=VatRate.VAT_23,
            )
        .done()
    .done()
)
```

Użyj `add_line_model()` albo `replace_lines()`, gdy inna warstwa utworzyła już modele `InvoiceRow`. Użyj `summary_overrides()`, gdy oficjalny przypadek FA(3) wymaga wartości podsumowania, których nie należy wyliczać z pozycji.

Builder wylicza kwoty każdej pozycji, zaokrągla je do dwóch miejsc metodą `ROUND_HALF_UP`, a potem sumuje zaokrąglone pozycje. Domyślnie obowiązuje zaokrąglanie każdej pozycji z osobna. Builder nie udostępnia trybu obliczeń od sumy.

Kwoty, ilości, ceny i kursy walut przyjmują `Decimal`, `int`, `float` oraz napisy z liczbą. Pydantic konwertuje wartości `float` na `Decimal` przez ich reprezentację tekstową, co odpowiada `Decimal(str(value))`, zanim policzy pozycję. Użyj `Decimal` albo napisu z liczbą, żeby zachować dokładną wartość dziesiętną danych wejściowych.

## Dodaj płatności i adnotacje

Builder płatności obsługuje formę płatności, terminy, płatności częściowe, rachunki bankowe, rachunki faktora, rabaty, linki płatności i IP KSeF.

Gdy dodajesz płatności częściowe, wywołaj `partial_payment_status("partial")` dla faktury zapłaconej w części albo `partial_payment_status("final")` dla faktury zapłaconej w całości w ratach. Odpowiadają one wartościom flagi XSD `1` i `2`. Builder wymaga jawnego wyboru przy `done()` albo `build()`, bo same wpisy płatności nie określają statusu.

```python
_ = (
    builder.standard()
    .payment()
        .via("bank_transfer")
        .due_on(date(2026, 7, 8))
        .partial_payment_status("partial")
        .add_partial_payment(
            amount=Decimal("50.00"),
            payment_date=date(2026, 6, 24),
            payment_form="card",
        )
        .bank_account(
            "PL10101010101010101010101010",
            bank_name="Demo Bank S.A.",
            account_description="Rachunek PLN",
        )
    .done()
    .annotations()
        .split_payment()
        .cash_accounting(False)
        .margin_procedure("travel_agency")
    .done()
    .done()
)
```

Większość metod adnotacji przyjmuje wartości logiczne albo napisy zbliżone do wyliczeń i zapisuje odpowiednią flagę FA(3) tylko wtedy, gdy jest potrzebna.

## Zbuduj korektę

Korekta zostaje w builderze. Użyj selektora `.correction()`, dodaj ujemne pozycje albo pozycje przed i po zmianie, a potem otwórz zagnieżdżoną sekcję `.correction()` z powodem korekty i wskazaniem faktur korygowanych.

```python
from datetime import date
from decimal import Decimal

from ksef2.fa3 import InvoiceBuilder, InvoiceSummaryOverrides, VatRate

correction = (
    InvoiceBuilder()
    .header(system_info="ksef2 correction guide")
    .seller(
        name="Demo Seller Sp. z o.o.",
        tax_id="5261040828",
        country_code="PL",
        address_line_1="Prosta 1",
    )
    .buyer(
        name="Demo Buyer Sp. z o.o.",
        tax_id="5250001009",
        country_code="PL",
        address_line_1="Kwiatowa 2",
    )
    .correction()
    .issue_date(date(2026, 7, 1))
    .issue_place("Warszawa")
    .invoice_number("FK/1/2026")
    .summary_overrides(
        InvoiceSummaryOverrides(
            base_rate_net_total=Decimal("-100.00"),
            base_rate_vat_total=Decimal("-23.00"),
            total_gross=Decimal("-123.00"),
        )
    )
    .rows()
    .add_line(
        name="Korekta usługi wdrożeniowej",
        quantity=Decimal("1"),
        unit_price_net=Decimal("-100.00"),
        vat_rate=VatRate.VAT_23,
    )
    .done()
    .correction()
    .reason("Korekta ceny")
    .effect_type("other_date")
    .add_corrected_invoice(
        issue_date=date(2026, 6, 24),
        invoice_number="FV/1/2026",
        ksef_id="5261040828-20260624-ABCDEFABCDEF-FF",
    )
    .done()
    .done()
    .build()
)
```

Sekcja korekty obsługuje też okres faktury korygowanej, skorygowane dane sprzedawcy, skorygowanych nabywców oraz metody, które przyjmują gotowe modele FA(3).

Korekta może wprost opisać różnicę, także jedną ujemną pozycją. Jeśli chcesz pokazać stan przed i po, dodaj obie pozycje przez `rows().add_line()`. Dla pierwotnej ustaw `before_correction=True` (pole FA(3) `StanPrzed`), a pozycję po korekcie dodaj bez tej flagi. Builder liczy sumy korekty jako wartości po zmianie minus wartości sprzed zmiany. Wskazanie korygowanej faktury dodaj w zagnieżdżonej sekcji `.correction()`.

## Zbuduj zaliczkę i rozliczenie

Faktura zaliczkowa łączy ścieżkę treści z zamówieniem, płatnością i opcjonalnym wskazaniem wcześniejszych zaliczek. Faktura rozliczeniowa może potem wskazać wcześniejsze faktury zaliczkowe.

```python
advance_xml = (
    InvoiceBuilder()
    .header(system_info="advance guide")
    .seller(
        name="Demo Developer S.A.",
        tax_id="5261040828",
        country_code="PL",
        address_line_1="Sadowa 1",
    )
    .buyer(
        name="Demo Buyer",
        tax_id="5250001009",
        country_code="PL",
        address_line_1="Kwiatowa 2",
    )
    .advance()
        .issue_date(date(2026, 8, 1))
        .invoice_number("FZ/1/2026")
        .order(declared_total=Decimal("324000.00"))
            .add_line(
                name="Rezerwacja mieszkania",
                quantity=Decimal("1"),
                unit_price_net=Decimal("300000.00"),
                vat_rate=VatRate.VAT_8,
                gross_amount=Decimal("324000.00"),
            )
        .done()
        .payment()
            .via("bank_transfer")
            .already_paid(date(2026, 8, 1))
        .done()
    .done()
    .to_xml()
)
```

```python
settlement_xml = (
    InvoiceBuilder()
    .header(system_info="settlement guide")
    .seller(
        name="Demo Developer S.A.",
        tax_id="5261040828",
        country_code="PL",
        address_line_1="Sadowa 1",
    )
    .buyer(
        name="Demo Buyer",
        tax_id="5250001009",
        country_code="PL",
        address_line_1="Kwiatowa 2",
    )
    .settlement()
        .issue_date(date(2026, 9, 1))
        .invoice_number("FR/1/2026")
        .rows()
            .add_line(
                name="Rozliczenie mieszkania",
                quantity=Decimal("1"),
                unit_price_net=Decimal("185185.19"),
                vat_rate=VatRate.VAT_8,
            )
        .done()
        .advance()
            .add_invoice_reference(ksef_id="5261040828-20260801-ABCDEFABCDEF-FF")
        .done()
        .payment()
            .via("bank_transfer")
            .due_on(date(2026, 9, 15))
        .done()
    .done()
    .to_xml()
)
```

## Dodaj szczegóły faktury

Szczegóły spoza treści faktury możesz dodać przed ścieżką treści albo po niej.

| Potrzeba | Metoda łańcuchowa | Metoda z gotowym modelem |
| --- | --- | --- |
| Gotowy model nagłówka, sprzedawcy, nabywcy, stopki albo załącznika | Użyj buildera, gdy chcesz edytować pola. | `header_model()`, `seller_model()`, `buyer_model()`, `footer_model()`, `attachment_model()` |
| Podmiot trzeci | `third_party(...)` | `add_third_party_model()`, `replace_third_parties()` |
| Stopka rejestrowa albo nota prawna | `footer().add_information().add_registry().done()` | `footer_model()` |
| Załącznik z blokami danych albo tabelami | `attachment().build_data_block()...done().done()` | `attachment_model()` |

```python
builder = (
    builder
    .third_party(
        name="Additional buyer",
        tax_id="3333333333",
        address_country_code="PL",
        address_line_1="Polna 3",
        role="additional_buyer",
        share_percentage=Decimal("50"),
    )
    .footer()
        .add_information("Faktura wygenerowana elektronicznie.")
        .add_registry(krs="0000123456", regon="123456789")
    .done()
    .attachment()
        .build_data_block()
            .set_header("Specyfikacja dostawy")
            .add_paragraph("Towar sprawdzono przed wysyłką.")
            .build_table()
                .set_columns(["txt", "decimal"], names=["Usługa", "Kwota netto"])
                .add_row(["Consulting", "1000.00"])
            .done()
        .done()
    .done()
)
```

## Wygeneruj XML

Builder może zwrócić trzy postacie faktury:

- `build()` zwraca `KsefInvoice`.
- `to_spec()` zwraca wygenerowany model schemy FA(3) `Faktura`.
- `to_xml()` zwraca XML jako napis.
- `to_xml()` domyślnie sprawdza wynik względem dołączonego XSD FA(3) i zgłasza `ValueError`, jeśli serializacja utworzyła dokument niezgodny ze schematem.
- Używaj `to_xml(validate=False)` wyłącznie do świadomej serializacji diagnostycznej albo pośredniej, która nie zostanie wysłana do KSeF.

```python
from pathlib import Path

invoice = builder.build()
spec = builder.to_spec()
xml_text = builder.to_xml()
Path("invoice.xml").write_text(xml_text, encoding="utf-8")
```

Do sesji interaktywnej albo wsadowej przekaż bajty XML.

Budowanie faktury i renderowanie PDF mają różny koszt. W jednym zgłoszonym pomiarze budowa faktury z 10 000 pozycji zajęła 4,3 s i osiągnęła szczytowo 63 MB pamięci. PDF z 2 000 pozycji powstawał 24 s. Wynik zależy od komputera i treści faktury, dlatego zmierz reprezentatywne faktury u siebie.

```python
from ksef2 import FormSchema

invoice_xml = builder.to_xml().encode("utf-8")

with auth.online_session(form_code=FormSchema.FA3) as session:
    sent = session.send_invoice(invoice_xml=invoice_xml)
    print(sent.reference_number)
```

## Zapisz i odtwórz szkic

Niepełny stan buildera zapisuj przez `dump_state()` albo `dump_state_json()`. Później odtworzysz go przez `from_state()` albo `from_state_json()`.

```python
from ksef2.fa3 import InvoiceBuilder, KsefInvoiceDraft

draft_json = builder.dump_state_json(indent=2)
draft = KsefInvoiceDraft.model_validate_json(draft_json)
restored = InvoiceBuilder.from_state(draft)
```

Jeżeli masz już kompletny `KsefInvoice`, otwórz go ponownie w builderze przez `InvoiceBuilder.from_invoice(invoice)`.

## Rozwiąż typowe błędy

| Błąd | Znaczenie | Naprawa |
| --- | --- | --- |
| `Invoice header is required but not set.` | Builder faktury nie ma nagłówka. | Wywołaj `header()` albo `header_model()` przed `build()`, `to_spec()` albo `to_xml()`. |
| `Invoice seller is required but not set.` | Brakuje sprzedawcy. | Wywołaj `seller()` albo `seller_model()`. |
| `Invoice buyer is required but not set.` | Brakuje nabywcy. | Wywołaj `buyer()` albo `buyer_model()`. |
| `Invoice body is required but not set.` | Nie wybrano i nie zakończono ścieżki treści. | Wywołaj selektor, na przykład `standard()` albo `correction()`, uzupełnij wymagane pola i wróć przez `.done()`. |
| `Provide either unit_price_net or unit_price_gross, not both.` | Pozycja ma niejednoznaczną cenę. | Przekaż tylko jedną cenę jednostkową i pozwól builderowi wyliczyć sumy. |
| `... details are empty. Set at least one field before calling done().` | Otworzono opcjonalną sekcję, ale nie dodano danych. | Dodaj dane sekcji przed `.done()` albo nie twórz tej sekcji. |

## Zalecany przepływ

1. Utwórz `InvoiceBuilder()` i ustaw nagłówek, sprzedawcę oraz nabywcę.

2. Wybierz ścieżkę treści: `standard()`, `correction()`, `advance()` albo inny selektor pasujący do dokumentu.

3. Dodaj sekcje zagnieżdżone, takie jak `rows()`, `payment()`, `annotations()`, `correction()`, `order()`, `footer()` albo `attachment()`.

4. Użyj `build()` dla publicznego modelu przy sprawdzaniu danych i `to_xml()` na ścieżce wysyłki.

5. Zakoduj XML do bajtów, zanim przekażesz go do sesji interaktywnej albo wsadowej.

## Odczytaj istniejącą fakturę FA(3)

`parse_invoice_xml` przyjmuje bajty XML i zwraca publiczny model `KsefInvoice`. Nie wymaga importowania prywatnych schematów ani mapowań. Krótki napis wyglądający jak ścieżka zgłasza `KSeFArgumentError`. Przed parsowaniem odczytaj plik przez `Path(...).read_bytes()`.

Istniejący XML jest parsowany bez reguł biznesowych buildera. Walidacja XSD
jest opcjonalna. Włącz ją przez `parse_invoice_xml(xml, validate=True)` lub
`InvoiceXSLTRenderer(validate=True)` z dołączonym arkuszem stylów. Przy przeglądaniu faktury zaakceptowanej przez KSeF renderuj oryginalny
XML. Ponowne budowanie przez `InvoiceBuilder.from_invoice` stosuje reguły szkicu
i nie zachowuje bezstratnie XML. Dla ZAL `P_15` oznacza wpłaconą zaliczkę,
niezależną od zadeklarowanej wartości zamówienia. Zadeklarowana wartość zamówienia
jest zachowywana również wtedy, gdy różni się od podanych pozycji zamówienia.
Ilość zero jest dozwolona w wierszach KOR po korekcie. Pozostałe wiersze szkicu
nadal odrzucają ilość zero.

XML FA(2) jest rozpoznawany, ale nieobsługiwany. Użyj przeglądarki obsługującej
FA(2) lub arkusza wizualizacji FA(2) Ministerstwa Finansów. Nie zmieniaj
przestrzeni nazw, aby przedstawić fakturę FA(2) jako FA(3).

Błędy parsowania zgłaszają `KSeFValidationError`, który nadal jest `ValueError`.
Błędy renderowania zgłaszają `KSeFInvoiceRenderingError`. Oba wyjątki udostępniają
`hint` (`str | None`) i atrybuty błędów XML, dostępne również w `context`:

- `field_path: str | None`: XPath XML dla błędów XSD lub ścieżka pola modelu szkicu.
- `detected_schema: str | None`: `"FA(2)"`, `"FA(3)"` lub `None`, gdy schemat jest nieznany.
- `detected_namespace: str | None`: przestrzeń nazw korzenia, jeśli można ją odczytać.
- `local_rule: bool`: `True` dla lokalnej reguły szkicu, `False` dla błędów XML/XSD.
- `accepted_by_ksef: bool | None`: `None`, gdy akceptacja jest nieznana. Samo
  parsowanie XML nie potwierdza akceptacji przez KSeF.

Buduj wskazówki na podstawie tych pól zamiast analizować treść komunikatu wyjątku.

```python
from pathlib import Path
from ksef2.fa3 import InvoiceBuilder, parse_invoice_xml

xml_bytes = Path("invoice.xml").read_bytes()
invoice = parse_invoice_xml(xml_bytes)
print(invoice.seller.tax_id, invoice.body.issue_date, invoice.total_gross)

builder = InvoiceBuilder.from_invoice(invoice)
rebuilt_xml = builder.to_xml()
```

Parser uwzględnia deklarację kodowania XML, odrzuca DTD oraz inne przestrzenie nazw faktur i stosuje sprawdzenie domenowe. Nieprawidłowe dane powodują `ValueError` z zachowaną pierwotną przyczyną. Parser nie wykonuje pełnego sprawdzenia XSD i nie zachowuje formatowania oryginalnego XML. `builder.to_xml()` sprawdza wynik względem schematu FA(3) dostarczonego z SDK. Zachowaj oryginalne bajty do obliczania skrótu weryfikacyjnego.

## Zgodność z wersją 0.17.0

Wszystkie cztery zgłoszone problemy buildera odtworzono na tagu 0.17.0. Faktury `KOR_ZAL` i `KOR_ROZ` bez wierszy są teraz obsługiwane przez `correction_advance()` i `correction_settlement()`. Podaj `summary_overrides(InvoiceSummaryOverrides(...))`, gdy sum nie można wyliczyć z wierszy. `return_of_excise(True)` zapisuje teraz `ZwrotAkcyzy=1`. `False` i `None` pomijają opcjonalny znacznik. Odczyt pominiętego znacznika zwraca `None`. `annotations().add_new_transport_item(...).done()` bez innych adnotacji naprawiono już wcześniej. Nadal sprawdzają to testy regresji.

## Powiązane strony

- [Dokumentacja API Pythona: builder faktur FA(3)](../reference/api/fa3.md): Sygnatury buildera, agregat faktury, szkice i nadpisania podsumowania.
- [Szybki start](../getting-started/quickstart.md): Złóż, wyślij, potwierdź i pobierz fakturę w środowisku testowym od początku do końca.
- [Wysyłanie faktur](send-invoices.md): Użyj wyniku buildera w sesji interaktywnej albo wsadowej.
- [Interfejs publiczny](../reference/public-api.md): Stabilne publiczne importy używane przez kod buildera faktur.
