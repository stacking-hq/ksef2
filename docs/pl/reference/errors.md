---
title: Referencja błędów
description: Hierarchia wyjątków SDK, atrybuty, kody błędów KSeF, wskazówki i klasy timeoutów pollingu.
---

ksef2 rzuca wyjątki SDK dla każdego błędu, który klasyfikuje, także dla błędów
żądań HTTP: żadna metoda publiczna nie przepuszcza błędu żądania `httpx` do
wywołującego. Łap `KSeFException`, żeby obsłużyć każdy błąd SDK, albo węższy
`KSeFTransportError`, gdy żądanie nie dało odpowiedzi, której SDK mógłby użyć.
Błędy, których SDK nie zgłasza, np. `TypeError` z Twoich własnych argumentów,
pozostają zwykłymi wyjątkami Pythona. Transfery przez presigned URL-e do
zewnętrznego storage używają opisanych niżej dedykowanych wyjątków zamiast
klasyfikacji błędów API lub uwierzytelnienia KSeF.

## Rozgałęziaj po klasie albo po `ksef_code`

Obsługuj błędy po klasie wyjątku, a dla błędów API KSeF po `ksef_code`. Nigdy nie
rozgałęziaj po treści komunikatu: komunikaty są pisane dla ludzi, zawierają
aktualne sformułowania KSeF i mogą zmienić się między wydaniami. To samo dotyczy
`hint`: pokaż go albo zaloguj, ale nie parsuj.

## Klasy bazowe

| Klasa | Baza | `code` | Główne atrybuty |
| --- | --- | --- | --- |
| `KSeFException` | `Exception` | `SDK_ERROR` | `context`, `hint` |
| `KSeFPollingTimeoutError` | `KSeFException` | `POLLING_TIMEOUT` | `timeout` |
| `KSeFResponseValidationError` | `KSeFValidationError` | `RESPONSE_VALIDATION_ERROR` | `context`, `hint` |
| `KSeFProfileConfigError` | `KSeFValidationError` | `PROFILE_CONFIG_ERROR` | `context`, `hint` |
| `KSeFSessionFailedError` | `KSeFSessionError`, `KSeFOperationFailedError` | `SESSION_FAILED` | `reference_number`, `session_status_code`, `description`, `details`, `status` |
| `KSeFTokenActivationFailedError` | `KSeFApiError`, `KSeFOperationFailedError` | `TOKEN_ACTIVATION_FAILED` | `reference_number`, `token_status` |
| `KSeFOperationFailedError` | `KSeFException` | `OPERATION_FAILED` | Wspólna baza błędów operacji zakończonych niepowodzeniem. |
| `KSeFNotFoundError` | `KSeFApiError` | `NOT_FOUND` | `status_code`, `ksef_code`, `details`, `response` |
| `KSeFServerError` | `KSeFApiError` | `SERVER_ERROR` | `status_code`, `ksef_code`, `details`, `response` |
| `KSeFTransportError` | `KSeFException` | `TRANSPORT_ERROR` | `method`, `path`, `outcome_ambiguous` |
| `KSeFApiError` | `KSeFException` | `API_ERROR` | `status_code`, `ksef_code`, `exception_code`, `trace_id`, `details`, `response` |
| `KSeFNotReadyError` | `KSeFApiError` | `NOT_READY` | Atrybuty błędu API |
| `KSeFAuthError` | `KSeFApiError` | `AUTH_ERROR` | Atrybuty błędu API |
| `KSeFPermissionDeniedError` | `KSeFApiError` | `PERMISSION_DENIED` | Atrybuty błędu API |
| `KSeFAuthenticationExpiredError` | `KSeFAuthError` | `AUTHENTICATION_EXPIRED` | Atrybuty błędu API |
| `KSeFRateLimitError` | `KSeFApiError` | `RATE_LIMIT_ERROR` | `retry_after` oraz atrybuty błędu API |
| `KSeFExternalTransferError` | `KSeFTransportError` | `EXTERNAL_TRANSFER_ERROR` | `operation`, `host`, `reference_number`, `part_ordinal`, `status_code`, `outcome_ambiguous` |
| `KSeFBatchUploadError` | `KSeFExternalTransferError` | `BATCH_UPLOAD_ERROR` | Atrybuty transferu zewnętrznego oraz `recovery_state()` i `recovery_prepared_batch()` |
| `KSeFInvoiceRejectedError` | `KSeFSessionError` | `INVOICE_REJECTED` | `invoice_reference_number`, `invoice_status_code`, `description`, `details`, `extensions`, `status` |

Łap węższe podklasy przed `KSeFException`, gdy workflow ma konkretną akcję
odzyskiwania.

```python
try:
    result = auth.invoices.query_metadata(filters=filters)
except KSeFRateLimitError as exc:
    retry_after = exc.retry_after
except KSeFNotReadyError:
    ...  # KSeF jeszcze nie skończył; poczekaj i zapytaj ponownie
except KSeFApiError as exc:
    if exc.ksef_code == 21405:
        details = exc.details
    trace_id = exc.trace_id  # podaj go, kontaktując się z pomocą KSeF
except KSeFTransportError as exc:
    if exc.outcome_ambiguous:
        ...  # KSeF mógł przyjąć żądanie; sprawdź rezultat przed ponowną wysyłką
except KSeFException as exc:
    context = exc.context
```

## Klasy wyjątków SDK

| Klasa | `code` | Kiedy jest rzucana |
| --- | --- | --- |
| `KSeFPollingTimeoutError` | `POLLING_TIMEOUT` | Baza dziesięciu timeoutów pollingu workflow. |
| `KSeFResponseValidationError` | `RESPONSE_VALIDATION_ERROR` | Nieprawidłowa odpowiedź API lub metadane eksportu. |
| `KSeFProfileConfigError` | `PROFILE_CONFIG_ERROR` | Nieprawidłowa konfiguracja profilu, brak sekretów lub błąd wczytywania poświadczeń. |
| `KSeFSessionFailedError` | `SESSION_FAILED` | Przetwarzanie sesji online lub wsadowej zakończyło się błędem. |
| `KSeFTokenActivationFailedError` | `TOKEN_ACTIVATION_FAILED` | Aktywacja wygenerowanego tokenu nie powiodła się lub token został unieważniony. |
| `KSeFNotFoundError` | `NOT_FOUND` | Brak zasobu według kodu KSeF lub HTTP 404/410. |
| `KSeFServerError` | `SERVER_ERROR` | Sesja tymczasowo niedostępna lub HTTP 5xx. |
| `KSeFClientClosedError` | `CLIENT_CLOSED` | Klient główny albo klient sesji użyty po zamknięciu. |
| `KSeFUnsupportedEnvironmentError` | `UNSUPPORTED_ENVIRONMENT` | Gałąź albo przepływ tylko dla TEST użyty poza `Environment.TEST`. |
| `KSeFValidationError` | `VALIDATION_ERROR` | Niepoprawne dane wejściowe SDK, błędny payload odpowiedzi, błędny profil albo błędne argumenty sesji/batch. |
| `KSeFArgumentError` | `ARGUMENT_ERROR` | Wywołanie łączy argumenty niedozwolone przez SDK, na przykład oba albo żaden z `form_code` i `state`. Podklasa `KSeFValidationError`, `TypeError` i (przez `KSeFValidationError`) `ValueError`. |
| `KSeFInvoiceRenderingError` | `INVOICE_RENDERING_ERROR` | Błędy opcjonalnego renderowania XSLT/PDF. |
| `KSeFEncryptionError` | `ENCRYPTION_ERROR` | Błąd szyfrowania tokenu, klucza symetrycznego, faktury albo deszyfrowania. |
| `KSeFSessionError` | `SESSION_ERROR` | Naruszenie stanu sesji, na przykład użycie zamkniętej sesji. Klasa bazowa `KSeFInvoiceRejectedError`. |
| `KSeFInvoiceRejectedError` | `INVOICE_REJECTED` | KSeF zakończył przetwarzanie faktury z sesji interaktywnej i ją odrzucił (`InvoiceSubmission.wait()`). |
| `KSeFExportFailedError` | `EXPORT_FAILED` | KSeF zakończył eksport faktur bez paczki: eksport się nie powiódł, został anulowany przez system albo wygasł (`ExportJob.wait()`). Podklasa `KSeFOperationFailedError`. |
| `KSeFPermissionOperationFailedError` | `PERMISSION_OPERATION_FAILED` | KSeF zakończył nadanie albo cofnięcie uprawnienia bez jego zastosowania (`PermissionOperation.wait()`). Podklasa `KSeFOperationFailedError`. |
| `KSeFCertificateEnrollmentFailedError` | `CERTIFICATE_ENROLLMENT_FAILED` | KSeF odrzucił, anulował albo nie zrealizował rejestracji certyfikatu (`CertificateEnrollment.wait()`). Podklasa `KSeFOperationFailedError`. |
| `KSeFAuthTokenRedemptionError` | `AUTH_TOKEN_REDEMPTION_ERROR` | Jednorazowy redeem uwierzytelnienia nie dostał użytecznej odpowiedzi i mógł się powieść. Podklasa `KSeFTransportError`. |
| `KSeFExternalTransferError` | `EXTERNAL_TRANSFER_ERROR` | Upload lub download przez presigned URL został odrzucony albo nie dał użytecznej odpowiedzi. |
| `KSeFBatchUploadError` | `BATCH_UPLOAD_ERROR` | Upload części batch nie powiódł się, ale chroniony stan odzyskiwania pozostaje dostępny. |
| `NoCertificateAvailableError` | `NO_CERTIFICATE_AVAILABLE` | Brak poprawnego certyfikatu dla podpisu albo szyfrowania. |
| `KSeFMetadataPaginationError` | `METADATA_PAGINATION_ERROR` | Paginacja metadanych nie może bezpiecznie kontynuować. |

`KSeFAuthTokenRedemptionError.outcome_ambiguous` ma zawsze wartość `True`. Nie
ponawiaj redeem: KSeF mógł już zużyć tymczasowy token uwierzytelnienia, mimo że
do wywołującego nie dotarła użyteczna odpowiedź.

`KSeFValidationError` dziedziczy również po `ValueError`, aby zachować zgodność
z kodem obsługującym wcześniejsze błędy walidacji. Gdy przyczyną jest walidacja
Pydantic, wyjątek udostępnia `.errors()` i zachowuje oryginalny wyjątek w
`__cause__`. `KSeFArgumentError` dziedziczy również po `TypeError`. HTTP 401
zgłasza `KSeFAuthError`, a HTTP 403 zgłasza `KSeFPermissionDeniedError`. Kod,
który wcześniej obsługiwał HTTP 403 przez `except KSeFAuthError`, powinien teraz
obsługiwać `KSeFPermissionDeniedError` albo `KSeFApiError`.

## Atrybuty błędu transportu

`KSeFTransportError` jest rzucany, gdy żądanie nie dało odpowiedzi, której SDK
mógłby użyć: nie dotarło do KSeF, odpowiedź nie dała się zdekodować albo
łańcuch przekierowań został porzucony. Żądania nadające się do ponowienia są
ponawiane najpierw, więc ten błąd oznacza wyczerpane próby albo żądanie, którego
SDK nie ponawia. Powtarzamy tylko błędy, których KSeF mógł nie zobaczyć, więc
błąd dekodowania albo przekierowania jest zgłaszany po jednej próbie; sama
otoczka nie zmienia liczby prób.

| Atrybut | Typ | Znaczenie |
| --- | --- | --- |
| `method` | `str \| None` | Metoda HTTP błędnego żądania albo `None`, gdy SDK jej nie zna. |
| `path` | `str \| None` | Ścieżka URL żądania bez userinfo, hosta, query i fragmentu. Presigned URL-e storage nigdy nie trafiają do tego pola. |
| `cause_type` | `str \| None` | Typ oryginalnego błędu transportu albo `None`. |
| `cause_message` | `str \| None` | Bezpieczne podsumowanie przyczyny; adresy URL i query są usuwane. |
| `outcome_ambiguous` | `bool` | `True`, gdy żądanie mogło mimo wszystko dotrzeć do KSeF: wszystko poza `GET`, `HEAD` i `OPTIONS`, bo wcześniejsza próba mogła dotrzeć. |

Oryginalny wyjątek `httpx` pozostaje dostępny jako `__cause__`. Komunikat i
`str(exc)` zawierają metodę żądania, oczyszczoną ścieżkę, typ przyczyny i jej
bezpieczne podsumowanie. `repr(exc)` i `context` nie zawierają przyczyny, treści
żądania, tokenu bearer ani podpisanego URL-a. `cause_message` może mieć wartość
`None`, gdy SDK utworzyło wyjątek bez pierwotnego błędu transportu.

```python
from ksef2 import KSeFException, KSeFTransportError

try:
    providers = client.peppol.list().first_page()
except KSeFTransportError as exc:
    print(f"{exc.method} {exc.path} nie dało użytecznej odpowiedzi")
    if exc.outcome_ambiguous:
        ...  # sprawdź, co zapisał KSeF, zanim wyślesz coś ponownie
except KSeFException as exc:
    print(exc)  # każdy pozostały błąd SDK
```

## Atrybuty transferu zewnętrznego i odzyskiwanie batch

Odpowiedzi z presigned storage nie są odpowiedziami API KSeF. Na przykład błąd
`403` storage zgłasza `KSeFExternalTransferError`, a nie `KSeFAuthError`.
Komunikat i `context` zawierają wyłącznie oczyszczony host, operację, referencję
workflow, numer części, status i flagę niejednoznaczności; nie zawierają
podpisanego URL-a.

| Atrybut | Typ | Znaczenie |
| --- | --- | --- |
| `operation` | `Literal["upload", "download"]` | Zewnętrzny transfer, który się nie powiódł. |
| `host` | `str` | Host storage bez ścieżki, query i podpisu. |
| `reference_number` | `str` | Referencja eksportu lub workflow batch. |
| `part_ordinal` | `int` | Jednobazowy numer części paczki. |
| `status_code` | `int | None` | Status odpowiedzi storage albo `None`, gdy odpowiedź nie dotarła. |
| `outcome_ambiguous` | `bool` | `True`, gdy upload mógł dotrzeć do storage mimo utraty odpowiedzi. |

`KSeFBatchUploadError.recovery_state()` celowo ujawnia wrażliwy
`BatchSessionResumeState` potrzebny do odzyskania workflow, a
`recovery_prepared_batch()` ujawnia dokładną paczkę `PreparedBatch`, której użył
nieudany upload, również tę przygotowaną wewnątrz `submit()`. Oba przekazujesz do
`auth.batch_session(state=..., prepared_batch=...)`. Żaden z nich nie trafia do
komunikatu ani `context`, ponieważ zawierają materiał szyfrujący, a stan także
presigned URL-e. Zapisuj je wyłącznie w chronionym magazynie danych
uwierzytelniających i nie ponawiaj automatycznie uploadu, gdy
`outcome_ambiguous` ma wartość `True`.

Oryginalny błąd `httpx` pozostaje dostępny przez `__cause__`. Nie loguj go bez
kontroli, ponieważ surowa diagnostyka HTTP może zawierać podpisany URL.

## Atrybuty błędu API

`KSeFApiError` jest rzucany dla sparsowanych odpowiedzi KSeF 4xx i 5xx.
Specjalne podklasy są używane dla błędów auth/autoryzacji, rate limitu oraz
zasobów, których KSeF jeszcze nie udostępnił.

| Atrybut | Typ | Znaczenie |
| --- | --- | --- |
| `status_code` | `int` | Status HTTP zwrócony przez KSeF. |
| `ksef_code` | `int | None` | Surowy kod błędu KSeF, niezależnie od wartości. `None`, gdy odpowiedź nie zawierała kodu. To źródło prawdy. |
| `exception_code` | `ExceptionCode` | Ten sam kod jako enum, gdy SDK go zna; w przeciwnym razie `UNKNOWN_ERROR`. Zachowany dla zgodności. |
| `trace_id` | `str | None` | Identyfikator śledzenia żądania w KSeF, gdy KSeF go zwrócił. |
| `details` | `list[str]` | Komunikaty szczegółowe dołączone przez KSeF; pusta lista, gdy ich brak. |
| `hint` | `str | None` | Co zrobić dalej, gdy SDK zna przyczynę. |
| `response` | `BaseModel | None` | Sparsowany payload błędu KSeF, gdy parsowanie się udało. |

Te same wartości są dostępne w `context`: `status_code`, `ksef_code`,
`trace_id`, `details` oraz `hint` (jeśli jest).

Używaj `response.model_dump()` albo `response.model_dump_json()` do
strukturalnych diagnostyk, gdy `response` nie jest `None`.

### Format komunikatu

Każdy błąd API KSeF ma ten sam format, niezależnie od kształtu odpowiedzi
(`application/problem+json`, starszy payload `exception`, inne JSON-y, tekst albo
pusta odpowiedź). SDK wybiera parser po nagłówku `Content-Type` odpowiedzi:
`application/problem+json` jest czytany jako Problem Details, `application/json`
jako starszy payload (poza 401, który KSeF wysyła jako Problem Details oznaczony
`application/json`), a wszystko inne staje się krótkim fragmentem:

```text
KSeF rejected <METODA> <ścieżka> (HTTP <status>, KSeF code <kod>): <opis>
Details: <szczegół>; <szczegół>
Trace ID: <identyfikator śledzenia>
Hint: <wskazówka>
```

Fragment `KSeF code` jest pomijany, gdy odpowiedź nie ma kodu, a linie `Details`,
`Trace ID` i `Hint` pojawiają się tylko wtedy, gdy jest co pokazać. Domyślnie
SDK wysyła `X-Error-Format: problem-details` w każdym żądaniu do API KSeF
(zobacz [Format błędów](#format-błędów)), więc KSeF zwraca błędy 400 i 429 jako
`application/problem+json`, a `trace_id` jest ustawiony w każdym błędzie API
zwróconym w tym formacie. (401, 403 i 410 zawsze są Problem Details.) Nagłówek
nie jest wysyłany do presigned URL-i storage. Treść odpowiedzi nie wchodzi do
komunikatu; zostaje w `response`. Gdy treść nie jest rozpoznawalnym błędem,
opisem jest krótki, skrócony fragment tej treści.

### Format błędów

`TransportConfig.error_format` wybiera format, o który SDK prosi KSeF:

| Wartość | Wysyłany nagłówek | Błędy 400 i 429 |
| --- | --- | --- |
| `"problem-details"` (domyślnie) | `X-Error-Format: problem-details` | `application/problem+json`: `trace_id` jest ustawiony, a `response` to `BadRequestProblemDetails` / `TooManyRequestsProblemDetails` |
| `"legacy"` | brak | `application/json`: `trace_id` to identyfikator śledzenia zawarty w `serviceCode` (brak przy 429), a `response` to `ExceptionResponse` / `TooManyRequestsResponse` |

401, 403 i 410 zawsze są Problem Details. SDK czyta oba formaty tak samo, więc
`ksef_code`, `details`, klasa i wskazówka się nie zmieniają; zmienia się tylko
typ `response`, a `trace_id` pochodzi z `serviceCode` zamiast z `traceId`
(starszy błąd 429 nie ma żadnego z nich). Używaj `"legacy"` tylko wtedy, gdy
Twój kod czyta `response` i oczekuje starszych modeli:

```python
client = Client(Environment.PRODUCTION, transport_config=TransportConfig(error_format="legacy"))
```

Treść niezgodna ze swoim modelem w specyfikacji KSeF (brak wymaganego pola,
wartość poza limitami specyfikacji) albo Problem Details ze statusem, dla
którego specyfikacja nie ma modelu, na przykład 500, jest czytana bez modelu:
`response` to `None`, ale kod KSeF, opis, szczegóły i identyfikator śledzenia
nadal pochodzą z treści, więc klasa i wskazówka się nie zmieniają.

Przykład: pobranie UPO faktury, którego KSeF jeszcze nie wystawił:

```text
KSeF rejected GET /sessions/online/S1/invoices/I1/upo (HTTP 400, KSeF code 21178): Nie znaleziono UPO dla podanych kryteriów.
Details: UPO o numerze referencyjnym I1 nie zostało znalezione.
Trace ID: 0b1f6a7c-4d2e-4a53-9a6e-3f2b9d1c8e11
Hint: KSeF has no UPO for this yet. Call `wait()` on the invoice submission or the session first, then call `download_upo()` or `download_invoice_upo()` again. If `wait()` raises `KSeFInvoiceRejectedError`, KSeF rejected the invoice and will never issue a UPO for it.
```

Opis i szczegóły pochodzą z KSeF, a `Hint` z SDK, które pisze wskazówki po
angielsku. Linia `Trace ID` pojawia się, gdy KSeF zwrócił identyfikator
śledzenia (odpowiedzi `application/problem+json`).

## Wskazówki

`KSeFException.hint` mówi, co zrobić dalej. Jest pokazywany w osobnej linii
`Hint:` w `str(exc)` i zapisany w `exc.context["hint"]`. Wskazówka jest ustawiana
tylko wtedy, gdy SDK zna przyczynę, każda wymieniona w niej metoda jest aktualna,
a dla jednego wystąpienia można ją zastąpić, przekazując `hint=...` do wyjątku.

Wskazówki do błędów API zależą najpierw od kodu KSeF, potem od statusu HTTP.
Kod z własną wskazówką zachowuje ją także przy 401 albo 403. HTTP 401 zgłasza
`KSeFAuthError`, a HTTP 403 zgłasza `KSeFPermissionDeniedError`:

| Status HTTP | Kod KSeF | Klasa | Wskazówka |
| --- | --- | --- | --- |
| inny | 21155 | `KSeFApiError` | The session has reached its invoice limit. Close it with `close()` and send the remaining invoices in a new session from `online_session()`. |
| inny | 21157 | `KSeFApiError` | Build the encrypted package with `auth.batch.prepare()`, which splits parts within KSeF size and count limits. |
| inny | 21161 | `KSeFApiError` | Build the encrypted package with `auth.batch.prepare()`, which splits parts within KSeF size and count limits. |
| inny | 21165 | `KSeFNotReadyError` | KSeF has processed the invoice but has not made it available yet. Call `download()` with a `timeout` so the SDK keeps polling until it is. |
| inny | 21178 | `KSeFNotReadyError` | KSeF has no UPO for this yet. Call `wait()` on the invoice submission or the session first, then call `download_upo()` or `download_invoice_upo()` again. If `wait()` raises `KSeFInvoiceRejectedError`, KSeF rejected the invoice and will never issue a UPO for it. |
| inny | 21180 | `KSeFApiError` | The session is already closed or in a state that does not allow this operation. Check its state with `get_status()`, or open a new session with `online_session()` or `batch_session()`. |
| inny | 21182 | `KSeFApiError` | KSeF limits how many exports can run at once. Wait for a running export to finish with `wait()`, then call `export()` again. |
| inny | 21183 | `KSeFApiError` | The date range reaches outside the data KSeF keeps. Narrow the date range in the filters passed to `search()`. |
| inny | 21184 | `KSeFServerError` | KSeF cannot accept invoices in this session at the moment. Retry later, or send the invoice in a new session from `online_session()`. |
| inny | 21205 | `KSeFApiError` | Upload every declared batch part with `upload_parts()` before closing the session, or send the batch with `submit()`. |
| inny | 21208 | `KSeFApiError` | KSeF cancelled the batch session because the parts were not uploaded or the session was not closed in time. Send the package again in a new session from `batch_session()`. |
| inny | 21418 | `KSeFApiError` | Continuation tokens come from KSeF and are only valid as returned. Iterate the pager the SDK returns, or use its `pages()`, instead of building or reusing a token yourself. |
| inny | 21470 | `KSeFApiError` | KSeF does not know the public key the request was encrypted with, or has retired it. The SDK keeps KSeF certificates for 24 hours; create a new client so it loads the current ones. |
| inny | 25001 | `KSeFApiError` | Certificate enrollment requires XAdES authentication. Authenticate with `client.authentication.with_xades()` instead of `client.authentication.with_token()`. |
| inny | 25002 | `KSeFApiError` | Certificate enrollment requires XAdES authentication. Authenticate with `client.authentication.with_xades()` instead of `client.authentication.with_token()`. |
| inny | 25003 | `KSeFApiError` | Fetch the subject data KSeF expects with `get_enrollment_data()` and build a new CSR before calling `enroll()`. |
| inny | 25006 | `KSeFApiError` | KSeF allows only a limited number of certificate enrollments. `get_limits()` shows how many are still allowed. |
| inny | 25007 | `KSeFApiError` | You hold the maximum number of KSeF certificates. Revoke one you no longer use with `revoke()`, and check `get_limits()` for the limit. |
| inny | 26001 | `KSeFApiError` | A token can only get permissions the authenticated identity holds. Request fewer permissions in `generate()`. |
| inny | 26002 | `KSeFApiError` | KSeF tokens cannot be generated in this context type. Authenticate in a supported context before calling `generate()`. |
| inny | 30001 | `KSeFApiError` | The subject or person already exists on KSeF TEST. Reuse it, or remove it first with `delete_subject()` or `delete_person()`. |
| 401 | inny | `KSeFAuthError` | KSeF rejected the credentials or the access token. Authenticate again with `client.authentication.with_token()` or `client.authentication.with_xades()`, and check that the token or certificate is valid for this context. |
| 403 | inny | `KSeFPermissionDeniedError` | The authenticated identity is not allowed to do this in the current context. Check the reason in `details`, and grant the missing permission with the permissions client, for example `grant_person()`. |

`KSeFRateLimitError` buduje wskazówkę z `retry_after`, na przykład
`Wait 17 seconds before retrying.`

Wskazówki do pozostałych błędów SDK:

| Klasa | Wskazówka |
| --- | --- |
| `KSeFArgumentError` | Pass exactly one of the mutually exclusive arguments named in the message. |
| `KSeFAuthPollingTimeoutError` | KSeF has not finished authenticating yet. Authenticate again with a larger `timeout` in `client.authentication.with_xades()` or `client.authentication.with_token()`. |
| `KSeFAuthenticationExpiredError` | Authenticate again with `client.authentication.with_token()` or `client.authentication.with_xades()`, or restore tokens that are still valid with `client.authentication.resume()`. |
| `KSeFBatchSessionTimeoutError` | KSeF may still be processing the batch. Call `wait()` on the batch session again with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `batch_session(state=...)`. |
| `KSeFCertificateEnrollmentFailedError` | Read `description` and `details` for the reason, then submit a corrected request with `enroll()`. `get_limits()` shows how many enrollments and certificates are still allowed. |
| `KSeFCertificateEnrollmentTimeoutError` | KSeF may still issue the certificate. Call `wait()` on the enrollment again with a larger `timeout`, or check it with `get_enrollment_status()`. After a restart, get the handle back with `auth.certificates.enrollment(state)` using the state saved from `resume_state()`. |
| `KSeFExportFailedError` | Read `description` and `details` for the reason, then start a new export with `export()`. |
| `KSeFExportTimeoutError` | The export may still finish. Call `wait()` on the export again with a larger `timeout`. After a restart, get the job back with `export(state=...)` using the state saved from `resume_state()`. |
| `KSeFInvoiceDownloadTimeoutError` | KSeF has not made the invoice available yet. Call `download()` again with a larger `timeout`. |
| `KSeFInvoiceProcessingTimeoutError` | KSeF may still accept the invoice. Keep waiting with `submission(reference_number).wait()` on the session, with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `online_session(state=...)`. `submission(state=...)` also takes the state saved on the submission itself, which keeps the invoice and session references together. |
| `KSeFInvoiceQueryTimeoutError` | No invoice matched before the deadline. Call `wait()` again with a larger `timeout`, or check the filters passed to `search()`. |
| `KSeFInvoiceRejectedError` | Read `description` and `details` for the reason, fix the invoice and send it again with `send_invoice()`. |
| `KSeFNotReadyError` | KSeF has not finished preparing this resource. Wait and request it again. |
| `KSeFOnlineSessionTimeoutError` | KSeF may still be processing the session. Call `wait()` on the session again with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `online_session(state=...)`. |
| `KSeFPermissionOperationFailedError` | Read `description` for the reason, fix the request and grant or revoke again. `get_operation_status()` shows the operation's final state. |
| `KSeFPermissionOperationTimeoutError` | The operation may still be applied. Call `wait()` on the operation again with a larger `timeout`, or check it with `get_operation_status()`. After a restart, get the handle back with `auth.permissions.operation(state)` using the state saved from `resume_state()`. |
| `KSeFSessionFailedError` | See why invoices failed with `list_failed_invoices()`. |
| `KSeFTokenActivationFailedError` | Generate a new token with `generate()`, or inspect the token status with `get_status()`. |
| `KSeFTokenStatusTimeoutError` | KSeF may still be activating the token. Call `wait()` on the token again with a larger `timeout`, or check it with `get_status()`. After a restart, get the handle back with `auth.tokens.generation(state)` using the state saved from `resume_state()`; that state never holds the one-time token. |

`KSeFSessionError` nie ma wskazówki na poziomie klasy. SDK ustawia ją tam, gdzie
zna przyczynę: oczekiwanie na sesję, która jest nadal otwarta (najpierw ją
zamknij), oraz sesja, którą KSeF zakończył błędem (sprawdź faktury z błędem).
Odrzucony duplikat (`440`) dostaje własną wskazówkę w `KSeFInvoiceRejectedError`.

## Kody błędów KSeF

`ksef_code` to liczba wysłana przez KSeF. SDK nigdy nie gubi nieznanego kodu.
Kody `21165` i `21178` zgłaszają `KSeFNotReadyError`. Kody `21301`, `21304`
i `21308` zgłaszają `KSeFAuthError` także przy HTTP 400. Kody `21164`, `21173`,
`21175`, `25005`, `25008` i `71001` zgłaszają `KSeFNotFoundError`, a `21184`
zgłasza `KSeFServerError`. HTTP 403 zawsze zgłasza
`KSeFPermissionDeniedError`. W pozostałych przypadkach pierwszeństwo mają
zmapowane kody KSeF, a następnie status HTTP: 401 oznacza błąd uwierzytelnienia,
429 limit żądań, 404/410 brak zasobu, a 5xx błąd serwera. Inne błędy zgłaszają
`KSeFApiError`. Poniżej są wszystkie kody, które wymienia dokumentacja API KSeF
(`openapi.json`), wszystkie w odpowiedziach HTTP 400, i każdy ma swój element
`ExceptionCode`. Test jednostkowy nie przejdzie, gdy aktualizacja specyfikacji
doda kod, którego tu nie ma.

`21178` nie zawsze znaczy „jeszcze nie wystawione”: KSeF zwraca go na stałe także
dla faktury, którą odrzucił (na przykład duplikatu, status 440). Najpierw wywołaj
`wait()`; jeśli rzuci `KSeFInvoiceRejectedError`, UPO nie będzie.

| Kod KSeF | `ExceptionCode` | Znaczenie |
| --- | --- | --- |
| `9101` | `INVALID_DOCUMENT` | Nieprawidłowy dokument. |
| `9102` | `MISSING_SIGNATURE` | Brak podpisu. |
| `9103` | `TOO_MANY_SIGNATURES` | Przekroczona liczba dozwolonych podpisów. |
| `9105` | `INVALID_SIGNATURE` | Nieprawidłowy podpis. |
| `21001` | `UNREADABLE_CONTENT` | Nieczytelna treść. |
| `21111` | `INVALID_AUTH_CHALLENGE` | Nieprawidłowe wyzwanie autoryzacyjne. |
| `21115` | `INVALID_CERTIFICATE` | Nieprawidłowy certyfikat. |
| `21117` | `INVALID_CONTEXT_IDENTIFIER` | Nieprawidłowy identyfikator podmiotu dla wskazanego typu kontekstu. |
| `21155` | `SESSION_INVOICE_LIMIT_EXCEEDED` | Przekroczono dozwoloną liczbę faktur w sesji. |
| `21157` | `INVALID_PACKAGE_PART_SIZE` | Nieprawidłowy rozmiar części pakietu. |
| `21161` | `PACKAGE_PART_LIMIT_EXCEEDED` | Przekroczono dozwoloną liczbę części pakietu. |
| `21164` | `INVOICE_NOT_FOUND` | Faktura o podanym identyfikatorze nie istnieje. |
| `21165` | `NOT_PROCESSED_YET` | Faktura o podanym numerze KSeF nie jest jeszcze dostępna. `KSeFNotReadyError`. |
| `21166` | `TECHNICAL_CORRECTION_UNAVAILABLE` | Korekta techniczna niedostępna. |
| `21167` | `TECHNICAL_CORRECTION_NOT_ALLOWED` | Status faktury nie pozwala na korektę techniczną. |
| `21173` | `SESSION_NOT_FOUND` | Brak sesji o wskazanym numerze referencyjnym. |
| `21175` | `QUERY_RESULT_NOT_FOUND` | Wynik zapytania o podanym identyfikatorze nie istnieje. |
| `21178` | `UPO_NOT_FOUND` | Nie znaleziono UPO dla podanych kryteriów. `KSeFNotReadyError`. |
| `21180` | `SESSION_STATUS_FORBIDS_OPERATION` | Status sesji nie pozwala na wykonanie operacji. |
| `21181` | `INVALID_EXPORT_REQUEST` | Nieprawidłowe żądanie eksportu faktur. |
| `21182` | `EXPORT_LIMIT_REACHED` | Osiągnięto limit trwających eksportów. |
| `21183` | `FILTER_RANGE_OUT_OF_BOUNDS` | Zakres filtrowania wykracza poza dostępny zakres danych. |
| `21184` | `SESSION_TEMPORARILY_UNAVAILABLE` | Sesja tymczasowo niedostępna. |
| `21205` | `EMPTY_PACKAGE` | Pakiet nie może być pusty. |
| `21208` | `UPLOAD_WINDOW_EXCEEDED` | Czas oczekiwania na requesty upload lub finish został przekroczony. |
| `21217` | `INVALID_CHARACTER_ENCODING` | Nieprawidłowe kodowanie znaków. |
| `21301` | `NO_AUTHORIZATION` | Brak autoryzacji. |
| `21304` | `NO_AUTHENTICATION` | Brak uwierzytelnienia. |
| `21308` | `DECEASED_PERSON_AUTHENTICATION` | Próba wykorzystania metod autoryzacyjnych osoby zmarłej. |
| `21401` | `SCHEMA_VALIDATION_FAILED` | Dokument nie jest zgodny ze schemą (XSD). |
| `21402` | `INVALID_FILE_SIZE` | Nieprawidłowy rozmiar pliku. |
| `21403` | `INVALID_FILE_HASH` | Nieprawidłowy skrót pliku. |
| `21405` | `VALIDATION_ERROR` | Błąd walidacji danych wejściowych. |
| `21406` | `SIGNATURE_AUTH_TYPE_CONFLICT` | Konflikt podpisu i typu uwierzytelnienia. |
| `21418` | `INVALID_CONTINUATION_TOKEN` | Przekazany token kontynuacji jest nieprawidłowy. |
| `21470` | `UNKNOWN_KEY_ID` | Identyfikator klucza jest nieznany lub wskazuje na wycofany klucz. |
| `25001` | `CSR_DATA_UNAVAILABLE` | Brak możliwości pobrania danych do CSR dla wykorzystanego sposobu uwierzytelnienia. |
| `25002` | `ENROLLMENT_NOT_ALLOWED` | Brak możliwości złożenia wniosku certyfikacyjnego dla wykorzystanego sposobu uwierzytelnienia. |
| `25003` | `CSR_DATA_MISMATCH` | Dane w CSR nie zgadzają się z danymi w użytym wektorze uwierzytelniającym. |
| `25004` | `INVALID_CSR` | Niepoprawny format CSR lub niepoprawny podpis CSR. |
| `25005` | `ENROLLMENT_NOT_FOUND` | Wniosek certyfikacyjny o podanym numerze referencyjnym nie istnieje. |
| `25006` | `ENROLLMENT_LIMIT_REACHED` | Osiągnięto limit możliwych do złożenia wniosków certyfikacyjnych. |
| `25007` | `CERTIFICATE_LIMIT_REACHED` | Osiągnięto limit dopuszczalnej liczby posiadanych certyfikatów. |
| `25008` | `CERTIFICATE_NOT_FOUND` | Certyfikat o podanym numerze seryjnym nie istnieje. |
| `25009` | `CERTIFICATE_NOT_REVOCABLE` | Nie można odwołać wskazanego certyfikatu, ponieważ jest już odwołany, zablokowany lub nieważny. |
| `25010` | `INVALID_KEY` | Nieprawidłowy typ lub długość klucza. |
| `25011` | `INVALID_CSR_SIGNATURE_ALGORITHM` | Nieprawidłowy algorytm podpisu CSR. |
| `26001` | `TOKEN_PERMISSIONS_NOT_HELD` | Nie można nadać tokenowi uprawnień, których nie posiadasz. |
| `26002` | `TOKEN_CONTEXT_NOT_ALLOWED` | Nie można wygenerować tokena dla obecnego typu kontekstu. |
| `30001` | `OBJECT_ALREADY_EXISTS` | Podmiot lub uprawnienie już istnieje. |
| `71001` | `COLLECTIVE_INVOICE_NOT_FOUND` | Faktura o podanym identyfikatorze nie istnieje. |
| `71002` | `COLLECTIVE_IDENTIFIER_LIMIT_REACHED` | Faktura jest już przypisana do maksymalnej liczby identyfikatorów zbiorczych. |
| `71004` | `DIFFERENT_SELLERS` | Faktury mają różnych sprzedawców. |
| `71005` | `DUPLICATE_KSEF_NUMBER` | Powtórzony numer KSeF w żądaniu. |

## Wartości ExceptionCode

`ExceptionCode` to `IntEnum`: wartością każdego elementu jest jego kod KSeF, a
nazwy są w tabeli powyżej. Jeden dodatkowy element nie jest kodem KSeF:

| Nazwa | Wartość |
| --- | --- |
| `UNKNOWN_ERROR` | `10000` |

Kody, których enum nie zna, mapują się do `ExceptionCode.UNKNOWN_ERROR`, ale
surowa liczba zostaje w `ksef_code`. W nowym kodzie preferuj `ksef_code`.

## Klasy timeoutów pollingu

Wszystkie dziesięć klas poniżej dziedziczy po `KSeFPollingTimeoutError`,
który udostępnia `timeout`.

Wyjątki timeoutów pollingu oznaczają przekroczenie lokalnego deadline'u
czekania. Same w sobie nie dowodzą, że zdalny workflow KSeF się nie udał.

| Klasa | `code` | Atrybuty identyfikujące |
| --- | --- | --- |
| `KSeFAuthPollingTimeoutError` | `AUTH_POLLING_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFTokenStatusTimeoutError` | `TOKEN_STATUS_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFInvoiceQueryTimeoutError` | `INVOICE_QUERY_TIMEOUT` | `timeout` |
| `KSeFInvoiceDownloadTimeoutError` | `INVOICE_DOWNLOAD_TIMEOUT` | `ksef_number`, `timeout` |
| `KSeFInvoiceProcessingTimeoutError` | `INVOICE_PROCESSING_TIMEOUT` | `invoice_reference_number`, `timeout` |
| `KSeFExportTimeoutError` | `EXPORT_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFPermissionOperationTimeoutError` | `PERMISSION_OPERATION_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFCertificateEnrollmentTimeoutError` | `CERTIFICATE_ENROLLMENT_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFBatchSessionTimeoutError` | `BATCH_SESSION_TIMEOUT` | `reference_number`, `timeout` |
| `KSeFOnlineSessionTimeoutError` | `ONLINE_SESSION_TIMEOUT` | `reference_number`, `timeout` |

Zapisz właściwą referencję albo stan zwracany przez `resume_state()` przed
pollingiem, aby inny proces mógł wznowić sprawdzanie statusu. Każdy błąd
timeoutu niesie `hint`, który mówi, jak czekać dalej albo wznowić pracę.

`download_upo()` na handle faktury, sesji interaktywnej i sesji batch nigdy nie
czeka i nie ma `timeout`. Najpierw wywołaj `wait()` na handle albo sesji.
Wywołane za wcześnie rzuca `KSeFNotReadyError` ze wskazówką wskazującą `wait()`;
sesja, która jest nadal otwarta, rzuca `KSeFSessionError`.

## Atrybuty rate limitu

| Atrybut | Typ | Znaczenie |
| --- | --- | --- |
| `retry_after` | `int | None` | Całkowite sekundy z `Retry-After` KSeF, podane jako sekundy albo data HTTP; `None`, gdy nagłówka brak lub nie da się go odczytać. |
| `status_code` | `int` | Zawsze `429`. |
| `response` | `BaseModel | None` | Sparsowany payload błędu KSeF, gdy jest dostępny. |
| `hint` | `str` | `Wait <retry_after> seconds before retrying.` |

## Atrybuty odrzucenia faktury

`KSeFInvoiceRejectedError` dziedziczy po `KSeFSessionError`, więc istniejące
handlery nadal go łapią. Łap `KSeFInvoiceRejectedError` przed
`KSeFSessionError`, gdy tylko naruszenie stanu sesji wymaga otwarcia sesji od
nowa albo ponownego uwierzytelnienia.

| Atrybut | Typ | Znaczenie |
| --- | --- | --- |
| `invoice_reference_number` | `str` | Numer referencyjny odrzuconej faktury. |
| `invoice_status_code` | `int` | Kod statusu faktury KSeF, na przykład `440` albo `450`. To nie jest status HTTP. |
| `description` | `str` | Opis statusu KSeF. |
| `details` | `list[str]` | Szczegóły statusu KSeF; pusta lista, gdy ich brak. |
| `extensions` | `dict[str, str | None]` | Rozszerzenia statusu KSeF; pusty słownik, gdy ich brak. |
| `status` | `SessionInvoiceStatusResponse` | Pełna odpowiedź statusu. |

W przeciwieństwie do `KSeFApiError.status_code`, które zawsze jest statusem HTTP,
`invoice_status_code` pochodzi ze statusu faktury KSeF.

Dla duplikatu (`440`) `extensions` zawiera `originalKsefNumber` i
`originalSessionReferenceNumber`. Wywołujący, który odzyskuje wysyłkę z utraconą
odpowiedzią, może przekazać `originalKsefNumber` do `download()` i
porównać pobraną fakturę z wysłaną. Jeśli to ta sama faktura, może uznać ją za
już przyjętą.

## Powiązana referencja

- [Referencja operacji](operations.md): Sprawdź retry, rate limit, timeouty workflow i wznawialny stan.
- [Cykl życia klienta](client-lifecycle.md): Sprawdź błędy lifecycle i zamykanie klientów.
- [Status i UPO](../concepts/status-and-upo.md): Zrozum statusy, dokumenty UPO i deadline'y pollingu.
