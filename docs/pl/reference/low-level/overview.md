---
title: API niskiego poziomu
description: Wrappery endpointów zgodne ze schematem, przestrzenie nazw modeli raw i narzędzia niskopoziomowe.
---

API niskiego poziomu to powierzchnia SDK dla kontroli na poziomie endpointów bez
wychodzenia poza transport biblioteki. Jest dostępne przez `client.raw` przed
uwierzytelnieniem i `auth.raw` po uwierzytelnieniu.

Użyj go, gdy integracja wymaga własnego podpisywania, własnej obsługi
szyfrowania, dokładnych payloadów OpenAPI albo debugowania endpointów. Większość
aplikacji nadal powinna zaczynać od klientów wysokiego poziomu.

## Kontrakt

| Właściwość | Zachowanie low-level |
| --- | --- |
| Transport | Ten sam stos middleware, retry, sprawdzenia cyklu życia i mapowanie wyjątków co klient bazowy. |
| Uwierzytelnienie | `client.raw` jest nieuwierzytelnione; `auth.raw` używa bearer transportu tam, gdzie wymaga tego KSeF. |
| Modele | Żądania i odpowiedzi używają nazw ze schematu KSeF/OpenAPI, np. `referenceNumber`, `publicKeyId`, `authenticationToken`. |
| Parsowanie | Poprawne odpowiedzi JSON trafiają do wygenerowanych modeli `spec` albo uzupełniających `supp`. |
| Odpowiedzi binarne | XML faktur i UPO zwracane jako `bytes`. |
| Async | Klient async ma te same moduły i nazwy metod; wywołania sieciowe używają `await`. |

## Przestrzenie nazw modeli

Modele low-level importuj ze wspieranego `ksef2.raw`, nie z wewnętrznych
pakietów wygenerowanych:

```python
from ksef2.raw import spec, supp
```

| Namespace | Do czego służy |
| --- | --- |
| `spec` | Wygenerowane modele żądań i odpowiedzi OpenAPI. |
| `supp` | Modele supplemental używane tam, gdzie wygenerowany kształt OpenAPI wymaga wsparcia SDK. |
| `ksef2.raw.mappers` | Jawne mosty z modeli schema-native do publicznych modeli SDK. |

## Eksportowane utility

| Export | Do czego służy |
| --- | --- |
| `encrypt_token` | Szyfrowanie payloadów uwierzytelniania tokenem KSeF. |
| `generate_session_key` | Generowanie klucza AES i IV dla szyfrowania sesji, faktur albo eksportu. |
| `encrypt_symmetric_key` | Szyfrowanie lokalnego materiału AES publicznym certyfikatem KSeF. |
| `encrypt_invoice` | Szyfrowanie bajtów XML faktury dla low-level wysyłki online. |
| `sha256_b64` | Obliczanie base64 SHA-256 dla metadanych payloadów low-level. |
| `prepare_batch_package` | Budowanie zaszyfrowanej paczki batch, gdy caller prowadzi low-level batch flow. |

## Poziomy kontroli

| Poziom | Co posiada SDK | Co posiada caller | Typowe wejście |
| --- | --- | --- | --- |
| Workflow | Kolejność endpointów, szyfrowanie, polling i mapowanie modeli. | Dane biznesowe i persystencja. | `auth.invoices`, `auth.batch`, klienci sesji. |
| Step-level | Szczegóły protokołu dla jednego kroku workflow SDK. | Kolejność i zapis stanu między krokami. | `session.send_invoice()`, `submission.wait()`. |
| Low-level | Transport, parsowanie odpowiedzi, mapowanie wyjątków. | Kolejność endpointów, payloady ze schematu, obsługa szyfrowania, polling. | `client.raw`, `auth.raw`. |

Główna zasada dotyczy właściciela sesji: jeśli low-level kod otwiera sesję, ten
sam poziom zwykle powinien ją zamknąć i sprawdzać. Jeśli wysoki poziom otwiera
sesję, używaj zwróconego klienta sesji.

## Sekcja low-level

- [Uwierzytelnianie niskiego poziomu](authentication.md): Sprawdź endpointy auth raw oraz sekwencję wiązania token/XAdES.
- [Sesje i faktury niskiego poziomu](sessions-invoices.md): Sprawdź metody endpointów sesji, faktur, UPO i eksportu.
- [Mapa endpointów](endpoint-map.md): Znajdź moduł raw i grupę metod dla danego obszaru KSeF.
