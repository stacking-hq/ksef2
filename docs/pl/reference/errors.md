---
title: Referencja błędów
description: Hierarchia wyjątków SDK, atrybuty, kody błędów KSeF, wskazówki i klasy timeoutów pollingu.
---

ksef2 rzuca wyjątki SDK dla błędów, które potrafi sklasyfikować. Błędy
transportu, które wystąpią zanim KSeF zwróci sparsowaną odpowiedź API, pozostają
wyjątkami `httpx.HTTPError`. Transfery przez presigned URL-e do zewnętrznego
storage używają opisanych niżej dedykowanych wyjątków zamiast klasyfikacji
błędów API lub uwierzytelnienia KSeF.

## Rozgałęziaj po klasie albo po `ksef_code`

Obsługuj błędy po klasie wyjątku, a dla błędów API KSeF po `ksef_code`. Nigdy nie
rozgałęziaj po treści komunikatu: komunikaty są pisane dla ludzi, zawierają
aktualne sformułowania KSeF i mogą zmienić się między wydaniami. To samo dotyczy
`hint`: pokaż go albo zaloguj, ale nie parsuj.

## Klasy bazowe

| Klasa | Baza | `code` | Główne atrybuty |
| --- | --- | --- | --- |
| `KSeFException` | `Exception` | `SDK_ERROR` | `context`, `hint` |
| `KSeFApiError` | `KSeFException` | `API_ERROR` | `status_code`, `ksef_code`, `exception_code`, `trace_id`, `details`, `response` |
| `KSeFNotReadyError` | `KSeFApiError` | `NOT_READY` | Atrybuty błędu API |
| `KSeFAuthError` | `KSeFApiError` | `AUTH_ERROR` | Atrybuty błędu API |
| `KSeFAuthenticationExpiredError` | `KSeFAuthError` | `AUTHENTICATION_EXPIRED` | Atrybuty błędu API |
| `KSeFRateLimitError` | `KSeFApiError` | `RATE_LIMIT_ERROR` | `retry_after` oraz atrybuty błędu API |
| `KSeFExternalTransferError` | `KSeFException` | `EXTERNAL_TRANSFER_ERROR` | `operation`, `host`, `reference_number`, `part_ordinal`, `status_code`, `outcome_ambiguous` |
| `KSeFBatchUploadError` | `KSeFExternalTransferError` | `BATCH_UPLOAD_ERROR` | Atrybuty transferu zewnętrznego oraz `recovery_state()` |
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
except KSeFException as exc:
    context = exc.context
except httpx.HTTPError as exc:
    transport_error = exc
```

## Klasy wyjątków SDK

| Klasa | `code` | Kiedy jest rzucana |
| --- | --- | --- |
| `KSeFClientClosedError` | `CLIENT_CLOSED` | Klient główny albo klient sesji użyty po zamknięciu. |
| `KSeFUnsupportedEnvironmentError` | `UNSUPPORTED_ENVIRONMENT` | Gałąź albo przepływ tylko dla TEST użyty poza `Environment.TEST`. |
| `KSeFValidationError` | `VALIDATION_ERROR` | Niepoprawne dane wejściowe SDK, błędny payload odpowiedzi, błędny profil albo błędne argumenty sesji/batch. |
| `KSeFArgumentError` | `ARGUMENT_ERROR` | Wywołanie łączy argumenty niedozwolone przez SDK, na przykład oba albo żaden z `form_code` i `state`. Podklasa `KSeFValidationError` i `TypeError`. |
| `KSeFInvoiceRenderingError` | `INVOICE_RENDERING_ERROR` | Błędy opcjonalnego renderowania XSLT/PDF. |
| `KSeFEncryptionError` | `ENCRYPTION_ERROR` | Błąd szyfrowania tokenu, klucza symetrycznego, faktury albo deszyfrowania. |
| `KSeFSessionError` | `SESSION_ERROR` | Naruszenie stanu sesji, na przykład użycie zamkniętej sesji. Klasa bazowa `KSeFInvoiceRejectedError`. |
| `KSeFInvoiceRejectedError` | `INVOICE_REJECTED` | KSeF zakończył przetwarzanie faktury z sesji interaktywnej i ją odrzucił (`InvoiceSubmission.wait()`). |
| `KSeFExportFailedError` | `EXPORT_FAILED` | KSeF zakończył eksport faktur bez paczki: eksport się nie powiódł, został anulowany przez system albo wygasł (`ExportJob.wait()`). |
| `KSeFPermissionOperationFailedError` | `PERMISSION_OPERATION_FAILED` | KSeF zakończył nadanie albo cofnięcie uprawnienia bez jego zastosowania (`PermissionOperation.wait()`). |
| `KSeFCertificateEnrollmentFailedError` | `CERTIFICATE_ENROLLMENT_FAILED` | KSeF odrzucił, anulował albo nie zrealizował rejestracji certyfikatu (`CertificateEnrollment.wait()`). |
| `KSeFAuthTokenRedemptionError` | `AUTH_TOKEN_REDEMPTION_ERROR` | Jednorazowy redeem uwierzytelnienia utracił odpowiedź i mógł się powieść. |
| `KSeFExternalTransferError` | `EXTERNAL_TRANSFER_ERROR` | Upload lub download przez presigned URL został odrzucony albo utracił odpowiedź. |
| `KSeFBatchUploadError` | `BATCH_UPLOAD_ERROR` | Upload części batch nie powiódł się, ale chroniony stan odzyskiwania pozostaje dostępny. |
| `NoCertificateAvailableError` | `NO_CERTIFICATE_AVAILABLE` | Brak poprawnego certyfikatu dla podpisu albo szyfrowania. |
| `KSeFMetadataPaginationError` | `METADATA_PAGINATION_ERROR` | Paginacja metadanych nie może bezpiecznie kontynuować. |

`KSeFAuthTokenRedemptionError.outcome_ambiguous` ma zawsze wartość `True`. Nie
ponawiaj redeem: KSeF mógł już zużyć tymczasowy token uwierzytelnienia, mimo że
odpowiedź nie dotarła do wywołującego.

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
`BatchSessionResumeState` potrzebny do odzyskania workflow. Stan nie trafia do
komunikatu ani `context`, ponieważ zawiera materiał szyfrujący i presigned URL-e.
Zapisuj go wyłącznie w chronionym magazynie danych uwierzytelniających i nie
ponawiaj automatycznie uploadu, gdy `outcome_ambiguous` ma wartość `True`.

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
pusta odpowiedź):

```text
KSeF rejected <METODA> <ścieżka> (HTTP <status>, KSeF code <kod>): <opis>
Details: <szczegół>; <szczegół>
Trace ID: <identyfikator śledzenia>
Hint: <wskazówka>
```

Fragment `KSeF code` jest pomijany, gdy odpowiedź nie ma kodu, a linie `Details`,
`Trace ID` i `Hint` pojawiają się tylko wtedy, gdy jest co pokazać. Treść
odpowiedzi nie wchodzi do komunikatu; zostaje w `response`. Gdy treść nie jest
rozpoznawalnym błędem, opisem jest krótki, skrócony fragment tej treści.

Przykład: pobranie UPO faktury, którego KSeF jeszcze nie wystawił:

```text
KSeF rejected GET /sessions/online/S1/invoices/I1/upo (HTTP 400, KSeF code 21178): Nie znaleziono UPO dla podanych kryteriów.
Details: UPO o numerze referencyjnym I1 nie zostało znalezione.
Hint: KSeF has not issued the UPO yet. Wait for processing to finish and request it again: `download_upo()` on a session or an invoice submission waits for processing first.
```

Opis i szczegóły pochodzą z KSeF, a `Hint` z SDK, które pisze wskazówki po
angielsku. Linia `Trace ID` pojawia się, gdy KSeF zwrócił identyfikator
śledzenia (odpowiedzi `application/problem+json`).

## Wskazówki

`KSeFException.hint` mówi, co zrobić dalej. Jest pokazywany w osobnej linii
`Hint:` w `str(exc)` i zapisany w `exc.context["hint"]`. Wskazówka jest ustawiana
tylko wtedy, gdy SDK zna przyczynę, każda wymieniona w niej metoda jest aktualna,
a dla jednego wystąpienia można ją zastąpić, przekazując `hint=...` do wyjątku.

Wskazówki do błędów API pochodzą z jednej tabeli, wyszukiwanej po statusie HTTP i
kodzie KSeF:

| Status HTTP | Kod KSeF | Klasa | Wskazówka |
| --- | --- | --- | --- |
| dowolny | 21165 | `KSeFNotReadyError` | KSeF has processed the invoice but has not made it available yet. Call `download()` with a `timeout` so the SDK keeps polling until it is. |
| dowolny | 21178 | `KSeFNotReadyError` | KSeF has not issued the UPO yet. Wait for processing to finish and request it again: `download_upo()` on a session or an invoice submission waits for processing first. |
| 401 | dowolny | `KSeFAuthError` | KSeF rejected the credentials or the access token. Authenticate again with `client.authentication.with_token()` or `client.authentication.with_xades()`, and check that the token or certificate is valid for this context. |
| 403 | dowolny | `KSeFAuthError` | The authenticated identity is not allowed to do this in the current context. Check the reason in `details`, and grant the missing permission with the permissions client, for example `grant_person()`. |

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
| `KSeFCertificateEnrollmentTimeoutError` | KSeF may still issue the certificate. Call `wait()` on the enrollment again with a larger `timeout`, or check it with `get_enrollment_status()`. |
| `KSeFExportFailedError` | Read `description` and `details` for the reason, then start a new export with `export()`. |
| `KSeFExportTimeoutError` | The export may still finish. Call `wait()` on the export again with a larger `timeout`. After a restart, get the job back with `export(state=...)` using the state saved from `resume_state()`. |
| `KSeFInvoiceDownloadTimeoutError` | KSeF has not made the invoice available yet. Call `download()` again with a larger `timeout`. |
| `KSeFInvoiceProcessingTimeoutError` | KSeF may still accept the invoice. Keep waiting with `submission(reference_number).wait()` on the session, with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `online_session(state=...)`. |
| `KSeFInvoiceQueryTimeoutError` | No invoice matched before the deadline. Call `wait()` again with a larger `timeout`, or check the filters passed to `search()`. |
| `KSeFInvoiceRejectedError` | Read `description` and `details` for the reason, fix the invoice and send it again with `send_invoice()`. |
| `KSeFNotReadyError` | KSeF has not finished preparing this resource. Wait and request it again. |
| `KSeFOnlineSessionTimeoutError` | KSeF may still be processing the session. Call `wait()` on the session again with a larger `timeout`. After a restart, rebuild the session from the state saved with `resume_state()` using `online_session(state=...)`. |
| `KSeFPermissionOperationFailedError` | Read `description` for the reason, fix the request and grant or revoke again. `get_operation_status()` shows the operation's final state. |
| `KSeFPermissionOperationTimeoutError` | The operation may still be applied. Call `wait()` on the operation again with a larger `timeout`, or check it with `get_operation_status()`. |
| `KSeFTokenStatusTimeoutError` | KSeF may still be activating the token. Call `wait()` on the token again with a larger `timeout`, or check it with `get_status()`. |

`KSeFSessionError` nie ma wskazówki na poziomie klasy. SDK ustawia ją tam, gdzie
zna przyczynę: oczekiwanie na sesję, która jest nadal otwarta (najpierw ją
zamknij), oraz sesja, którą KSeF zakończył błędem (sprawdź faktury z błędem).
Odrzucony duplikat (`440`) dostaje własną wskazówkę w `KSeFInvoiceRejectedError`.

## Kody błędów KSeF

`ksef_code` to liczba wysłana przez KSeF. SDK nigdy nie gubi nieznanego kodu.
Tylko `21165` i `21178` mają dedykowaną klasę (`KSeFNotReadyError`); pozostałe to
zwykły `KSeFApiError` z ustawionym `ksef_code`. Poniższe kody pochodzą z
dokumentacji API KSeF.

| Kod KSeF | Znaczenie |
| --- | --- |
| `21001` | Nieczytelna treść. |
| `21111` | Nieprawidłowe wyzwanie autoryzacyjne. |
| `21115` | Nieprawidłowy certyfikat. |
| `21117` | Nieprawidłowy identyfikator podmiotu dla wskazanego typu kontekstu. |
| `21155` | Przekroczono dozwoloną liczbę faktur w sesji. |
| `21157` | Nieprawidłowy rozmiar części pakietu. |
| `21161` | Przekroczono dozwoloną liczbę części pakietu. |
| `21164` | Faktura o podanym identyfikatorze nie istnieje. |
| `21165` | Faktura o podanym numerze KSeF nie jest jeszcze dostępna. `KSeFNotReadyError`. |
| `21166` | Korekta techniczna niedostępna. |
| `21167` | Status faktury nie pozwala na korektę techniczną. |
| `21173` | Brak sesji o wskazanym numerze referencyjnym. |
| `21175` | Wynik zapytania o podanym identyfikatorze nie istnieje. |
| `21178` | Nie znaleziono UPO dla podanych kryteriów. `KSeFNotReadyError`. |
| `21180` | Status sesji nie pozwala na wykonanie operacji. |
| `21181` | Nieprawidłowe żądanie eksportu faktur. |
| `21182` | Osiągnięto limit trwających eksportów. |
| `21183` | Zakres filtrowania wykracza poza dostępny zakres danych. |
| `21184` | Sesja tymczasowo niedostępna. |
| `21205` | Pakiet nie może być pusty. |
| `21208` | Czas oczekiwania na requesty upload lub finish został przekroczony. |
| `21217` | Nieprawidłowe kodowanie znaków. |
| `21301` | Brak autoryzacji. |
| `21304` | Brak uwierzytelnienia. |
| `21308` | Próba wykorzystania metod autoryzacyjnych osoby zmarłej. |
| `21401` | Dokument nie jest zgodny ze schemą (XSD). |
| `21402` | Nieprawidłowy rozmiar pliku. |
| `21403` | Nieprawidłowy skrót pliku. |
| `21405` | Błąd walidacji danych wejściowych. `ExceptionCode.VALIDATION_ERROR`. |
| `21406` | Konflikt podpisu i typu uwierzytelnienia. |
| `21418` | Przekazany token kontynuacji jest nieprawidłowy. |
| `21470` | Identyfikator klucza jest nieznany lub wskazuje na wycofany klucz. |
| `25001` | Brak możliwości pobrania danych do CSR dla wykorzystanego sposobu uwierzytelnienia. |
| `25002` | Brak możliwości złożenia wniosku certyfikacyjnego dla wykorzystanego sposobu uwierzytelnienia. |
| `25003` | Dane w CSR nie zgadzają się z danymi w użytym wektorze uwierzytelniającym. |
| `25004` | Niepoprawny format CSR lub niepoprawny podpis CSR. |
| `25005` | Wniosek certyfikacyjny o podanym numerze referencyjnym nie istnieje. |
| `25006` | Osiągnięto limit możliwych do złożenia wniosków certyfikacyjnych. |
| `25007` | Osiągnięto limit dopuszczalnej liczby posiadanych certyfikatów. |
| `25008` | Certyfikat o podanym numerze seryjnym nie istnieje. |
| `25009` | Nie można odwołać wskazanego certyfikatu, ponieważ jest już odwołany, zablokowany lub nieważny. |
| `25010` | Nieprawidłowy typ lub długość klucza. |
| `25011` | Nieprawidłowy algorytm podpisu CSR. |
| `26001` | Nie można nadać tokenowi uprawnień, których nie posiadasz. |
| `26002` | Nie można wygenerować tokena dla obecnego typu kontekstu. |
| `30001` | Podmiot lub uprawnienie już istnieje. `ExceptionCode.OBJECT_ALREADY_EXISTS`. |
| `71001` | Faktura o podanym identyfikatorze nie istnieje. |
| `71002` | Faktura jest już przypisana do maksymalnej liczby identyfikatorów zbiorczych. |
| `71004` | Faktury mają różnych sprzedawców. |
| `71005` | Powtórzony numer KSeF w żądaniu. |

## Wartości ExceptionCode

| Nazwa | Wartość |
| --- | --- |
| `UNKNOWN_ERROR` | `10000` |
| `OBJECT_ALREADY_EXISTS` | `30001` |
| `VALIDATION_ERROR` | `21405` |
| `UPO_NOT_FOUND` | `21178` |
| `NOT_PROCESSED_YET` | `21165` |

Nieznane numeryczne kody KSeF mapują się do `ExceptionCode.UNKNOWN_ERROR`, ale
surowa liczba zostaje w `ksef_code`. W nowym kodzie preferuj `ksef_code`.

## Klasy timeoutów pollingu

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

Zapisz właściwą referencję przed pollingiem, aby inny proces mógł wznowić
sprawdzanie statusu. Każdy błąd timeoutu niesie `hint`, który mówi, jak czekać
dalej albo wznowić pracę.

`download_upo()` na handle faktury, sesji interaktywnej i sesji batch czeka, aż
KSeF zakończy przetwarzanie, i dopiero potem pobiera, więc nie kończy się
`KSeFNotReadyError` ani błędem sesji tylko dlatego, że zostało wywołane za
wcześnie. Przyjmuje `timeout` i `poll_interval` jak `wait()` i rzuca te same
błędy timeoutu i niepowodzenia.

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
odpowiedzią, może przekazać `originalKsefNumber` do `download_invoice()` i
porównać pobraną fakturę z wysłaną. Jeśli to ta sama faktura, może uznać ją za
już przyjętą.

## Powiązana referencja

- [Referencja operacji](operations.md): Sprawdź retry, rate limit, timeouty workflow i wznawialny stan.
- [Cykl życia klienta](client-lifecycle.md): Sprawdź błędy lifecycle i zamykanie klientów.
- [Status i UPO](../concepts/status-and-upo.md): Zrozum statusy, dokumenty UPO i deadline'y pollingu.
