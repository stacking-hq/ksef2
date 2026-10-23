---
title: Notatki wydania 1.0.0
description: Granica stabilności i udokumentowana publiczna powierzchnia pierwszego stabilnego wydania SDK.
---

> Trwają przygotowania do wydania. Data wydania nie jest ustalona.
> Aliasy kompatybilności z [#171](https://github.com/stacking-hq/ksef2/issues/171)
> są już dostępne i objęte kontrolą zgodności dawnych API.

ksef2 1.0.0 to pierwsze wydanie, które traktuje udokumentowane, aplikacyjne
ścieżki importu jako kontrakt kompatybilności dla linii 1.x.
SDK obecnie celuje w wersję OpenAPI KSeF `2.9.0`.

> **Nieoficjalne SDK.** ksef2 jest utrzymywane społecznościowo. Nie jest
> publikowane, zatwierdzane ani wspierane przez Ministerstwo Finansów. Oficjalna
> dokumentacja KSeF pozostaje źródłem prawdy dla zachowania API.

[Oficjalna dokumentacja API KSeF v2](https://api-test.ksef.mf.gov.pl/docs/v2/) — Używaj dokumentacji Ministerstwa Finansów jako źródła prawdy dla zachowania API.

## Stabilne w 1.0

Stabilnym kontraktem jest udokumentowana publiczna powierzchnia SDK, a nie każdy
moduł, który da się zaimportować z repozytorium.

| Powierzchnia | Kontrakt 1.0 |
| --- | --- |
| `ksef2` | Klienci root, środowiska, konfiguracja transportu, `FormSchema`, `__version__` i publiczne wyjątki. |
| `ksef2.clients` | Konkretne klasy klientów sync i async do adnotacji typów i zaawansowanego konstruowania. |
| `ksef2.models` | Publiczne modele SDK dla requestów, response'ów, filtrów, paginacji, tokenów, uprawnień, sesji, batchy i faktur. |
| Wysokopoziomowe moduły klientów | `client.authentication`, `client.encryption`, `client.peppol`, `client.testdata` oraz moduły uwierzytelnione: `auth.invoices`, `auth.tokens`, `auth.permissions`, `auth.certificates`, `auth.collective_identifiers`, `auth.limits`. |
| Przepływy identyfikatorów zbiorczych | `auth.collective_identifiers` generuje identyfikator zbiorczy dla wskazanych faktur, odpytuje identyfikatory strona po stronie, rozwiązuje identyfikatory dołączone do jednej liczby KSeF oraz wymienia faktury w wybranych identyfikatorach zbiorczych. |
| Pomocniki sesji | Przepływy sesji online i batch do wysyłki, pollingu, UPO i wznawialnych referencji KSeF. |
| Stronicowanie | Każdy `Pager` odpowiada na `.page(cursor)`, zwracając `Page` (`items`, `next_cursor`), gdzie kursor to stan wydany przez SDK, który można zapisywać i odtworzyć po restarcie; obok tego `.pages()`, `.first_page()` i `.wait()`. |
| `ksef2.xades` | Ładowanie certyfikatów, generowanie certyfikatów TEST, lokalne pomocniki podpisu XAdES i `LocalSigner`. |
| `ksef2.profiles` | Pomocniki konfiguracji profili zgodnych z lokalnymi profilami `ksef2-cli`. |
| `ksef2.fa3` | Publiczny builder faktur FA(3), drafty buildera i publiczne modele domenowe FA(3) używane przez przepływy buildera. |
| `ksef2.renderers` | Opcjonalne lokalne pomocniki renderowania faktur XSLT/PDF po instalacji dodatku `pdf`. |

Dokładną granicę kompatybilności opisuje strona interfejsu publicznego.

`PreparedBatch.to_sensitive_dict()` i `to_sensitive_json()` zapisują pełną
przygotowaną paczkę jako `{"version": "1", "payload": {...}}`, z zaszyfrowanymi
częściami jako Base64 bezpieczne dla URL z dopełnieniem. Odtwórz ją przez
`from_sensitive_dict()` lub `from_sensitive_json()` wraz z zapisanym stanem sesji
batch. Czytniki odrzucają brak wersji, nieobsługiwane wersje, niewersjonowane
eksporty rozwojowe i nieznane pola przez `ValueError` bez ujawniania
zapisanych wartości. Przechowuj ten wynik jak poświadczenia; ogólne dumpy i repr
pomijają klucze i bajty paczki. Czytniki w serii 1.x zachowują obsługę wydanych
wersji zapisu. Niezgodne formaty wymagają nowej wersji i udokumentowanej migracji.
Stany wznowienia sesji i operacji zapisują teraz `format_version` jako tekst
`"1"`; czytniki przyjmują także liczbę całkowitą `1` zapisywaną przez wcześniejsze
wydania. Kursory stronicowania zachowują osobne pole wersji całkowitej.

## Przepływy faktur w 1.0

Operacje, które uruchamiają asynchroniczną pracę KSeF, zwracają uchwyt z metodą
`.wait()`, a każda kolekcja zwraca jeden `Pager`. Stare nazwy zostają jako
przestarzałe aliasy.

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

Tokeny dostępu odświeżają się automatycznie, a sesję lub eksport można wznowić
metodą, która je uruchamia: `auth.online_session(state=saved)`.

## Polityka wycofywania

Stare ścieżki importu i nazwy metod pozostają działające przez całą linię 1.x.
Usunięcie jest decyzją dla 2.0 (#171), także dla API wycofanych w 0.19.0.
Ta decyzja zastępuje wcześniejszy plan usunięcia w 1.10.0. Zobacz tabelę [wycofywanych API](public-api.md#wycofywane-api).

## Błędy

Każdy błąd API ma ten sam format, niesie surowy kod KSeF i identyfikator śladu
oraz podpowiada, co zrobić dalej. Treść odpowiedzi nie jest już zrzucana do
komunikatu; pozostaje w `e.response`. Rozgałęziaj kod po klasie wyjątku lub
`ksef_code`, nigdy po treści komunikatu.

Węższe klasy obejmują typowe przypadki: `KSeFNotFoundError`, `KSeFServerError`,
`KSeFResponseValidationError`, `KSeFProfileConfigError`, `KSeFSessionFailedError`
i `KSeFTokenActivationFailedError`. Każdy timeout oczekiwania dziedziczy po
`KSeFPollingTimeoutError`, który udostępnia `timeout`. Każda nowa klasa dziedziczy
po klasie rzucanej wcześniej, więc istniejące obsługi nadal działają. Zobacz
[referencję błędów](errors.md).

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

`download_upo()` pobiera UPO od razu i zgłasza `KSeFNotReadyError`, jeśli UPO
nie jest gotowe. Najpierw wywołaj
`wait(timeout=..., poll_interval=...)` na zgłoszeniu lub zamkniętej sesji,
a następnie pobierz UPO (#169).

SDK domyślnie żąda Problem Details. `TransportConfig(error_format="legacy")`
wybiera starszy format HTTP 400/429; HTTP 401, 403 i 410 zawsze używają
Problem Details (#169, #175).

## Przełomowe zmiany w 1.0

Błędy transportu są błędami SDK. Metoda publiczna nie przepuszcza już wyjątku
`httpx`: żądanie, które nie dało użytecznej odpowiedzi, rzuca
`KSeFTransportError` (`code = "TRANSPORT_ERROR"`) z `method`, `path` i
`outcome_ambiguous`, a oryginalny wyjątek `httpx` pozostaje jako `__cause__`.
Obejmuje każdy `httpx.RequestError`: błędy połączenia i timeouty, odpowiedź, której
klient HTTP nie odkodował, oraz porzucony łańcuch przekierowań. Nie dziedziczy on
po `httpx.HTTPError`, więc obsługujące je wcześniej bloki muszą wskazać klasę SDK;
`KSeFException` obejmuje już każdy błąd SDK. Ponowienia, klasy błędów API oraz
`KSeFAuthError` dla 401 albo 403 pozostają bez zmian.
`KSeFExternalTransferError`, `KSeFBatchUploadError` i
`KSeFAuthTokenRedemptionError` dziedziczą teraz po `KSeFTransportError` i zachowują
własne kody oraz zachowanie odzyskiwania.
Zobacz [przewodnik migracji](migration-1-0.md#błędy-transportu) i
[referencję błędów](errors.md#atrybuty-błędu-transportu).

## Publiczne, ale niższopoziomowe

`ksef2.raw` i `ksef2.raw.mappers` są publicznymi API dla zaawansowanych
integracji. Ich ścieżki importu należą do kontraktu 1.x, ale kształty modeli
schema-native podążają za sprawdzoną wersją OpenAPI Ministerstwa Finansów.

Używaj `ksef2.raw`, gdy potrzebujesz kontroli na poziomie endpointów,
dokładnych payloadów w kształcie OpenAPI, własnej obsługi szyfrowania albo
debugowania protokołu. Większość kodu aplikacyjnego powinna korzystać z
modułów wysokiego poziomu.

## Poza kontraktem 1.x

Nie buduj kodu aplikacji na tych ścieżkach:

- każdej ścieżki modułu z komponentem poprzedzonym podkreśleniem, na przykład
  `ksef2._core` lub `ksef2._clients.base` (ścieżka modułu bez podkreślenia jest
  publiczna, a każda ze znakiem podkreślenia jest prywatna);
- repozytoryjnych `scripts/*`;
- internali wygenerowanych schem poza `ksef2.raw.spec` i `ksef2.raw.supp`.

Dawne ścieżki `ksef2.core`, `ksef2.domain`, `ksef2.infra` i `ksef2.services`,
wraz z podmodułami, nadal działają jako wycofywane aliasy. Emitują
`DeprecationWarning` raz dla danej rodziny pakietów, wskazując zamienniki. Dawne nazwy metod także
działają przez całe 1.x. Usunięcie jest możliwe nie wcześniej niż w 2.0.0.
Zmiana nazw modułów prywatnych nie usuwa dawnych importów w 1.0.

[Poradnik migracji](migration-1-0.md) pokazuje importy, wysyłkę/oczekiwanie/UPO
oraz wyszukiwanie. Python zwykle ukrywa ostrzeżenia, więc włącz je w testach.

## Powiązane strony

- [Kontrakt publicznego API](public-api.md): Przejrzyj stabilne importy i granice internal dla kodu aplikacyjnego.
- [API niskiego poziomu](low-level/overview.md): Zrozum wspieraną powierzchnię endpointów raw i kontrakt modeli zależnych od schemy.
- [Operacje](operations.md): Przejrzyj retry, timeouty, rate limity, granice logowania i wznawialne referencje.
