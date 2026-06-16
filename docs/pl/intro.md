---
title: Przegląd
description: Punkt startowy polskiej dokumentacji KSeF2 SDK.
---

KSeF2 to SDK dla Pythona do API KSeF v2. Udostępnia typowane klienty sync i
async do uwierzytelniania, sesji faktur, zapytań metadanych, eksportów,
uprawnień, tokenów KSeF, certyfikatów, PEPPOL, danych TEST oraz budowania
faktur FA(3).

> **Nieoficjalne SDK.** KSeF2 jest społecznościowo utrzymywanym SDK dla
> Pythona. Nie jest publikowane, zatwierdzane ani wspierane przez Ministerstwo
> Finansów. Oficjalna dokumentacja KSeF pozostaje źródłem prawdy dla zachowania
> API.

## Zacznij tutaj

- [Instalacja SDK](getting-started/installation.md)
- [Quickstart](getting-started/quickstart.md)
- [Wybór sposobu uwierzytelniania](getting-started/authentication.md)

## Mapa dokumentacji

- **Pierwsze kroki**: instalacja, wybór uwierzytelniania i pierwszy przepływ w
  środowisku TEST.
- **Przewodniki**: konkretne zadania, takie jak wysyłka faktur, eksport,
  zarządzanie tokenami, dane TEST i praca async.
- **Koncepcje**: decyzje projektowe ważne dla użytkownika, szczególnie async
  jako źródło prawdy i generowany klient sync.
- **Reference**: wygenerowana referencja publicznego API, w tym sygnatury,
  stabilne importy, używane modele, publiczne wyjątki, FA(3) i helpery XAdES.

## Wejścia do referencji

- [Referencja API](reference/api-signatures.md): generowane karty źródłowe
  pogrupowane według oficjalnej struktury przepływów API KSeF tam, gdzie SDK
  się z nią mapuje.
- [Generowanie sync](contributing/sync-codegen.md): dlaczego API sync jest
  lustrzanym odbiciem drzewa async.

## Publiczne API

Za publiczne uznajemy:

- `ksef2`
- `ksef2.domain.models`
- `ksef2.fa3`
- `ksef2.core.xades`
- stabilne klasy wyjątków eksportowane z `ksef2`

Moduły endpointów, mapperów, transportu i wygenerowanych schematów są
szczegółami implementacyjnymi, o ile strona referencyjna nie mówi inaczej.
