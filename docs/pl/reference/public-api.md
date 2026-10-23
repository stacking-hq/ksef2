---
title: Interfejs publiczny
description: Stabilne ścieżki importu i granice modułów wewnętrznych w ksef2 1.0.
---

W kodzie aplikacyjnym używaj ścieżek importu z tej strony. To one mają pozostać
stabilne w linii 1.x.

## Stabilne importy aplikacyjne

| Ścieżka importu | Do czego służy |
| --- | --- |
| `ksef2` | Klienci root, konfiguracja środowiska i transportu, `FormSchema`, `__version__` oraz publiczne wyjątki. |
| `ksef2.clients` | Konkretne klasy klientów sync/async, stabilne typy workflow `InvoicesService` / `BatchService` oraz typy uchwytów, stronicowania i wyniku eksportu (`InvoiceSubmission`, `ExportJob`, `GeneratedToken`, `PermissionOperation`, `CertificateEnrollment`, `ExportedInvoices`, `Pager`, `OperationHandle`) wraz z odpowiednikami async, do adnotacji typów. |
| `ksef2.models` | Modele żądań, odpowiedzi, filtrów, paginacji (w tym `Page`), tokenów, uprawnień, sesji, batchy, eksportu i stanów wznowienia (`ExportResumeState`, `GeneratedTokenResumeState`, `CertificateEnrollmentResumeState`, `PermissionOperationResumeState`, `InvoiceSubmissionResumeState`) oraz obiekt poświadczeń XAdES (`XAdESCredentials`). |
| `ksef2.fa3` | Publiczny builder faktur FA(3), drafty buildera oraz typy modelu faktury używane przez aplikacje. |
| `ksef2.xades` | Ładowanie certyfikatów, generowanie certyfikatów TEST, lokalne podpisy XAdES, `LocalSigner` oraz obiekt poświadczeń `XAdESCredentials` przyjmowany przez `with_xades()`. |
| `ksef2.testdata` | Pomocniki tylko dla TEST, które generują poprawne numery NIP i PESEL (`generate_nip`, `generate_pesel`). |
| `ksef2.profiles` | Helpery konfiguracji profili zgodnych z `ksef2-cli`. |
| `ksef2.renderers` | Opcjonalne lokalne helpery renderowania faktur XSLT/PDF. |
| `ksef2.raw` | Klienty endpointów niskiego poziomu, modele `spec` i `supp` oraz narzędzia kryptograficzne. |
| `ksef2.raw.mappers` | Publiczne mappery między modelami raw i modelami SDK. |

Preferuj najwyższy poziom importu pasujący do workflow:

```python
from ksef2 import Client, Environment, FormSchema, KSeFApiError
from ksef2.fa3 import InvoiceBuilder, KsefInvoiceDraft, VatRate
from ksef2.models import InvoicesFilter, InvoiceMetadataParams
from ksef2.renderers import InvoicePDFExporter, InvoiceXSLTRenderer
from ksef2.xades import XAdESCredentials, load_certificate_from_pem
```

## Eksporty pakietu root

Pakiet root `ksef2` jest publiczną fasadą dla typowego kodu aplikacyjnego:

- `Client`, `AsyncClient`;
- `Environment`, `TransportConfig`, `TimeoutConfig`, `RetryConfig`,
  `TlsConfig`, `ConnectionPoolConfig`;
- `FormSchema`;
- `ExceptionCode` i wszystkie publiczne klasy wyjątków `KSeF*`;
- `__version__`.

Dla tych nazw używaj importów z root zamiast sięgać do modułów implementacyjnych.

## Stabilność API niskiego poziomu

`ksef2.raw` jest publiczne, ale celowo niskopoziomowe. Ścieżka importu jest
stabilna, natomiast kształt modeli zgodnych ze schematem podąża za wersją
OpenAPI KSeF.

```python
from ksef2.raw import spec
from ksef2.raw.mappers import auth as auth_mapper
```

Nie importuj wygenerowanych modeli OpenAPI z prywatnego pakietu schem SDK.
Używaj `ksef2.raw.spec` i `ksef2.raw.supp`, żeby kod aplikacyjny pozostał na
wspieranej powierzchni.

## Ścieżki prywatne

Zasada jest prosta: **ścieżka modułu bez podkreślenia jest publiczna, a każda
ze znakiem podkreślenia jest prywatna.** `ksef2._core`, `ksef2._clients.base` i
`ksef2.raw._facade` są prywatne, podobnie jak każdy moduł poniżej nich.

Moduły prywatne mogą zmieniać się bez wydania major. Dawne ścieżki `core`,
`domain`, `infra` i `services` pozostają jako wycofywane aliasy przez całe 1.x.
Emitują ostrzeżenie raz dla danej rodziny pakietów, wskazując zamienniki,
i używają tych samych modułów oraz klas. Usunięcie jest możliwe nie wcześniej
niż w 2.0.0.

Przykłady przed i po zmianie zawiera [poradnik migracji do 1.0](migration-1-0.md).

`scripts/*` to narzędzia repozytorium, nie API pakietu.

## Sekrety i serializacja

Modele przenoszące sekrety lub podpisane adresy URL (tokeny dostępu i
odświeżania, klucze AES i IV, presigned URL-e pobierania i wysyłki, tokeny
jednorazowe) ukrywają je w `model_dump()`, `model_dump_json()` i `repr()`. Te
metody służą do logowania i wyświetlania. **Nie są formatem trwałego zapisu**:
zredagowanego wyniku nie da się wczytać z powrotem, a jego walidacja może się
nie powieść. Na przykład `UpoPage.model_validate(page.model_dump())` zgłasza
błąd, bo `download_url` jest wykluczony z dumpa, ale wymagany przez model.

Stan zapisuj i odtwarzaj jawnymi metodami:

- `to_dict()` i `to_json()` w modelach stanu wznowienia
  (`AuthenticationResumeState`, `OnlineSessionResumeState`,
  `BatchSessionResumeState`) eksportują pełne poświadczenia; odtworzysz je przez
  `from_dict()` lub `from_json()`.
- `to_sensitive_dict()` w modelach odpowiedzi z sekretami, takich jak `UpoPage`,
  `GenerateTokenResponse` i `ExportHandle`, eksportuje pola sekretne do
  świadomego, chronionego użycia.
- `to_sensitive_dict()` i `to_sensitive_json()` w `PreparedBatch` eksportują pełne
  zaszyfrowane części i materiał AES do chronionego magazynu. Odtwórz paczkę przez
  `PreparedBatch.from_sensitive_dict()` lub `from_sensitive_json()` i przekaż ją razem
  z zapisanym stanem sesji, aby wznowić upload po restarcie. Ogólne dumpy i repr
  ukrywają bajty paczki i klucze.

`XAdESCredentials` przechowuje załadowane obiekty certyfikatu i klucza prywatnego
cryptography, dostępne przez `certificate` i `private_key`. Nie zachowuje hasła ani
bajtów wejściowych, ukrywa oba obiekty w `repr()` i nie ma schematu Pydantic ani
API serializacji JSON.

Wynik tych metod traktuj jak poświadczenie: przechowuj go zaszyfrowany, nigdy
nie loguj i nie commituj.

Zakończone eksporty faktur zapisuj jako zwykłe bajty `ExportedInvoices.archive`.
Odtwórz je przez `ExportedInvoices.from_archive(archive, compression="zip")` lub
użyj `compression="tar_gz"` dla TarGz. Metadane są odczytywane leniwie z archiwum;
status paczki i adresy pobierania nie są odtwarzane. Chroń odszyfrowane dane faktur
w magazynie. Zobacz [Pobieranie faktur](../how-to-guides/download-invoices.md).

## Reguła kompatybilności

Usunięcie lub zmiana nazwy stabilnych importów SDK wymaga wydania major.
Wycofywane API działa przez całe 1.x. Nowe API może wejść w wydaniu minor.
Wydania patch zachowują udokumentowane działanie poza poprawkami błędów.

### Zmiany wymuszone przez KSeF

Gdy KSeF usuwa lub zmienia endpoint w sposób, którego SDK nie może wchłonąć,
wynikająca z tego zmiana może trafić do wydania minor. Jest opisana w
changelogu pod nagłówkiem „KSeF API changes”, żeby nie pomylić jej z decyzją
SDK. Zmiany łamiące, które SDK inicjuje samo, nadal wymagają major version bump.

### Polityka wycofywania

Wycofywane API SDK używa PEP 702 `@deprecated` lub ostrzeżenia przy imporcie
aliasu modułu i wskazuje zamiennik. Usunięcie jest decyzją dla 2.0, a nie
zaplanowaną zmianą w 1.x. Komunikat "will be removed no earlier than ksef2
2.0.0" podaje najwcześniejszą wersję, nie obiecuje usunięcia w 2.0.

## Wycofywane API

Te API działają przez całe 1.x. Każde z nich emituje `DeprecationWarning` raz na
wywołanie, jest oznaczone PEP 702 `@deprecated`, więc type checkery i IDE
wskazują miejsca użycia, i może zostać usunięte nie wcześniej niż w ksef2 2.0.0. Python ukrywa
`DeprecationWarning` poza `__main__` i runnerami testów, więc uruchom testy z
`python -W error::DeprecationWarning`, żeby je znaleźć.

| Wycofane | Użyj zamiast | Usunięte w |
| --- | --- | --- |
| `Client.authenticated(tokens)` i `AsyncClient.authenticated(tokens)` | `client.authentication.resume(AuthenticationResumeState.from_tokens(tokens))` | 2.0.0 lub później |
| `get_state()` w klientach sesji online i wsadowej | `resume_state()` | 2.0.0 lub później |
| `BatchSessionClient.access_token` | `AuthenticatedClient.access_token` klienta nadrzędnego | 2.0.0 lub później |
| `dump_state()` w stanie wznowienia sesji | `to_dict()` | 2.0.0 lub później |
| `model_dump_sensitive()` w stanie wznowienia sesji | `to_dict()` | 2.0.0 lub później |
| `model_dump_sensitive_json()` w stanie wznowienia sesji | `to_json()` | 2.0.0 lub później |
| `from_state()` w stanie wznowienia sesji | `from_dict()` | 2.0.0 lub później |
| `BaseSessionState`, `OnlineSessionState`, `BatchSessionState` | `BaseSessionResumeState`, `OnlineSessionResumeState`, `BatchSessionResumeState` | 2.0.0 lub później |
| argument `access_token=` w `from_encoded()` stanu wznowienia sesji (ignorowany) | Zapisuj `AuthenticationResumeState` osobno | 2.0.0 lub później |
| klucz `access_token` w zapisanym stanie wznowienia sesji (ignorowany; stare pliki nadal się wczytują) | Zapisuj `AuthenticationResumeState` osobno | 2.0.0 lub później |
| klucz `auth_timeout` w profilu zapisanym przez ksef2-cli 0.0.2 | `max_poll_attempts` (i opcjonalnie `poll_interval`) | 2.0.0 lub później |
| `send_invoice_and_wait()` i `wait_for_invoice_ready()` w sesji online | `send_invoice(...).wait()` | 2.0.0 lub później |
| `get_invoice_upo_by_ksef_number()` i `get_invoice_upo_by_reference()` w sesji online | `download_invoice_upo(ksef_number=...)` albo `download_invoice_upo(reference_number=...)` | 2.0.0 lub później |
| `BatchSessionClient.get_upo(upo_reference_number=...)` | `download_upo()` | 2.0.0 lub później |
| `auth.batch.prepare_batch()` i `prepare_batch_from_paths()` | `auth.batch.prepare()` | 2.0.0 lub później |
| `auth.batch.submit_batch()`, `submit_prepared_batch()` i `open_session()` | `auth.batch.submit()` albo `auth.batch_session(...)` | 2.0.0 lub później |
| `auth.batch.get_status()`, `list_invoices()`, `list_failed_invoices()`, `get_upo()` i `wait_for_completion()` (z `session=`) | Te same operacje na kliencie sesji, z `wait()` i `download_upo()` | 2.0.0 lub później |
| `auth.open_batch_session(aes_key=..., iv=..., ...)` | `auth.raw` | 2.0.0 lub później |
| `auth.resume_online_session(state)` i `auth.resume_batch_session(state)` | `auth.online_session(state=...)` i `auth.batch_session(state=...)` | 2.0.0 lub później |
| `auth.invoices.query_metadata()`, `query_metadata_pages()`, `all_metadata()` i `wait_for_invoices()` | `auth.invoices.search(...)` z `.responses()`, `.first_response()`, `.pages()`, `.first_page()` i `.wait()` | 2.0.0 lub później |
| `auth.invoices.download_invoice()` i `wait_for_invoice_download()` | `auth.invoices.download(...)` | 2.0.0 lub później |
| `auth.invoices.schedule_export()`, `get_export_status()`, `wait_for_export_package()`, `fetch_package()`, `fetch_package_bytes()` i `export_and_download()` | `auth.invoices.export(...)`, potem `ExportJob.wait()` | 2.0.0 lub później |
| `auth.tokens.wait_for_activation(reference_number=...)` | `auth.tokens.generate(...).wait()` | 2.0.0 lub później |
| `auth.tokens.status()` | `auth.tokens.get_status()` | 2.0.0 lub później |
| `auth.tokens.list_all()` | `auth.tokens.list(...)` z `.pages()` i `.first_page()` | 2.0.0 lub później |
| `auth.certificates.query()` i `all()` | `auth.certificates.list(...)` | 2.0.0 lub później |
| `client.peppol.query()` i `all()` | `client.peppol.list(...)` | 2.0.0 lub później |
| `auth.sessions.query()` i `all()` | `auth.sessions.list(...)` | 2.0.0 lub później |
| `auth.sessions.close(reference_number=...)` | `auth.sessions.terminate(reference_number)` | 2.0.0 lub później |
| `auth.invoice_sessions.query()` i `all()` | `auth.invoice_sessions.list(session_type, ...)` | 2.0.0 lub później |
| `auth.collective_identifiers.query()` i `query_all()` | `auth.collective_identifiers.list(filters)` | 2.0.0 lub później |
| `auth.collective_identifiers.query_by_ksef_number()` i `query_all_by_ksef_number()` | `auth.collective_identifiers.list_for_invoice(ksef_number)` | 2.0.0 lub później |
| `auth.collective_identifiers.list_all_invoices()` | `auth.collective_identifiers.list_invoices(numbers)` | 2.0.0 lub później |
| `auth.permissions.query_persons()`, `query_entities()`, `query_authorizations()`, `query_eu_entities()`, `query_personal()`, `query_subunits()` i `query_subordinate_entities()` | `auth.permissions.list_persons(query)`, `list_entities(query)`, `list_authorizations(query)`, `list_eu_entities(query)`, `list_personal(query)`, `list_subunits(query)` i `list_subordinate_entities(query)` | 2.0.0 lub później |
| `auth.permissions.get_entity_roles()` | `auth.permissions.list_entity_roles()` | 2.0.0 lub później |
| `auth.permissions.revoke_common()` | `auth.permissions.revoke()` | 2.0.0 lub później |
| `InvoicesClient` i `AsyncInvoicesClient` importowane z `ksef2.clients` | `auth.invoices` (`InvoicesService`) | 2.0.0 lub później |

`session.send_invoice()` zachowuje nazwę i przyjmuje XML pozycyjnie jako `bytes`
albo `str`. Zwraca teraz uchwyt `InvoiceSubmission`, który udostępnia każde pole
dawnego `SendInvoiceResponse`, więc kod czytający `.reference_number` nadal
działa.

To samo dotyczy pozostałych operacji, które KSeF kończy asynchronicznie:
`tokens.generate()` zwraca `GeneratedToken` (odczytaj `.token` od razu, `.wait()`
czeka na aktywację), `permissions.grant_*()` i `revoke*()` zwracają
`PermissionOperation`, a `certificates.enroll()` zwraca `CertificateEnrollment`.
Każdy udostępnia wszystkie pola odpowiedzi, którą zastępuje, a
`get_operation_status()` i `get_enrollment_status()` pozostają getterami danych.

`auth.collective_identifiers.list_invoices()` zachowuje nazwę, ale zwraca teraz
`Pager` po fakturach zamiast jednej strony, więc jest jedyną nazwą z powyższej
tabeli, której typ zwracany się zmienia. Iteruj po nim albo wywołaj
`.first_page()`, by wykonać dawne pojedyncze żądanie; `list_all_invoices()` nadal
zwraca strony.

`auth.tokens.list_page()` pozostaje wspierane i nie jest już opisane jako
wycofane: to pojedyncze żądanie przyjmujące własny token kontynuacji KSeF, a
stronicowanie z kursorem go nie zastępuje. Każdy `Pager`, także ten z
`auth.invoices.search(...)`, odpowiada na `.page(cursor)` zwracając `Page` z
`items` oraz `next_cursor`, który zapisujesz, by kontynuować tę kolekcję później.

`InvoiceBuilder.dump_state()` i `from_state()` to osobne API szkiców buildera
i nie są wycofane.

## Referencja

- [Cykl życia klienta](client-lifecycle.md): Przejrzyj klientów głównych, klientów uwierzytelnionych i własność cyklu życia.
- [API niskiego poziomu](low-level/overview.md): Użyj schema-native wrapperów endpointów przez wspieraną powierzchnię raw.
- [Generowanie kodu sync](../contributing/sync-generation.md): Zobacz jak klient sync jest generowany z implementacji async.
