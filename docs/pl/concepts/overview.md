---
title: Jak działa SDK
description: Główne obiekty SDK, granice przepływów KSeF i słownik pojęć używanych w dokumentacji.
---

ksef2 opiera się na kilku długo żyjących obiektach SDK i krótkich przepływach
KSeF. Klient bazowy `Client` albo `AsyncClient` wybiera środowisko i trzyma
konfigurację transportu. Po uwierzytelnieniu powstaje klient uwierzytelniony dla
jednego kontekstu podatnika. Sesje otwierasz tylko wtedy, gdy KSeF wymaga pracy
w ramach sesji.

Użyj tej sekcji, gdy chcesz zrozumieć kształt przepływu KSeF przed pisaniem
kodu. Użyj przewodników praktycznych, gdy znasz już zadanie i potrzebujesz
konkretnych wywołań SDK.

**Zobacz też:**

- [Podstawy](clients-and-lifecycle.md): Klient bazowy, klient uwierzytelniony, środowiska i zasada własności zasobów.
- [Uwierzytelnianie i bezpieczeństwo](authentication-methods.md): Zrozum kontekst logowania, podmiot uwierzytelniający, certyfikaty, szyfrowanie i XAdES.
- [Przepływy faktur](invoice-lifecycle.md): Przejdź przez sesje, przetwarzanie faktur, UPO, zapytania metadanych, pobieranie i eksporty.
- [Administracja](permissions.md): Zrozum tokeny, operacje uprawnień, certyfikaty, limity i wyszukiwanie PEPPOL.

:::note[Najpierw pojęcia, potem kod]
Strony koncepcyjne wyjaśniają nazwy, granice i decyzje. Przewodniki
praktyczne pokazują uruchamialne wywołania dla konfiguracji, uwierzytelniania,
wysyłania faktur, zapytań, pobierania i administracji.
:::

## Jak SDK odwzorowuje oficjalne API

Oficjalna dokumentacja API KSeF grupuje pracę w obszary: dostęp, wysyłka
interaktywna, wysyłka wsadowa, status i UPO, pobieranie faktur, tokeny,
uprawnienia, certyfikaty, limity, publiczne certyfikaty szyfrowania i PEPPOL.
SDK zachowuje te granice pojęciowe i udostępnia je jako moduły klienta bazowego
albo klienta uwierzytelnionego.

| Obszar oficjalnego API | Widok w SDK |
| --- | --- |
| Dostęp | `client.authentication` tworzy klienta uwierzytelnionego dla jednego kontekstu. |
| Wysyłka interaktywna i wsadowa | `auth.online_session()` i `auth.batch_session()` posiadają stan sesji wysyłki. |
| Status i UPO | Klienci sesji oraz `auth.invoice_sessions` sprawdzają zdalne przetwarzanie i potwierdzenia. |
| Pobieranie faktur | `auth.invoices` odpowiada za zapytania metadanych, eksporty, bezpośrednie pobieranie i paczki. |
| Tokeny, uprawnienia, certyfikaty, limity | Moduły administracyjne klienta uwierzytelnionego. |
| Dane publiczne | Moduły klienta bazowego: `client.encryption`, `client.peppol` i dane TEST. |

Moduł niskopoziomowy `raw` służy do własnej obsługi protokołu, diagnostyki i
debugowania ładunków KSeF. Jest publiczny, ale nie jest typowym punktem startu
dla kodu aplikacji.

:::note[Zacznij od modułów wysokiego poziomu]
Większość kodu aplikacyjnego powinna zaczynać od `client.authentication`, a
potem korzystać z modułów uwierzytelnionych: `auth.invoices`,
`auth.online_session()` albo `auth.batch_session()`. Modułu `raw` używaj tylko
wtedy, gdy potrzebujesz kontroli na poziomie protokołu.
:::

## Główne pojęcia

| Pojęcie | Znaczenie w SDK |
| --- | --- |
| Klient bazowy | Nieuwierzytelniony klient ze środowiskiem i transportem HTTP. |
| Klient uwierzytelniony | Obiekt powiązany z tokenami dostępu i odświeżania KSeF dla jednego kontekstu. |
| Sesja online | Krótko żyjący kontekst wysyłki pojedynczych zaszyfrowanych faktur. |
| Sesja wsadowa | Krótko żyjący kontekst wysyłki przygotowanych zaszyfrowanych paczek wsadowych. |
| Moduł faktur | Uwierzytelniony moduł do metadanych, eksportów, pobierania pojedynczych faktur i paczek eksportu. |
| Numer referencyjny | Uchwyt zwracany przez KSeF dla sesji, faktur, eksportów, tokenów, uprawnień i innych prac asynchronicznych. |
| Numer KSeF | Identyfikator nadawany po przyjęciu i przetworzeniu faktury przez KSeF. |
| UPO | Urzędowe potwierdzenie dostępne po osiągnięciu wymaganego stanu przetworzenia przez sesję albo fakturę. |

## Co należy gdzie

Użyj klienta bazowego do publicznych zapytań i konfiguracji:

- `client.authentication`, aby rozpocząć uwierzytelnianie.
- `client.encryption`, aby sprawdzić publiczne certyfikaty szyfrowania.
- `client.peppol`, aby wyszukiwać publiczne dane dostawców PEPPOL.
- `client.testdata` tylko w `Environment.TEST`.

Użyj klienta uwierzytelnionego dla pracy zależnej od kontekstu:

- `auth.online_session()` i `auth.batch_session()` dla wysyłki.
- `auth.invoices` dla metadanych, eksportów i pobierania.
- `auth.tokens`, `auth.permissions`, `auth.certificates` i `auth.limits` dla przepływów administracyjnych.
- `auth.sessions` i `auth.invoice_sessions` dla zarządzania sesjami i historii.

## Powiązane strony

- [Środowiska](environments.md): Wybierz TEST, DEMO albo PRODUCTION i trzymaj stan w granicach tego środowiska.
- [Model klientów](clients-and-lifecycle.md): Klient bazowy, klient uwierzytelniony, sesje i uchwyty eksportu.
- [Metody uwierzytelniania](authentication-methods.md): Wybierz token, XAdES, certyfikat TEST albo uwierzytelnianie przez profil.
- [Sesje](sessions.md): Zrozum sesje online, wsadowe, uwierzytelniania i historyczne sesje faktur.
- [Faktura w KSeF](invoice-lifecycle.md): Od wysyłki XML przez przetwarzanie po numer KSeF, pobranie i UPO.
- [API klientów i usług](../reference/api/client-surface.md): Użyj wygenerowanej referencji API, gdy potrzebujesz pełnej listy obiektów i metod.
- [Oficjalny przewodnik API KSeF](https://github.com/CIRFMF/ksef-api): Dokumentacja źródłowa dla pojęć API KSeF 2.0.
