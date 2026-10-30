---
title: Pobieranie faktur
description: Pobierz przetworzony XML faktury bezpośrednio albo z szyfrowanej paczki eksportu.
---

Użyj `auth.invoices`, gdy potrzebujesz treści faktury po przetworzeniu jej przez KSeF. Przykłady poniżej zakładają, że masz już uwierzytelnionego klienta `auth`.

## Pobierz jedną fakturę

Jeśli masz numer KSeF, bezpośrednie pobranie jest najkrótsze.

```python
from pathlib import Path

ksef_number = "5261040828-20260625-ABCDEF012345-67"

xml_bytes = auth.invoices.download(ksef_number)
Path("invoice.xml").write_bytes(xml_bytes)
```

Jeśli faktura została dopiero wysłana, KSeF może potrzebować czasu, zanim przetworzony XML będzie dostępny. Podaj `timeout`, a `download()` będzie cyklicznie sprawdzać KSeF, aż dokument się pojawi.

```python
xml_bytes = auth.invoices.download(ksef_number, timeout=120.0, poll_interval=2.0)
Path("invoice.xml").write_bytes(xml_bytes)
```

## Zbuduj filtr eksportu

Eksportu używaj do większych pobrań. Eksport korzysta z `InvoicesFilter`, czyli z tych samych filtrów co zapytanie o metadane.

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
`restrict_to_permanent_storage_hwm_date=True` trzyma automatyczny eksport w zakresie, do którego KSeF uznaje dane za kompletne. Zapisz `permanent_storage_hwm_date` na kolejne okno synchronizacji.
:::

## Wyeksportuj wiele faktur

`export()` planuje eksport i zwraca `ExportJob`. Jego `wait()` cyklicznie sprawdza KSeF, aż paczka będzie gotowa, pobiera i odszyfrowuje części, łączy je i zwraca obiekt `ExportedInvoices`.

Dla dużych paczek użyj `job.download(Path(...))`, aby zapisać połączone, odszyfrowane archiwum na dysku. Metoda zwraca `ExportedInvoices` korzystający z tego pliku. Każda część AES jest odszyfrowywana fragmentami i sprawdzana według rozmiaru oraz sumy SHA-256 otrzymanych z KSeF. Dane trafiają do nowego pliku tymczasowego o unikalnej nazwie obok pliku docelowego. Plik docelowy jest podmieniany atomowo dopiero po poprawnym sprawdzeniu wszystkich części. W razie błędu plik tymczasowy jest usuwany, a istniejący plik docelowy zostaje bez zmian. Obecny transport HTTP buforuje każdą zaszyfrowaną odpowiedź, więc pamięć zależy od rozmiaru pobranej części, a nie od całego odszyfrowanego archiwum.

Opcjonalny `compression_type` przyjmuje `"zip"` albo `"tar_gz"`. Gdy go pominiesz, format paczki wybiera serwer.

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

`save()` rozpakowuje archiwum i odrzuca każdy wpis, którego ścieżka wychodziłaby poza katalog docelowy. Surowe bajty ZIP są dostępne jako `package.archive`.

### Wznowienie po restarcie

`job.resume_state()` zwraca `ExportResumeState` z numerem referencyjnym i kluczem odszyfrowującym paczkę. Zapisz jego JSON, a `export(state=...)` zwróci z powrotem `ExportJob`, więc `wait()` nadal działa.

```python
job = auth.invoices.export(filters)
saved = job.resume_state().to_json()   # przechowuj jak poświadczenie, nie loguj

# po restarcie
job = auth.invoices.export(state=saved)
package = job.wait(timeout=300.0)
```

Podaj dokładnie jedno z `filters` albo `state`. `to_dict()`, `from_json()` i `from_dict()` działają jak w stanach sesji. `model_dump()` i `repr()` ukrywają klucz.

### Zapisz i odtwórz zakończony eksport

`ExportResumeState` służy do eksportu, który jeszcze się nie skończył. Gdy `wait()` zwróci wynik, zapisz `package.archive` jako zwykłe bajty ZIP albo TarGz we własnym magazynie. Odtwórz te bajty przez `ExportedInvoices.from_archive()`.

```python
from pathlib import Path

from ksef2.clients import ExportedInvoices

archive_path = Path("export.zip")
archive_path.write_bytes(package.archive)

# w innym procesie
restored = ExportedInvoices.from_archive(archive_path.read_bytes())
for ksef_number, xml in restored.invoices():
    print(ksef_number, len(xml))

written = restored.save(Path("downloads"))
```

Fabryka domyślnie używa `compression="zip"`. Dla eksportu TarGz zapisz bajty archiwum w pliku `.tar.gz` i podaj `compression="tar_gz"` przy odtwarzaniu. Użyj formatu kompresji oryginalnego eksportu. Fabryka nie wykrywa go sama. Jeśli archiwum jest już na dysku, użyj `ExportedInvoices.from_path(path, compression="zip")`, aby czytać wpisy bez wczytywania całego archiwum. Obie metody przyjmują `Path` albo inny obiekt `os.PathLike`. Wartość `str` albo `bytes` zgłasza `KSeFArgumentError`, bo SDK traktuje napisy jako treść, a nie jako nazwy plików.

Utworzenie obiektu nie otwiera ani nie sprawdza archiwum. `metadata` czyta `_metadata.json` przy pierwszym dostępie i zapamiętuje wynik: `None` oznacza brak pliku, a `[]` oznacza, że plik nie zawiera faktur. Niepoprawne archiwum zgłasza błąd przy odczycie albo wypakowaniu. Niepoprawne metadane zgłaszają `KSeFValidationError` przy dostępie. `save()` odrzuca niebezpieczne ścieżki, dowiązania i pliki specjalne, zanim cokolwiek zapisze.

Archiwum zawiera już odszyfrowane dane faktur. Chroń je we własnym magazynie. Odtworzenie nie wymaga klucza szyfrowania ani dostępu do sieci. Status paczki i podpisane adresy pobierania nie są zapisane w archiwum, więc `restored.package` ma wartość `None`. `await job.wait()` zwraca tę samą klasę `ExportedInvoices`, więc kod synchroniczny i asynchroniczny zapisuje i odtwarza archiwa tak samo.

:::note[SDK odszyfrowuje części paczki]
KSeF zwraca zaszyfrowane adresy części paczki. `export()` ładuje poprawny certyfikat szyfrowania KSeF i planuje eksport z lokalnym materiałem AES, a `wait()` pobiera części i odszyfrowuje je przed zwróceniem wyniku.
:::

:::caution[Części paczki są tymczasowe]
Adresy paczki wygasają. Zapisz wypakowane XML-e faktur we własnym magazynie i zachowaj `_metadata.json`, jeśli paczka go zawiera. Gdy KSeF zakończy eksport błędem albo eksport wygaśnie, `wait()` zgłasza `KSeFExportFailedError`.
:::

## Po wysyłce faktur

Trzymaj wysyłkę, przetwarzanie i pobieranie jako osobne fazy.

1. Wyślij XML faktury przez sesję interaktywną albo wsadową.

2. Sprawdzaj cyklicznie status sesji albo faktury, aż dojdziesz do końcowego, przyjętego wyniku.

3. Zapisz zwrócone wartości `ksef_number`.

4. Pobierz jeden przetworzony dokument XML po numerze KSeF albo zbuduj filtr eksportu dla szerszego okna czasu.

## Pobieranie partii przy limitach zapytań

Nie potrzebujesz stałego `sleep` między wywołaniami `download()` ani ponownego logowania po `401`. SDK stosuje dokładnie nagłówek `Retry-After` do wartości `RetryConfig.max_retry_after` (domyślnie 120 sekund), ponawia błędy przemijające i odświeża token dostępu (`accessToken`) raz po `401`.

Jeden przypadek SDK oddaje aplikacji: gdy KSeF każe czekać dłużej niż ustalony sufit. Wtedy `download()` od razu zgłasza `KSeFRateLimitError`, bez oczekiwania, a `error.retry_after` niesie prawdziwą wartość z nagłówka.

Pojedyncze `download()` nadal blokuje, gdy nagłówek jest na tyle krótki, że SDK go stosuje. Jeśli KSeF powtarza ten sam `Retry-After`, takie wywołanie czeka maksymalnie `(max_attempts - 1) * max_retry_after`, zanim zgłosi błąd, czyli domyślnie 240 sekund. Uwzględnij to w długiej partii.

```python
from pathlib import Path

from ksef2 import KSeFRateLimitError

downloads = Path("downloads")
try:
    for ksef_number in ksef_numbers:
        xml_bytes = auth.invoices.download(ksef_number)
        downloads.joinpath(f"{ksef_number}.xml").write_bytes(xml_bytes)
except KSeFRateLimitError as error:
    # KSeF kazał czekać dłużej niż RetryConfig.max_retry_after sekund.
    # SDK nie spał. Zaplanuj pozostałe numery za error.retry_after sekund,
    # zamiast ponawiać w pętli.
    print(f"zwolnij, wróć za {error.retry_after} sekund")
```

Pełne zachowanie dla `429` i `401` oraz listę rzeczy należących do aplikacji opisuje [Operacje](../reference/operations.md).

## Następne przepływy

- [Wyszukiwanie faktur](query-invoices.md): Znajdź numery KSeF i metadane, zanim pobierzesz treść faktury.
- [Wysyłanie faktur](send-invoices.md): Wyślij XML faktury przez sesję interaktywną albo wsadową.
- [Wyszukiwanie i eksport paczek](../concepts/querying-and-exports.md): Metadane, bezpośrednie pobieranie, paczki eksportu i synchronizacja według HWM.
- [Podgląd certyfikatów szyfrowania](inspect-encryption-certificates.md): Publiczne certyfikaty KSeF używane w szyfrowanych przepływach.

## Opisy kodów bez połączenia z siecią

`InvoiceXSLTRenderer` i `InvoicePDFExporter` przyjmują `enable_code_lookups=True`, aby dodać opisy z dołączonych oficjalnych słowników XSD: krajów, walut, urzędów skarbowych, urzędów skarbowych bez WUS oraz naczelników urzędów skarbowych. Połączenie z siecią nie jest potrzebne.

```python
from ksef2.renderers import InvoiceXSLTRenderer

renderer = InvoiceXSLTRenderer(enable_code_lookups=True)
html = renderer.render_from_path("invoice.xml")
```

Domyślnie opisy kodów są wyłączone, a funkcja XSLT `document()` nie może czytać plików ani korzystać z sieci. Włączenie opisów zezwala na odczyt plików lokalnych. Dostęp do sieci i zapis pozostają zablokowane. Używaj tej opcji tylko z zaufanymi arkuszami stylów i XML faktur: oba mogą skierować `document()` do innych plików lokalnych. Odwołania do zdalnych hostów pozostają zablokowane. Opcja nie ogranicza odczytu do dołączonych słowników. Jeśli nie można odczytać dokumentu spod danego URI, `KSeFInvoiceRenderingError` zawiera ten URI w komunikacie i w `context["details"]`.

## Eksportuj PDF z weryfikacyjnym kodem QR

Zainstaluj opcjonalne zależności przez `pip install 'ksef2[pdf]'` oraz biblioteki systemowe wymagane przez [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).

```python
from ksef2 import Environment
from ksef2.renderers import InvoicePDFExporter, PDFPageSize

exporter = InvoicePDFExporter(
    page_size=PDFPageSize.A4,
    verification_environment=Environment.TEST,
)
output = exporter.export_to_file(
    "invoice.xml",
    "invoice.pdf",
    ksef_number="9999999999-20260215-ABCDEF123456-AB",
)
```

Podaj rzeczywisty numer KSeF nadany tej fakturze. `ksef_number` dodaje lokalnie wygenerowany kod QR w formacie SVG oraz numer pod kodem. Pominięcie tego argumentu zostawia dotychczasowy PDF bez QR. Ten sam argument obsługują `export_from_path()` i `export_from_string()`. `verification_environment` jest wymagane. Wybierz środowisko, w którym wystawiono fakturę. Kod zawiera NIP sprzedawcy, datę wystawienia oraz SHA-256 oryginalnych bajtów XML, zakodowany jako Base64URL bez dopełnienia, zgodnie ze [specyfikacją kodów QR Ministerstwa Finansów](https://github.com/CIRFMF/ksef-docs/blob/main/kody-qr.md). Do `export_from_string()` przekazuj bajty. Tekst jest kodowany jako UTF-8. Krótki napis wyglądający jak ścieżka, przekazany do `export_from_string()` albo `InvoiceXSLTRenderer.render_from_string()`, zgłasza `KSeFArgumentError`. Do odczytu plików użyj `export_from_path()` albo `render_from_path()`. Ponowna serializacja faktury zmienia skrót. Eksport nie sprawdza, czy faktura została przyjęta, ani czy podany numer KSeF do niej należy.

Ta opcja obsługuje faktury z nadanym numerem KSeF. Nie generuje kodu QR certyfikatu dla trybu offline, nie podpisuje adresów URL i nie zastępuje własnych układów PDF.

`PDFPageSize` obsługuje `A4`, `A4_LANDSCAPE`, `A3`, `A3_LANDSCAPE`, `LETTER` oraz `LETTER_LANDSCAPE`. Bez `page_size` obowiązuje dotychczasowe ustawienie arkusza, zwykle A4 poziomo. Jawny rozmiar strony ma pierwszeństwo przed CSS w `html_overrides`. Pozostałe reguły CSS nadal działają. Szerokie tabele mogą wymagać orientacji poziomej albo własnego CSS, żeby zmieściły się na pionowej stronie.


### Własne oznaczenia wizualizacji

Użyj `footer_text`, aby dodać tekst za fakturą i kodem QR, oraz
`watermark_text`, aby dodać znak wodny powtarzany na drukowanych stronach.
Obie opcje przyjmują zwykły tekst i domyślnie mają wartość `None`. Ustaw je
jawnie dla faktur TEST/DEMO. Środowisko nie dodaje oznaczeń automatycznie.
Stopka pojawia się raz. Te same opcje obsługuje `InvoiceXSLTRenderer` dla HTML.
Renderery lokalne działają z klientem synchronicznym i asynchronicznym.
W aplikacjach asynchronicznych użyj `asyncio.to_thread`, aby konwersja PDF
nie blokowała pętli zdarzeń.

```python
from ksef2 import Environment
from ksef2.renderers import InvoicePDFExporter

exporter = InvoicePDFExporter(
    verification_environment=Environment.TEST,
    footer_text="Test visualization",
    watermark_text="TEST",
)
pdf = exporter.export_from_path("invoice.xml")
```
