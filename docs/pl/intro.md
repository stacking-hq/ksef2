---
title: Przegląd
description: Punkt startowy polskiej dokumentacji ksef2 SDK.
---

ksef2 to SDK Pythona dla API KSeF v2. Udostępnia klientów sync i async,
typowane modele żądań, pomocniki sesji faktur i builder faktur FA(3).

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
- [Budowanie faktur](workflows/building-invoices.mdx): budowanie XML faktury w
  Pythonie.
- [Wysyłanie faktur](workflows/sending-invoices.mdx): sesje online albo batch i
  wysyłka XML do KSeF.
- [Przepływy administracyjne](workflows/tokens.mdx): zacznij od tokenów, potem
  używaj uprawnień, certyfikatów i limitów według potrzeb.

## Referencja

Użyj [referencji API](reference/api-signatures.md), gdy potrzebujesz sygnatur,
typów zwracanych, nazw modeli albo dokładnych wariantów sync/async.
