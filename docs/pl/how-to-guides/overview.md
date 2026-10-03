---
title: Spis poradników
description: Wybierz poradnik do konkretnego zadania na publicznej powierzchni SDK.
---

Ta sekcja jest dla sytuacji, w których znasz już ogólny kształt SDK i chcesz
wykonać konkretne zadanie w KSeF. Szybki start pokazuje jedną ścieżkę od początku
do końca; poniższe poradniki rozbijają typowe decyzje produkcyjne.

## Konfiguracja

- [Konfiguracja klienta](client-setup.md): Sync albo async, publiczne moduły klienta bazowego i moduły po uwierzytelnieniu.
- [Uwierzytelnij się](authenticate.md): Wybierz certyfikat TEST, token KSeF, certyfikat XAdES, zmienne środowiskowe albo profile kompatybilne z CLI.
- [Użyj profili](profiles.md): Współdziel lokalną konfigurację ksef2-cli z uwierzytelnianiem SDK i ProfileStore.

## Faktury

- [Zbuduj faktury FA(3)](build-fa3-invoices.md): Wygeneruj prosty publiczny model faktury i XML FA(3) do wysyłki przez fluent builder.
- [Wyślij faktury](send-invoices.md): Wyślij XML FA(3) przez sesję online albo sesję wsadową i sprawdź wynik przetwarzania.
- [Sprawdź status i UPO](get-status-and-upo.md): Odpytuj status online albo batch, listuj faktury sesji i pobieraj dokumenty UPO.
- [Wyszukaj faktury](query-invoices.md): Zbuduj filtry metadanych, przejdź po stronach wyników i czekaj na widoczność nowych faktur.
- [Pobierz faktury](download-invoices.md): Pobierz jedną fakturę po numerze KSeF albo zaplanuj szyfrowany eksport paczek.

## Administracja

- [Zarządzaj tokenami](manage-tokens.md): Generuj, listuj, sprawdzaj i cofaj tokeny KSeF dla automatyzacji.
- [Zarządzaj uprawnieniami](configure-permissions.md): Nadawaj, wyszukuj, odbieraj i monitoruj uprawnienia KSeF.
- [Zarządzaj certyfikatami](manage-certificates.md): Sprawdzaj limity, rejestruj certyfikaty, pobieraj wydane materiały i cofaj certyfikaty.
- [Zarządzaj limitami](manage-limits.md): Odczytuj i nadpisuj limity kontekstu, podmiotu oraz API rate limity.

## Narzędzia pomocnicze

- [Sprawdź certyfikaty szyfrowania](inspect-encryption-certificates.md): Sprawdzaj publiczne certyfikaty KSeF używane w szyfrowanych przepływach faktur i eksportów.
- [Wyszukaj dostawców PEPPOL](query-peppol-providers.md): Wyszukuj publiczne dane dostawców PEPPOL z klienta bazowego.
- [Użyj danych TEST](use-test-data.md): Twórz sandboxowe podmioty, uprawnienia, flagi załączników i fixture'y z temporal cleanup.
- [Użyj pomocników XAdES](use-xades-helpers.md): Ładuj materiał certyfikatu, generuj certyfikaty TEST i podpisuj XML.
- [API niskiego poziomu](../reference/low-level/overview.md): Zejdź do schema-native wrapperów endpointów dla własnego podpisu, custody szyfrowania albo debugowania payloadów.

:::tip[Sync i async mają ten sam przepływ]
Klient async ma te same moduły i nazwy metod. Użyj `AsyncClient`, wywołania
sieciowe poprzedź `await`, a zasoby klienta i sesji zamykaj przez
`async with`.
:::

## Typowa kolejność

1. Skonfiguruj środowisko i dane uwierzytelniające.

   Sekrety trzymaj w zmiennych środowiskowych, a niesekretne ustawienia w
   lokalnej konfiguracji.

2. Uwierzytelnij się dla wybranego kontekstu.

   Uwierzytelniony klient udostępnia `online_session`, `batch`, `invoices`,
   `tokens`, `permissions`, `certificates` i inne moduły przepływów.

3. Uruchom gałąź przepływu, która odpowiada za zadanie.

   Użyj publicznych modułów klienta bazowego do certyfikatów szyfrowania, lookupu
   PEPPOL i danych TEST. Użyj modułów uwierzytelnionych do faktur, sesji,
   tokenów, uprawnień, certyfikatów i limitów.

4. Poczekaj na przetwarzanie w KSeF albo status operacji.

   Pomocniki wysokiego poziomu potrafią odpytywać status faktury, zakończenie
   batcha, operacje uprawnień, rejestrację certyfikatu, widoczność w metadanych
   i gotowość paczki eksportu.

5. Zapisz wynik biznesowy.

   Zapisuj numery KSeF, referencje sesji, referencje operacji, uchwyty
   eksportu, pobrany XML, referencje tokenów, numery seryjne certyfikatów i UPO
   zgodnie z polityką retencji aplikacji.

## Referencja

- [Szybki start](../getting-started/quickstart.md): Uruchom pierwszy przepływ generowania, wysyłki, potwierdzenia i pobrania.
- [Operacje](../reference/operations.md): Mapuj zadania na moduły SDK, pomocniki pollingu i granice ponawiania.
- [Kontrakt publicznego API](../reference/public-api.md): Przejrzyj stabilne importy i publiczne moduły wystawiane przez SDK.
- [Low-level API](../reference/low-level/overview.md): Użyj schema-native wrapperów endpointów, gdy przepływ wysokiego poziomu nie wystarcza.
