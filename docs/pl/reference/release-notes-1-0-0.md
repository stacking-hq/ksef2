---
title: Notatki wydania 1.0.0
description: Granica stabilności i udokumentowana publiczna powierzchnia pierwszego stabilnego wydania SDK.
---

ksef2 1.0.0 to pierwsze wydanie, które traktuje udokumentowane, aplikacyjne
ścieżki importu jako kontrakt kompatybilności dla linii 1.x.
SDK obecnie celuje w wersję OpenAPI KSeF `2.8.1`.

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
| `ksef2.xades` | Ładowanie certyfikatów, generowanie certyfikatów TEST, lokalne pomocniki podpisu XAdES i `LocalSigner`. |
| `ksef2.profiles` | Pomocniki konfiguracji profili zgodnych z lokalnymi profilami `ksef2-cli`. |
| `ksef2.fa3` | Publiczny builder faktur FA(3), drafty buildera i publiczne modele domenowe FA(3) używane przez przepływy buildera. |
| `ksef2.renderers` | Opcjonalne lokalne pomocniki renderowania faktur XSLT/PDF po instalacji dodatku `pdf`. |

Dokładną granicę kompatybilności opisuje strona interfejsu publicznego.

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

Przestarzałe API jest usuwane w wskazanym wydaniu 1.x. Każde wycofanie dostarczone
z 1.0.0 zostanie usunięte w **ksef2 1.10.0**, razem z siedmioma wycofanymi
w 0.19.0. Zobacz tabelę [wycofywanych API](public-api.md#wycofywane-api).

## Błędy

Każdy błąd API ma ten sam format, niesie surowy kod KSeF i identyfikator śladu
oraz podpowiada, co zrobić dalej. Treść odpowiedzi nie jest już zrzucana do
komunikatu; pozostaje w `e.response`. Rozgałęziaj kod po klasie wyjątku lub
`ksef_code`, nigdy po treści komunikatu.

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

`download_upo()` na zgłoszeniu lub sesji czeka teraz na zakończenie przetwarzania
zamiast kończyć się zbyt wcześnie.

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

Dawne pakiety wewnętrzne (`ksef2.core`, `ksef2.domain`, `ksef2.infra`,
`ksef2.endpoints`, `ksef2.services`, moduły implementacji klientów,
`ksef2.config` i `ksef2.logging`) mają teraz prefiks podkreślenia, bez aliasów
kompatybilności: import starych ścieżek zgłasza `ImportError`. Moduły prywatne
mogą zmieniać się bez wydania 2.0.

## Powiązane strony

- [Kontrakt publicznego API](public-api.md): Przejrzyj stabilne importy i granice internal dla kodu aplikacyjnego.
- [API niskiego poziomu](low-level/overview.md): Zrozum wspieraną powierzchnię endpointów raw i kontrakt modeli zależnych od schemy.
- [Operacje](operations.md): Przejrzyj retry, timeouty, rate limity, granice logowania i wznawialne referencje.
