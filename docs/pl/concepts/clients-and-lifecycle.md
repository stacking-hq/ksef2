---
title: Model klientów
description: Klient bazowy, klient uwierzytelniony, uchwyty sesji i zasada własności zasobów w ksef2.
---

SDK ma niewielką hierarchię obiektów. Każdy obiekt oznacza inną granicę
zarządzania zasobami, a nie tylko inną przestrzeń nazw.

```text
Client albo AsyncClient
  -> publiczne moduły klienta bazowego
  -> authentication
    -> AuthenticatedClient dla jednego kontekstu KSeF
      -> sesje, faktury, tokeny, uprawnienia, certyfikaty, limity
        -> sesja online, sesja batch, uchwyt eksportu
```

Klient bazowy wybiera środowisko KSeF i trzyma zasoby transportu. Klient
uwierzytelniony niesie dostęp do jednego kontekstu. Klienci sesji i uchwyty
eksportu to węższe obiekty jednego przepływu — nie używaj ich jako ogólnego
wejścia do SDK.

## Model obiektów

| Obiekt | Co posiada | Co można użyć ponownie |
| --- | --- | --- |
| `Client` / `AsyncClient` | Środowisko, transport HTTP, retry, TLS/proxy i cache publicznych certyfikatów. | Użyj ponownie, gdy operacje mają to samo środowisko i politykę transportu. |
| Klient uwierzytelniony | Tokeny dostępu i odświeżania dla jednego kontekstu logowania. | Użyj ponownie, gdy operacje należą do tego samego kontekstu podatnika i stanu credentiali. |
| Klient sesji online | Jeden zdalny numer referencyjny sesji online oraz materiał szyfrowania sesji. | Użyj dla jednego przepływu wysyłki, potem zamknij sesję. |
| Klient albo stan sesji batch | Jeden przepływ uploadu batch oraz materiał szyfrowania paczki. | Użyj do uploadu, zamknięcia, pollingu statusu i pobrania UPO. |
| Uchwyt eksportu | Numer referencyjny eksportu oraz lokalny materiał AES potrzebny do odszyfrowania części paczki. | Trzymaj tylko do czasu pobrania i zapisania paczki eksportu. |

Główna zasada jest prosta: ponownie używaj klientów bazowych i uwierzytelnionych,
gdy środowisko i kontekst się zgadzają; sesje i eksporty traktuj jako uchwyty
jednego przepływu.

## Klient bazowy

Klient bazowy jest granicą zasobów HTTP zarządzanych przez SDK. Udostępnia
publiczne moduły bez uwierzytelnienia — na przykład odczyt certyfikatów
szyfrowania i dostawców PEPPOL. Udostępnia też `authentication`, czyli wejście
do uwierzytelnionego kontekstu KSeF.

Twórz klienta bazowego dla jednego środowiska: TEST, DEMO albo PRODUCTION. Nie
przełączaj jednego klienta między środowiskami. Jeżeli aplikacja łączy się z
więcej niż jednym środowiskiem, każde powinno mieć osobnego klienta bazowego.

Zamknięcie klienta bazowego zwalnia zasoby HTTP, gdy należą one do SDK. Jeżeli
przekazujesz własnego klienta `httpx`, aplikacja nadal odpowiada za jego
zamknięcie.

## Klienci uwierzytelnieni

Uwierzytelnienie tworzy klienta uwierzytelnionego dla jednego kontekstu KSeF.
Kontekst to zwykle NIP podatnika plus credential potwierdzający prawo działania
w tym kontekście.

Klient uwierzytelniony udostępnia moduły chronione:

| Moduł | Rodzaj przepływu |
| --- | --- |
| `online_session` | Interaktywna wysyłka faktur. |
| `batch` | Przygotowanie, upload, status i UPO paczki batch. |
| `invoices` | Metadane, bezpośrednie pobrania, eksporty i pobieranie paczek eksportu. |
| `tokens` | Generowanie, lista, status i unieważnianie tokenów KSeF. |
| `permissions` | Nadawanie, zapytania, cofanie i status operacji uprawnień. |
| `certificates` | Enrollment, pobieranie, limity i unieważnianie certyfikatów KSeF. |
| `limits` | Odczyt albo zmiana limitów kontekstu, podmiotu i API. |
| `sessions` / `invoice_sessions` | Inspekcja sesji uwierzytelnienia i sesji faktur. |

Klienta uwierzytelnionego można używać ponownie między funkcjami workflow, gdy
należą do tego samego kontekstu KSeF. Przekazywanie go do kodu przepływu trzyma
setup transportu i credentiali poza logiką operacji biznesowej.

## Uchwyty sesji

Klienci sesji online i batch nie są ogólnymi klientami uwierzytelnionymi. Są
uchwytami do jednej zdalnej referencji sesji KSeF i lokalnego materiału
szyfrowania używanego przez tę sesję.

Sesja online powinna zostać zamknięta, gdy nie będą wysyłane kolejne faktury.
Zamknięcie sesji mówi KSeF, że etap wysyłki jest zakończony i pozwala przejść
do finalnego statusu oraz dostępności UPO.

Przepływ batch też ma granicę zamknięcia. KSeF zaczyna przetwarzanie dopiero po
wysłaniu zaszyfrowanych części paczki i zamknięciu sesji batch.

:::caution[Referencje żyją dłużej niż obiekty Pythona]
Obiekt sesji w Pythonie może zniknąć, gdy KSeF nadal przetwarza dane. Zapisz
numer referencyjny sesji, referencje faktur, numery KSeF i referencje UPO
potrzebne do późniejszego wznowienia statusu.
:::

## Sync i async

`Client` i `AsyncClient` udostępniają ten sam model modułów. Klient async zmienia
styl wywołań: operacje sieciowe używają `await`, a granice cyklu życia używają
async context managerów. Nie zmienia to modelu workflow KSeF.

Wybierz klienta sync dla skryptów, narzędzi CLI, synchronicznych workerów i
aplikacji, które nie mają własnej pętli zdarzeń. Wybierz klienta async, gdy
aplikacja już jest asynchroniczna, na przykład async web service albo async
worker.

## Co zapisywać

Nie zapisuj klientów głównych, klientów uwierzytelnionych ani obiektów sesji.
Zapisuj identyfikatory i artefakty:

- środowisko i nazwę profilu;
- identyfikator kontekstu logowania;
- numer referencyjny sesji;
- numer referencyjny faktury;
- numer KSeF;
- referencję eksportu i chroniony materiał uchwytu eksportu, dopóki eksport
  jest pobierany;
- bajty XML UPO albo miejsce ich zapisu;
- ostatni zaobserwowany status dla supportu i audytu.

Obiekty klientów są zasobami procesu. Referencje i artefakty są stanem
aplikacji.

## Powiązane strony

- [Skonfiguruj klienta](../how-to-guides/client-setup.md): Utwórz klienty sync i async oraz ustaw granice cyklu życia w kodzie.
- [Metody uwierzytelniania](authentication-methods.md): Wybierz token, XAdES, certyfikat TEST albo uwierzytelnianie profilem.
- [Sesje](sessions.md): Zrozum sesje online, batch, stan sesji i historię sesji.
- [Referencja cyklu życia klienta](../reference/client-lifecycle.md): Sprawdź kontrakt własności klienta i zamykania zasobów.
