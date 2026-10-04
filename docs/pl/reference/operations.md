---
title: Referencja operacji
description: Konfiguracja transportu, retry, timeouty workflow, pola logowania i wznawialne referencje KSeF.
---

Ta strona zapisuje zachowania operacyjne ważne dla integracji produkcyjnych.
Nie jest walkthrough wysyłki ani uwierzytelniania.

## TransportConfig

`TransportConfig` jest używany tylko wtedy, gdy SDK tworzy wewnętrznego klienta
`httpx`. Jeśli przekażesz `http_client`, ten klient posiada timeouty HTTP, pool,
TLS, proxy, `trust_env`, HTTP/2, custom transport i event hooki.

```python
TransportConfig(
    timeouts=TimeoutConfig(),
    pool=ConnectionPoolConfig(),
    retry=RetryConfig(),
    tls=TlsConfig(),
    proxy_url=None,
    trust_env=True,
    http2=True,
    auto_refresh_tokens=True,
)
```

| Pole | Typ | Domyślnie | Przekazywane do |
| --- | --- | --- | --- |
| `timeouts` | `TimeoutConfig` | `TimeoutConfig()` | `httpx.Timeout` |
| `pool` | `ConnectionPoolConfig` | `ConnectionPoolConfig()` | `httpx.Limits` |
| `retry` | `RetryConfig` | `RetryConfig()` | Middleware retry SDK |
| `tls` | `TlsConfig` | `TlsConfig()` | Weryfikacja TLS w `httpx` |
| `proxy_url` | `str | None` | `None` | Proxy `httpx` |
| `trust_env` | `bool` | `True` | Obsługa zmiennych środowiskowych przez `httpx` |
| `http2` | `bool` | `True` | Flaga HTTP/2 w `httpx` |
| `auto_refresh_tokens` | `bool` | `True` | Odświeżanie access tokenu przez klientów uwierzytelnionych, zobacz [Odświeżanie access tokenu](#odświeżanie-access-tokenu) |

`auto_refresh_tokens` jest jedynym polem, które nie konfiguruje `httpx`, więc
działa także wtedy, gdy przekażesz własny `http_client`.

## TimeoutConfig

`TimeoutConfig` kontroluje pojedynczy request HTTP. Nie kontroluje tego, jak
długo SDK odpytuje stan workflow KSeF.

| Pole | Domyślnie | Znaczenie |
| --- | --- | --- |
| `connect` | `5.0` | Czas na zestawienie połączenia. |
| `read` | `30.0` | Czas oczekiwania na bajty odpowiedzi. |
| `write` | `30.0` | Czas wysyłania bajtów requestu. |
| `pool` | `5.0` | Czas oczekiwania na połączenie z poola. |

## ConnectionPoolConfig

| Pole | Domyślnie | Znaczenie |
| --- | --- | --- |
| `max_connections` | `100` | Maksymalna liczba otwartych połączeń. |
| `max_keepalive_connections` | `20` | Maksymalna liczba bezczynnych połączeń keep-alive. |
| `keepalive_expiry` | `30.0` | Wygaśnięcie bezczynnego keep-alive w sekundach. |

## TlsConfig

| Pole | Domyślnie | Znaczenie |
| --- | --- | --- |
| `verify` | `True` | Przekazywane do `httpx`, chyba że ustawiono `ca_bundle_path`. |
| `ca_bundle_path` | `None` | Ścieżka bundle CA używana jako wartość `verify` w `httpx`. |

## RetryConfig

`RetryConfig` kontroluje middleware retry SDK. Obejmuje błędy transportu i
ponawialne odpowiedzi HTTP dla ponawialnych typów requestów.

| Pole | Domyślnie |
| --- | --- |
| `max_attempts` | `3` |
| `initial_delay` | `0.5` |
| `max_delay` | `4.0` |
| `backoff_multiplier` | `2.0` |
| `retryable_status_codes` | `(429, 502, 503, 504)` |

Opóźnienie retry jest wykładnicze:

```text
min(initial_delay * backoff_multiplier ** (attempt - 1), max_delay)
```

Jeżeli KSeF wyśle `Retry-After`, jako sekundy albo datę HTTP, middleware retry
użyje tej wartości, ale nie większej niż `max_delay`.

## Ponawialne requesty

SDK ponawia tylko kształty requestów, które są wystarczająco bezpieczne do
powtórzenia na poziomie transportu.

| Typ requestu | Zachowanie retry |
| --- | --- |
| `GET` | Ponawialny. |
| `DELETE` | Ponawialny. |
| Większość `POST` | Nie jest ponawiana automatycznie. |
| Wybrane `POST` | Ponawiane automatycznie, gdy są na liście niżej. |

Ponawialne grupy `POST`:

| Obszar | Operacje |
| --- | --- |
| Uwierzytelnianie | challenge, refresh token |
| Faktury | query metadanych |
| Certyfikaty | query, retrieve |
| Uprawnienia | query personal, authorization, EU entity, person, subordinate entity i subunit |

Wysyłka faktury, nadawanie uprawnień, enrollment certyfikatu, generowanie
tokenu, otwieranie sesji online i otwieranie sesji batch nie są ponawiane przez
middleware retry SDK. Zapisz zwrócone referencje i wznawiaj przez status zamiast
tworzyć te operacje ponownie w ciemno.

Redeem tokenu uwierzytelnienia także nigdy nie jest ponawiany, ponieważ KSeF
zwraca parę access/refresh tylko raz. Utrata odpowiedzi redeem rzuca
`KSeFAuthTokenRedemptionError` z `outcome_ambiguous=True`; nie powtarzaj tej
operacji automatycznie.

## Odświeżanie access tokenu

Klienci uwierzytelnieni odświeżają access token samodzielnie, używając refresh
tokenu z uwierzytelnienia albo z `AuthenticationResumeState`, z którego zostali
wznowieni.

| Wyzwalacz | Zachowanie |
| --- | --- |
| Proaktywny | Request, który zastaje access token na mniej niż 60 sekund przed `access_token_valid_until`, najpierw go odświeża, a potem jest wysyłany z nowym tokenem. |
| Reaktywny | Odpowiedź `401` wywołuje jedno odświeżenie i jedną ponowną próbę tego samego requestu. Drugi `401` jest zgłaszany jako `KSeFAuthError`. |
| Współbieżność | Requesty współdzielą jedno odświeżenie: lock w `Client`, `asyncio.Lock` w `AsyncClient`. |
| Inne statusy | `403` i pozostałe błędy nie powodują odświeżenia. |

`auth.auth_tokens`, `auth.access_token` i `auth.resume_state()` zawsze zwracają
bieżące tokeny, więc po długo trwającej pracy zapisz `resume_state()` ponownie.

Gdy refresh token wygasł albo KSeF go odrzucił, request rzuca
`KSeFAuthenticationExpiredError`, podklasę `KSeFAuthError`. Jedynym wyjściem
jest ponowne uwierzytelnienie. Jeśli refresh token już wygasł, ale access token
ma jeszcze ważność, requesty nadal używają access tokenu, dopóki KSeF go nie
odrzuci. Błędy transportu i inne błędy wywołania odświeżenia są propagowane bez
zmian.

Odświeżanie nigdy nie dotyczy jednorazowego redeem uwierzytelnienia ani
transferów presigned do zewnętrznego storage (upload części batch, pobieranie
eksportów). Używają osobnych ścieżek i nie niosą tokenu bearer.

Aby zarządzać tokenami samodzielnie, wyłącz to zachowanie. Wygasłe tokeny
ujawnią się wtedy jako `KSeFAuthError`, a `client.authentication.refresh()`
pozostaje dostępne.

```python
client = Client(Environment.PRODUCTION, transport_config=TransportConfig(auto_refresh_tokens=False))
```

## Timeouty pollingu workflow

Helpery pollingowe używają argumentów `timeout` i `poll_interval`. Są to
deadline'y workflow, nie timeouty requestu HTTP. Gdy zostanie rzucony timeout
pollingu, zdalny workflow KSeF może nadal zakończyć się później.

| Workflow | Wyjątek timeout | Identyfikator w wyjątku |
| --- | --- | --- |
| Polling uwierzytelniania | `KSeFAuthPollingTimeoutError` | `reference_number` |
| Polling aktywacji/statusu tokenu | `KSeFTokenStatusTimeoutError` | `reference_number` |
| Polling widoczności metadanych | `KSeFInvoiceQueryTimeoutError` | tylko `timeout` |
| Gotowość pobrania faktury | `KSeFInvoiceDownloadTimeoutError` | `ksef_number` |
| Przetwarzanie faktury online | `KSeFInvoiceProcessingTimeoutError` | `invoice_reference_number` |
| Gotowość paczki eksportu | `KSeFExportTimeoutError` | `reference_number` |
| Nadanie albo cofnięcie uprawnienia | `KSeFPermissionOperationTimeoutError` | `reference_number` |
| Wydanie certyfikatu | `KSeFCertificateEnrollmentTimeoutError` | `reference_number` |
| Zakończenie sesji batch | `KSeFBatchSessionTimeoutError` | `reference_number` |
| Zakończenie sesji online | `KSeFOnlineSessionTimeoutError` | `reference_number` |

Po timeoutcie wznów polling zapisanymi identyfikatorami. Nie traktuj lokalnego
deadline'u jako dowodu, że zdalna operacja się nie udała.

## Rate limit

Odpowiedzi KSeF `429` są klasyfikowane jako `KSeFRateLimitError`. Wyjątek
udostępnia:

| Atrybut | Znaczenie |
| --- | --- |
| `retry_after` | Liczba sekund z `Retry-After` (forma sekundowa albo data HTTP), jeśli KSeF zwrócił nagłówek; inaczej `None`. |
| `status_code` | Zawsze `429`. |
| `response` | Sparsowany payload błędu KSeF, jeśli jest dostępny. |

Używaj `retry_after` do planowania pracy w tle. W request handlerach lepiej
zwrócić albo zakolejkować pracę do ponowienia niż usypiać request.

## Granice sekretów i logowania

Nie loguj:

- access tokenów;
- refresh tokenów;
- wartości tokenów KSeF;
- kluczy prywatnych;
- haseł PEM albo PKCS#12;
- surowego XML faktury, chyba że polityka retencji na to pozwala;
- zserializowanego stanu sesji online albo batch.

Przydatne pola logów produkcyjnych:

| Pole | Znaczenie |
| --- | --- |
| `environment` | `test`, `demo` albo `production`. |
| `workflow` | Nazwa operacji na poziomie aplikacji. |
| `session_reference_number` | Referencja sesji online albo batch. |
| `invoice_reference_number` | Referencja faktury w sesji. |
| `ksef_number` | Finalny numer KSeF po przyjęciu faktury. |
| `operation_reference_number` | Referencja operacji tokenu, uprawnienia, certyfikatu, auth albo eksportu. |
| `sdk_error_code` | `KSeFException.context["code"]`, gdy istnieje. |
| `ksef_code` | Surowy kod błędu KSeF z `KSeFApiError.ksef_code`, gdy istnieje. |
| `trace_id` | Identyfikator śledzenia KSeF z `KSeFApiError.trace_id`; podaj go, kontaktując się z pomocą KSeF. |

## Wznawialny stan workflow

Większość workflow KSeF zaczyna się referencją i kończy przez polling albo
późniejsze pobranie. Zapisz referencję przed czekaniem.

| Workflow | Zapisz przed czekaniem |
| --- | --- |
| Uwierzytelnianie | referencję operacji auth i czas życia tymczasowego tokenu auth |
| Wysyłka faktury online | referencję sesji i numer referencyjny faktury |
| Upload batch | referencję sesji batch, referencje uploadu, metadane paczki i stan batch, dopóki jest potrzebny |
| Eksport faktur | numer referencyjny eksportu i chroniony materiał uchwytu eksportu |
| Generowanie tokenu | numer referencyjny tokenu i zwrócony sekret tokenu |
| Nadanie/cofnięcie uprawnień | numer referencyjny operacji uprawnień |
| Enrollment/revoke certyfikatu | referencję operacji certyfikatu albo numer seryjny certyfikatu |

## Powiązana referencja

- [Cykl życia klienta](client-lifecycle.md): Sprawdź konstruktory, własność gałęzi, zamykanie i błędy lifecycle.
- [Obsługa błędów](errors.md): Sprawdź klasy wyjątków SDK, błędy API KSeF i timeouty.
- [Konfiguracja klienta](../how-to-guides/client-setup.md): Zastosuj te ustawienia w przykładach setupu sync i async.
- [Status i UPO](../concepts/status-and-upo.md): Zrozum statusy, dokumenty UPO, polling i lokalne deadline'y.
