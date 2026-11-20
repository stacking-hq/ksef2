---
title: Wydanie 1.0.0
description: Co wchodzi w kontrakt zgodności pierwszego stabilnego wydania SDK.
---

ksef2 1.0.0 to pierwsze wydanie, które traktuje udokumentowane ścieżki importu dla aplikacji jako kontrakt zgodności linii 1.x.
SDK obecnie celuje w wersję OpenAPI KSeF `2.10.0`.

> **Nieoficjalne SDK.** ksef2 jest utrzymywane przez społeczność. Nie jest publikowane, zatwierdzane ani wspierane przez Ministerstwo Finansów. Oficjalna dokumentacja KSeF pozostaje miarodajnym opisem zachowania API.

[Oficjalna dokumentacja API KSeF v2](https://api-test.ksef.mf.gov.pl/docs/v2/). Traktuj dokumentację Ministerstwa Finansów jako miarodajny opis zachowania API.

## Stabilne w 1.0

Stabilnym kontraktem jest udokumentowany publiczny zestaw SDK, a nie każdy moduł, który da się zaimportować z repozytorium.

| Zakres | Kontrakt 1.0 |
| --- | --- |
| `ksef2` | Klienci pakietu głównego, środowiska, konfiguracja transportu, `FormSchema`, `__version__` i publiczne wyjątki. |
| `ksef2.clients` | Konkretne klasy klientów synchronicznych i asynchronicznych do adnotacji typów i zaawansowanego tworzenia obiektów. |
| `ksef2.models` | Publiczne modele SDK dla żądań, odpowiedzi, filtrów, paginacji, tokenów, uprawnień, sesji, sesji wsadowej i faktur. |
| Moduły klientów wysokiego poziomu | `client.authentication`, `client.encryption`, `client.peppol`, `client.testdata` oraz moduły uwierzytelnione: `auth.invoices`, `auth.tokens`, `auth.permissions`, `auth.certificates`, `auth.collective_identifiers`, `auth.limits`. |
| Przepływy identyfikatorów zbiorczych | `auth.collective_identifiers` generuje identyfikator zbiorczy dla wskazanych faktur, pobiera identyfikatory strona po stronie, rozwiązuje identyfikatory dołączone do jednego numeru KSeF oraz wymienia faktury w wybranych identyfikatorach zbiorczych. |
| Funkcje sesji | Przepływy sesji interaktywnej i wsadowej do wysyłki, cyklicznego sprawdzania statusu, UPO i numerów referencyjnych, które da się wznowić. |
| Stronicowanie | Każdy `Pager` odpowiada na `.page(cursor)` i zwraca `Page` (`items`, `next_cursor`). Kursor to stan wydany przez SDK, który można zapisać i odtworzyć po restarcie. Obok tego są `.pages()`, `.first_page()` i `.wait()`. |
| `ksef2.xades` | Wczytywanie certyfikatów, generowanie certyfikatów testowych, lokalne funkcje podpisu XAdES i `LocalSigner`. |
| `ksef2.profiles` | Funkcje konfiguracji profili zgodnych z lokalnymi profilami `ksef2-cli`. |
| `ksef2.fa3` | Publiczny builder faktur FA(3), szkice buildera i publiczne modele FA(3) używane przez ten builder. |
| `ksef2.renderers` | Opcjonalne lokalne funkcje renderowania faktur XSLT i PDF po instalacji dodatku `pdf`. |

Dokładny zakres zgodności opisuje strona interfejsu publicznego.

Pola oparte na wyliczeniach przyjmują udokumentowane wartości tekstowe bez względu na wielkość liter oraz odpowiadające im elementy wyliczenia. Nieprawidłowe wartości zgłaszają `KSeFArgumentError` z listą poprawnych opcji. Stawki VAT używają znaczników FA(3). Podawaj tekst, na przykład `"23"` albo `"zw"`. Wartości liczbowe, takie jak `23` i `Decimal("0.23")`, są odrzucane.

`PreparedBatch.to_sensitive_dict()` i `to_sensitive_json()` zapisują pełną przygotowaną paczkę jako `{"version": "1", "payload": {...}}`, z zaszyfrowanymi częściami jako Base64 bezpieczne dla URL, z dopełnieniem. Odtwórz ją przez `from_sensitive_dict()` albo `from_sensitive_json()` wraz z zapisanym stanem sesji wsadowej. Czytniki odrzucają brak wersji, nieobsługiwane wersje, niewersjonowane zapisy z wersji roboczej i nieznane pola przez `ValueError`, bez ujawniania zapisanych wartości. Przechowuj ten wynik jak sekret. Zwykły zrzut i `repr` pomijają klucze i bajty paczki. Czytniki w serii 1.x zachowują obsługę wydanych wersji zapisu. Niezgodny format wymaga nowej wersji i opisanej migracji. Stany wznowienia sesji i operacji zapisują teraz `format_version` jako tekst `"1"`. Czytniki przyjmują także liczbę całkowitą `1` zapisywaną przez wcześniejsze wydania. Kursory stronicowania zachowują osobne pole wersji całkowitej.

## Przepływy faktur w 1.0

Operacje, które uruchamiają asynchroniczną pracę KSeF, zwracają obiekt z metodą `.wait()`, a każda kolekcja zwraca jeden `Pager`. Stare nazwy zostają jako przestarzałe aliasy.

```python
# przed (0.22.x)
sent = session.send_invoice(invoice_xml=xml)
status = session.wait_for_invoice_ready(invoice_reference_number=sent.reference_number)
for m in auth.invoices.all_metadata(filters=f): ...

# po (1.0)
submission = session.send_invoice(xml)
status = submission.wait(timeout=60)
upo = submission.download_upo()
for m in auth.invoices.search(f): ...
package = auth.invoices.export(f).wait()
package.save("out/")
```

Token dostępu odświeża się automatycznie, a sesję albo eksport można wznowić metodą, która je uruchamia: `auth.online_session(state=saved)`.

## Polityka wycofywania

Stare ścieżki importu i nazwy metod pozostają działające przez całą linię 1.x. Usunięcie jest decyzją dla 2.0 (#171), także dla API wycofanych w 0.19.0. Ta decyzja zastępuje wcześniejszy plan usunięcia w 1.10.0. Zobacz tabelę [wycofywanych API](public-api.md#wycofywane-api).

## Błędy

Każdy błąd API ma ten sam format, niesie surowy kod KSeF i identyfikator śledzenia oraz podpowiada, co zrobić dalej. Treść odpowiedzi nie jest już wklejana do komunikatu. Zostaje w `e.response`. Rozróżniaj kod po klasie wyjątku albo po `ksef_code`, nigdy po treści komunikatu.

Węższe klasy obejmują typowe przypadki: `KSeFNotFoundError`, `KSeFServerError`, `KSeFResponseValidationError`, `KSeFProfileConfigError`, `KSeFSessionFailedError` i `KSeFTokenActivationFailedError`. Każde przekroczenie czasu oczekiwania dziedziczy po `KSeFPollingTimeoutError`, który udostępnia `timeout`. Węższe klasy zachowują wcześniejsze bazy, poza zmianą dla HTTP 403 opisaną poniżej. Zobacz [obsługę błędów](errors.md).

```text
# przed
API_ERROR/400: KSeF API error: 400
[UPO_NOT_FOUND:21178] Nie znaleziono UPO dla podanych kryteriów.
Response: { "exception": { "exceptionDetailList": [ ... ] } }

# po (KSeFNotReadyError)
KSeF rejected GET /sessions/online/S1/invoices/I1/upo (HTTP 400, KSeF code 21178): Nie znaleziono UPO dla podanych kryteriów.
Details: UPO o numerze referencyjnym 20260101-EE-ABC nie zostało znalezione.
Hint: KSeF has not issued the UPO yet. Wait for processing to finish and request it again.
```

`download_upo()` pobiera UPO od razu i zgłasza `KSeFNotReadyError`, jeśli UPO nie jest gotowe. Najpierw wywołaj `wait(timeout=..., poll_interval=...)` na obiekcie wysyłki albo na zamkniętej sesji, a następnie pobierz UPO (#169).

SDK domyślnie prosi o Problem Details. `TransportConfig(error_format="legacy")` wybiera starszy format HTTP 400 i 429. HTTP 401, 403 i 410 zawsze używają Problem Details (#169, #175).

## Przełomowe zmiany w 1.0

Błędy sprawdzania publicznych modeli i dane wejściowe builderów faktur zgłaszają teraz `KSeFValidationError` (albo `KSeFArgumentError`) z oryginalnym błędem Pydantic w `__cause__`. Dla zgodności te klasy dziedziczą też po `ValueError` albo `TypeError`. HTTP 403 zgłasza teraz `KSeFPermissionDeniedError` zamiast `KSeFAuthError`. Aplikacje, które obsługiwały HTTP 403 przez `except KSeFAuthError`, muszą dodać obsługę `KSeFPermissionDeniedError` albo jego bazy `KSeFApiError`.

Błędy `*FailedError` przepływu, w tym niepowodzenie aktywacji tokenu, mają teraz wspólną bazę `KSeFOperationFailedError` i zachowują dotychczasowe bazy API oraz sesji.

Błędy transportu są błędami SDK. Metoda publiczna nie przepuszcza już wyjątku `httpx`. Żądanie, które nie dało użytecznej odpowiedzi, zgłasza `KSeFTransportError` (`code = "TRANSPORT_ERROR"`) z `method`, `path` i `outcome_ambiguous`, a oryginalny wyjątek `httpx` zostaje jako `__cause__`. Obejmuje każdy `httpx.RequestError`: błędy połączenia i limity czasu, odpowiedź, której klient HTTP nie odkodował, oraz porzucony łańcuch przekierowań. Nie dziedziczy po `httpx.HTTPError`, więc bloki, które wcześniej go łapały, muszą wskazać klasę SDK. `KSeFException` obejmuje już każdy błąd SDK. Ponowienia, klasy błędów API oraz `KSeFAuthError` dla 401 zostają bez zmian. HTTP 403 zgłasza teraz `KSeFPermissionDeniedError`. Szczegóły są wyżej. `KSeFExternalTransferError`, `KSeFBatchUploadError` i `KSeFAuthTokenRedemptionError` dziedziczą teraz po `KSeFTransportError` i zachowują własne kody oraz sposób odzyskiwania. Zobacz [migrację](migration-1-0.md#błędy-transportu) i [obsługę błędów](errors.md#atrybuty-błędu-transportu).

## Publiczne, ale niższego poziomu

`ksef2.raw` i `ksef2.raw.mappers` są publicznym API dla zaawansowanych integracji. Ich ścieżki importu należą do kontraktu 1.x, ale postać modeli zgodnych ze schematem idzie za sprawdzoną wersją OpenAPI Ministerstwa Finansów.

Używaj `ksef2.raw`, gdy potrzebujesz kontroli na poziomie operacji API, dokładnej treści żądania w postaci OpenAPI, własnego szyfrowania albo diagnostyki protokołu. Większość kodu aplikacji powinna korzystać z modułów wysokiego poziomu.

## Poza kontraktem 1.x

Nie buduj kodu aplikacji na tych ścieżkach:

- każdej ścieżce modułu z członem poprzedzonym podkreśleniem, na przykład `ksef2._core` albo `ksef2._clients.base` (ścieżka modułu bez podkreślenia jest publiczna, a każda ze znakiem podkreślenia jest prywatna);
- narzędziach repozytorium `scripts/*`;
- wnętrzu wygenerowanych schematów poza `ksef2.raw.spec` i `ksef2.raw.supp`.

Dawne ścieżki `ksef2.core`, `ksef2.domain`, `ksef2.infra` i `ksef2.services`, razem z podmodułami, nadal działają jako wycofywane aliasy. Zgłaszają `DeprecationWarning` raz dla danej rodziny pakietów i wskazują zamienniki. Dawne nazwy metod też działają przez całe 1.x. Usunięcie jest możliwe nie wcześniej niż w 2.0.0. Zmiana nazw modułów prywatnych nie usuwa dawnych importów w 1.0.

[Migracja do 1.0](migration-1-0.md) pokazuje importy, wysyłkę, oczekiwanie i UPO oraz wyszukiwanie. Python zwykle ukrywa ostrzeżenia, więc włącz je w testach.

## Powiązane strony

- [Interfejs publiczny](public-api.md): Stabilne importy i zakres elementów wewnętrznych dla kodu aplikacji.
- [API niskiego poziomu](low-level/overview.md): Wspierany zakres operacji `raw` i kontrakt modeli zależnych od schematu.
- [Operacje](operations.md): Ponowienia, limity czasu, limity żądań, zasady logowania i numery referencyjne, które da się wznowić.
