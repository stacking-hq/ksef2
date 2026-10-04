---
title: Tworzenie i zamykanie klientów
description: Argumenty konstruktorów, własność modułów, zamykanie zasobów i błędy cyklu życia w klientach ksef2.
---

Ta strona opisuje kontrakt referencyjny klientów bazowych i uwierzytelnionych.
Skorzystaj z poradnika praktycznego, gdy potrzebujesz pełnej sekwencji
konfiguracji.

## Konstruktory klienta bazowego

```python
Client(
    environment=Environment.PRODUCTION,
    *,
    transport_config=None,
    http_client=None,
)

AsyncClient(
    environment=Environment.PRODUCTION,
    *,
    transport_config=None,
    http_client=None,
)
```

| Argument | Typ sync | Typ async | Domyślnie | Znaczenie |
| --- | --- | --- | --- | --- |
| `environment` | `Environment` | `Environment` | `Environment.PRODUCTION` | Środowisko KSeF i bazowy URL klienta. |
| `transport_config` | `TransportConfig | None` | `TransportConfig | None` | Timeouty HTTP, pool, TLS, proxy, HTTP/2 i retry dla klienta HTTP tworzonego przez SDK. |
| `http_client` | `httpx.Client | None` | `httpx.AsyncClient | None` | Klient HTTP przekazany przez aplikację. Gdy jest podany, aplikacja posiada jego ustawienia HTTP i końcowe zamknięcie. |

Gdy `http_client` nie jest podany, SDK tworzy klienta `httpx` z
`transport_config` i zamyka go razem z klientem bazowym.

## Elementy klienta bazowego

| Element | Dostępny na | Zwraca | Uwagi |
| --- | --- | --- | --- |
| `authentication` | `Client`, `AsyncClient` | `AuthClient` / `AsyncAuthClient` | Punkt wejścia do tokenu, XAdES, certyfikatu TEST i profili. |
| `encryption` | `Client`, `AsyncClient` | `EncryptionClient` / `AsyncEncryptionClient` | Publiczny odczyt certyfikatów szyfrowania KSeF. |
| `peppol` | `Client`, `AsyncClient` | `PeppolClient` / `AsyncPeppolClient` | Publiczny lookup dostawców PEPPOL. |
| `testdata` | `Client`, `AsyncClient` | `TestDataClient` / `AsyncTestDataClient` | Gałąź fixture'ów tylko dla TEST. Rzuca błąd poza `Environment.TEST`. |
| `raw` | `Client`, `AsyncClient` | `RawClient` / `AsyncRawClient` | Niskopoziomowe, nieuwierzytelnione grupy endpointów. |
| `authenticated(auth_tokens)` | `Client`, `AsyncClient` | `AuthenticatedClient` / `AsyncAuthenticatedClient` | Deprecated compatibility wrapper. Użyj `authentication.resume(AuthenticationResumeState.from_tokens(auth_tokens))`. |
| `close()` | `Client` | `None` | Idempotentnie zamyka klienta HTTP sync należącego do SDK i unieważnia moduły w cache. |
| `aclose()` | `AsyncClient` | `None` | Idempotentnie zamyka zasoby async i unieważnia moduły w cache. |

Właściwości modułów są cache'owane, dopóki klient bazowy jest otwarty. Po
zamknięciu klienta dostęp do modułów i operacje chronione middleware cyklu życia
rzucają `KSeFClientClosedError`.

## Context managery

| Klient | Protokół context managera | Metoda cleanup |
| --- | --- | --- |
| `Client` | `with Client(...) as client:` | `client.close()` przy wyjściu. |
| `AsyncClient` | `async with AsyncClient(...) as client:` | `await client.aclose()` przy wyjściu. |

Context manager zamyka tylko klienta bazowego. Sesje online i batch są osobnymi
granicami cyklu życia i powinny być zamykane przez własne context managery albo
metody serwisów.

## Elementy klienta uwierzytelnionego

Uwierzytelnienie zwraca klienta uwierzytelnionego powiązanego z jednym
kontekstem KSeF i jedną parą tokenów.

| Element | Zwraca | Uwagi |
| --- | --- | --- |
| `auth_tokens` | `AuthTokens` | Modele tokenów access i refresh używane przez tę gałąź. |
| `access_token` | `str` | String bearer access tokenu. Traktuj jako sekret. |
| `refresh_token` | `str` | String refresh tokenu. Traktuj jako sekret. |
| `resume_state()` | `AuthenticationResumeState` | Serializowalny stan uwierzytelnienia zawierający access i refresh token. |
| `online_session(form_code=... \| state=...)` | Klient sesji online | Otwiera jedną sesję online faktur albo wznawia ją z zapisanego stanu (obiekt lub JSON). Async zwraca awaitable wrapper context managera. |
| `resume_online_session(state)` | Klient sesji online | Wycofane; użyj `online_session(state=...)`. |
| `batch_session(prepared_batch= \| batch_file= \| state=)` | Klient sesji batch | Otwiera sesję batch z przygotowanego batcha albo deklaracji pliku batch, albo wznawia ją z zapisanego stanu. |
| `open_batch_session(...)` | Klient sesji batch | Otwiera sesję batch, gdy caller posiada metadane szyfrowania. |
| `resume_batch_session(state)` | Klient sesji batch | Wycofane; użyj `batch_session(state=...)`. |
| `invoices` | `InvoicesService` | Metadane, pobrania bezpośrednie, eksporty, pobieranie paczek i wait helpery. |
| `batch` | `BatchService` | Wysokopoziomowy workflow przygotowania paczki, uploadu, zamknięcia, statusu i UPO. |
| `limits` | `LimitsClient` | Endpointy limitów kontekstu, podmiotu i API. |
| `tokens` | `TokensClient` | Generowanie, status, lista i unieważnianie tokenów. |
| `certificates` | `CertificatesClient` | Enrollment, pobranie, query, limity i unieważnianie certyfikatów. |
| `sessions` | `SessionManagementClient` | Lista i zamykanie sesji uwierzytelnienia. |
| `invoice_sessions` | `InvoiceSessionsClient` | Historia sesji online i batch faktur. |
| `permissions` | `PermissionsClient` | Nadawanie, query, cofanie i status operacji uprawnień. |
| `raw` | `RawAuthenticatedClient` | Niskopoziomowe, uwierzytelnione grupy endpointów. |

`AuthenticationResumeState` jest właścicielem bearer access i refresh tokenów.
`OnlineSessionResumeState` i `BatchSessionResumeState` nie zawierają danych
uwierzytelnienia; wznawiaj je przez klienta uwierzytelnionego.

Klienci uwierzytelnieni współdzielą transport i cache certyfikatów klienta
głównego. Nie posiadają osobnego klienta HTTP.

## Własność klienta HTTP

| Setup | Źródło konfiguracji HTTP | Kto zamyka zasoby HTTP |
| --- | --- | --- |
| `Client(Environment.TEST)` | SDK buduje `httpx.Client` z `TransportConfig`. | `Client.close()` albo wyjście z context managera. |
| `AsyncClient(Environment.TEST)` | SDK buduje `httpx.AsyncClient` z `TransportConfig`. | `await AsyncClient.aclose()` albo wyjście z async context managera. |
| `Client(..., http_client=http)` | Podany `httpx.Client`. | Aplikacja zamyka `http`. |
| `AsyncClient(..., http_client=http)` | Podany `httpx.AsyncClient`. | Aplikacja zamyka `http`. |

Gdy `http_client` jest podany, ustawienia HTTP takie jak timeout, pool, TLS,
proxy, `trust_env`, HTTP/2, custom transporty i event hooki pochodzą z tego
obiektu. Middleware retry SDK nadal używa `transport_config.retry`.

## Błędy lifecycle

| Błąd | Kiedy jest rzucany |
| --- | --- |
| `KSeFClientClosedError` | Klient główny albo gałąź chroniona lifecycle jest użyta po zamknięciu. |
| `KSeFUnsupportedEnvironmentError` | Gałąź tylko dla TEST, obecnie `testdata`, jest użyta poza `Environment.TEST`. |

## Powiązana referencja

- [Konfiguracja klienta](../how-to-guides/client-setup.md): Twórz klientów w skryptach, jobach i zależnościach frameworka.
- [Metody uwierzytelniania](../concepts/authentication-methods.md): Jak klient bazowy przechodzi w klienta uwierzytelnionego.
- [Referencja operacji](operations.md): Sprawdź transport, retry, timeouty i wznawialność.
- [API niskiego poziomu](low-level/overview.md): Użyj schema-native wrapperów endpointów, gdy klient workflow nie wystarcza.
