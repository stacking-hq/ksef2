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
| `ksef2.models` | Modele żądań, odpowiedzi, filtrów, paginacji, tokenów, uprawnień, sesji i batchy. |
| `ksef2.fa3` | Publiczny builder faktur FA(3), drafty buildera oraz typy modelu faktury używane przez aplikacje. |
| `ksef2.xades` | Ładowanie certyfikatów, generowanie certyfikatów TEST, lokalne podpisy XAdES i `LocalSigner`. |
| `ksef2.testdata` | Pomocniki tylko dla TEST, które generują poprawne numery NIP i PESEL (`generate_nip`, `generate_pesel`). |
| `ksef2.profiles` | Helpery konfiguracji profili zgodnych z `ksef2-cli`. |
| `ksef2.renderers` | Opcjonalne lokalne helpery renderowania faktur XSLT/PDF. |
| `ksef2.raw` | Klienty endpointów niskiego poziomu, modele `spec` i `supp` oraz narzędzia kryptograficzne. |
| `ksef2.raw.mappers` | Publiczne mappery między modelami raw i modelami SDK. |

Preferuj najwyższy poziom importu pasujący do workflow:

```python
from ksef2 import Client, Environment, FormSchema, KSeFApiError
from ksef2.fa3 import FA3InvoiceBuilder, KsefInvoiceDraft, VatRate
from ksef2.models import InvoicesFilter, InvoiceMetadataParams
from ksef2.renderers import InvoicePDFExporter, InvoiceXSLTRenderer
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem
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

Moduły prywatne mogą się zmienić lub zniknąć w dowolnym wydaniu, także
poprawkowym, i nie należą do kontraktu kompatybilności. Pakiety, które wcześniejsze
wersje przedpremierowe udostępniały bez podkreślenia (`core`, `domain`, `infra`,
`endpoints`, `services`, moduły implementacji klientów, `config` i `logging`),
nie istnieją już pod tymi nazwami; ich import zgłasza `ImportError`. Te same
nazwy importuj z publicznych ścieżek powyżej, na przykład modele z
`ksef2.models`, klientów i typy usług workflow z `ksef2.clients`, a konfigurację
i wyjątki z `ksef2`.

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

Wynik tych metod traktuj jak poświadczenie: przechowuj go zaszyfrowany, nigdy
nie loguj i nie commituj.

## Reguła kompatybilności

Po 1.0 usunięcie albo zmiana nazwy stabilnej ścieżki importu wymaga major
version bump, z jednym wyjątkiem: wycofane API jest usuwane w wydaniu 1.x, które
wskazuje jego deprecation. Dodatkowe API może wejść w minor release. Patch
release powinien zachować udokumentowane importy i zachowanie poza poprawkami
błędów. Poniżej opisano dwa przypadki: zmiany wymuszone przez KSeF oraz
deprecation inicjowane przez SDK.

### Zmiany wymuszone przez KSeF

Gdy KSeF usuwa lub zmienia endpoint w sposób, którego SDK nie może wchłonąć,
wynikająca z tego zmiana może trafić do wydania minor. Jest opisana w
changelogu pod nagłówkiem „KSeF API changes”, żeby nie pomylić jej z decyzją
SDK. Zmiany łamiące, które SDK inicjuje samo, nadal wymagają major version bump.

### Polityka wycofywania

W obrębie 1.x wszystko, co SDK samo chce wycofać, jest najpierw oznaczane jako
deprecated w wydaniu minor: dostaje `@deprecated` (albo ostrzeżenie na poziomie
modułu dla aliasów), komunikat w formie „`X` is deprecated and will be removed in
ksef2 1.10.0; use `Y` instead." oraz wpis w changelogu. Komunikat i tabela
[wycofywanego API](#wycofywane-api) podają wydanie 1.x, które usuwa dane API,
więc możesz zaplanować migrację. Każde wycofanie z listy poniżej jest usuwane w
**ksef2 1.10.0**; do tego czasu każde zachowuje dotychczasowe działanie i typ
zwracany. Kolejne wycofania wskażą własne wydanie 1.x, nigdy wersję major.

## Wycofywane API

Te API działają przez całe 1.x. Każde z nich emituje `DeprecationWarning` raz na
wywołanie, jest oznaczone PEP 702 `@deprecated`, więc type checkery i IDE
wskazują miejsca użycia, i zostanie usunięte w ksef2 1.10.0. Python ukrywa
`DeprecationWarning` poza `__main__` i runnerami testów, więc uruchom testy z
`python -W error::DeprecationWarning`, żeby je znaleźć.

| Wycofane | Użyj zamiast | Usunięte w |
| --- | --- | --- |
| `Client.authenticated(tokens)` i `AsyncClient.authenticated(tokens)` | `client.authentication.resume(AuthenticationResumeState.from_tokens(tokens))` | 1.10.0 |
| `get_state()` w klientach sesji online i wsadowej | `resume_state()` | 1.10.0 |
| `BatchSessionClient.access_token` | `AuthenticatedClient.access_token` klienta nadrzędnego | 1.10.0 |
| `dump_state()` w stanie wznowienia sesji | `to_dict()` | 1.10.0 |
| `model_dump_sensitive()` w stanie wznowienia sesji | `to_dict()` | 1.10.0 |
| `model_dump_sensitive_json()` w stanie wznowienia sesji | `to_json()` | 1.10.0 |
| `from_state()` w stanie wznowienia sesji | `from_dict()` | 1.10.0 |
| `BaseSessionState`, `OnlineSessionState`, `BatchSessionState` | `BaseSessionResumeState`, `OnlineSessionResumeState`, `BatchSessionResumeState` | 1.10.0 |
| argument `access_token=` w `from_encoded()` stanu wznowienia sesji (ignorowany) | Zapisuj `AuthenticationResumeState` osobno | 1.10.0 |
| klucz `access_token` w zapisanym stanie wznowienia sesji (ignorowany; stare pliki nadal się wczytują) | Zapisuj `AuthenticationResumeState` osobno | 1.10.0 |
| klucz `auth_timeout` w profilu zapisanym przez ksef2-cli 0.0.2 | `max_poll_attempts` (i opcjonalnie `poll_interval`) | 1.10.0 |
| `send_invoice_and_wait()` i `wait_for_invoice_ready()` w sesji online | `send_invoice(...).wait()` | 1.10.0 |
| `get_invoice_upo_by_ksef_number()` i `get_invoice_upo_by_reference()` w sesji online | `download_invoice_upo(ksef_number=...)` albo `download_invoice_upo(reference_number=...)` | 1.10.0 |
| `BatchSessionClient.get_upo(upo_reference_number=...)` | `download_upo()` | 1.10.0 |
| `auth.batch.prepare_batch()` i `prepare_batch_from_paths()` | `auth.batch.prepare()` | 1.10.0 |
| `auth.batch.submit_batch()`, `submit_prepared_batch()` i `open_session()` | `auth.batch.submit()` albo `auth.batch_session(...)` | 1.10.0 |
| `auth.batch.get_status()`, `list_invoices()`, `list_failed_invoices()`, `get_upo()` i `wait_for_completion()` (z `session=`) | Te same operacje na kliencie sesji, z `wait()` i `download_upo()` | 1.10.0 |
| `auth.open_batch_session(aes_key=..., iv=..., ...)` | `auth.raw` | 1.10.0 |
| `auth.resume_online_session(state)` i `auth.resume_batch_session(state)` | `auth.online_session(state=...)` i `auth.batch_session(state=...)` | 1.10.0 |
| `auth.invoices.query_metadata()`, `query_metadata_pages()`, `all_metadata()` i `wait_for_invoices()` | `auth.invoices.search(...)` z `.pages()`, `.first_page()` i `.wait()` | 1.10.0 |
| `auth.invoices.download_invoice()` i `wait_for_invoice_download()` | `auth.invoices.download(...)` | 1.10.0 |
| `auth.invoices.schedule_export()`, `get_export_status()`, `wait_for_export_package()`, `fetch_package()`, `fetch_package_bytes()` i `export_and_download()` | `auth.invoices.export(...)`, potem `ExportJob.wait()` | 1.10.0 |
| `auth.tokens.wait_for_activation(reference_number=...)` | `auth.tokens.generate(...).wait()` | 1.10.0 |
| `auth.tokens.status()` | `auth.tokens.get_status()` | 1.10.0 |
| `auth.tokens.list_page()` i `list_all()` | `auth.tokens.list(...)` z `.pages()` i `.first_page()` | 1.10.0 |
| `auth.certificates.query()` i `all()` | `auth.certificates.list(...)` | 1.10.0 |
| `client.peppol.query()` i `all()` | `client.peppol.list(...)` | 1.10.0 |
| `auth.sessions.query()` i `all()` | `auth.sessions.list(...)` | 1.10.0 |
| `auth.sessions.close(reference_number=...)` | `auth.sessions.terminate(reference_number)` | 1.10.0 |
| `auth.invoice_sessions.query()` i `all()` | `auth.invoice_sessions.list(session_type, ...)` | 1.10.0 |
| `auth.collective_identifiers.query()` i `query_all()` | `auth.collective_identifiers.list(filters)` | 1.10.0 |
| `auth.collective_identifiers.query_by_ksef_number()` i `query_all_by_ksef_number()` | `auth.collective_identifiers.list_for_invoice(ksef_number)` | 1.10.0 |
| `auth.collective_identifiers.list_all_invoices()` | `auth.collective_identifiers.list_invoices(numbers)` | 1.10.0 |
| `auth.permissions.query_persons()`, `query_entities()`, `query_authorizations()`, `query_eu_entities()`, `query_personal()`, `query_subunits()` i `query_subordinate_entities()` | `auth.permissions.list_persons(query)`, `list_entities(query)`, `list_authorizations(query)`, `list_eu_entities(query)`, `list_personal(query)`, `list_subunits(query)` i `list_subordinate_entities(query)` | 1.10.0 |
| `auth.permissions.get_entity_roles()` | `auth.permissions.list_entity_roles()` | 1.10.0 |
| `auth.permissions.revoke_common()` | `auth.permissions.revoke()` | 1.10.0 |
| `InvoicesClient` i `AsyncInvoicesClient` importowane z `ksef2.clients` | `auth.invoices` (`InvoicesService`) | 1.10.0 |

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

`FA3InvoiceBuilder.dump_state()` i `from_state()` to osobne API szkiców buildera
i nie są wycofane.

## Referencja

- [Cykl życia klienta](client-lifecycle.md): Przejrzyj klientów głównych, klientów uwierzytelnionych i własność cyklu życia.
- [API niskiego poziomu](low-level/overview.md): Użyj schema-native wrapperów endpointów przez wspieraną powierzchnię raw.
- [Generowanie kodu sync](../contributing/sync-generation.md): Zobacz jak klient sync jest generowany z implementacji async.
