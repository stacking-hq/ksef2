---
title: Przegląd
description: Punkt startowy polskiej dokumentacji ksef2 SDK.
---

ksef2 to SDK Pythona dla API KSeF v2. Udostępnia klientów sync i async,
typowane modele żądań, pomocniki sesji faktur i low-level dostęp do endpointów.

> **Nieoficjalne SDK.** ksef2 jest społecznościowo utrzymywanym SDK dla
> Pythona. Nie jest publikowane, zatwierdzane ani wspierane przez Ministerstwo
> Finansów. Oficjalna dokumentacja KSeF pozostaje źródłem prawdy dla zachowania
> API.

## Start

- [Quickstart](getting-started/quickstart.md)
- [Wybierz przepływ uwierzytelniania](workflows/authentication.mdx)
- [Wyślij, znajdź i pobierz faktury](workflows/overview.mdx)

## Główne strony

- [Przegląd przepływów](workflows/overview.mdx): ścieżki zadaniowe dla
  klientów, uwierzytelniania, faktur, statusu, tokenów, uprawnień,
  certyfikatów, limitów, publicznych lookupów, danych TEST i XAdES.
- [Konfiguracja klienta](workflows/client-setup.mdx): sync albo async, publiczne
  gałęzie klienta głównego i gałęzie uwierzytelnione.
- [Kontrakt publicznego API](guides/public-api.md): stabilne ścieżki importu i
  granice pakietów internal dla kodu aplikacyjnego.
- [Obsługa błędów](guides/errors.md): łapanie wyjątków SDK, diagnostyka
  odpowiedzi KSeF i timeouty pollingu.
- [Wysyłanie faktur](workflows/sending-invoices.mdx): sesje online albo batch i
  wysyłka XML do KSeF.
- [Przepływy administracyjne](workflows/tokens.mdx): zacznij od tokenów, potem
  używaj uprawnień, certyfikatów i limitów według potrzeb.
- [Low-level API](raw/overview.md): używaj schema-native wrapperów endpointów do
  własnego podpisywania, custody szyfrowania albo debugowania payloadów KSeF.

## Referencja

Użyj [referencji API](reference/api-signatures.md), gdy potrzebujesz sygnatur,
typów zwracanych, nazw modeli albo dokładnych wariantów sync/async.
