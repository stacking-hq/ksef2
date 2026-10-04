---
title: PEPPOL
description: Zrozum lookup dostawców PEPPOL i jego miejsce w SDK.
---

Lookup dostawców PEPPOL jest publicznym przepływem klienta głównego. Nie wymaga
uwierzytelnionego kontekstu KSeF i sam nie bierze udziału w przetwarzaniu sesji
faktur.

Używaj go jako danych referencyjnych: do wypełniania wyboru dostawcy, walidacji
identyfikatorów dostawców albo odświeżania lokalnego cache dostawców. Trzymaj
go osobno od wysyłki faktur, zapytań o metadane KSeF, eksportów i statusu UPO.

:::note[Tylko publiczny lookup]
Lookup PEPPOL nie potwierdza doręczenia, akceptacji KSeF ani stanu
przetwarzania sesji. Odczytuje tylko dane dostawców zarejestrowane w KSeF.
:::

## Gdzie znajduje się w SDK

PEPPOL jest wystawiony na kliencie głównym obok innych publicznych gałęzi:

```python
for provider in client.peppol.list():
    print(provider.id, provider.name)
```

`list()` zwraca `Pager` po stronicowanej odpowiedzi: iteracja sama przechodzi po
stronach, `.pages()` zwraca po jednej liście na stronę, a `.first_page()`
wykonuje pojedyncze żądanie.

```python
providers_by_id = {
    provider.id: provider.name
    for provider in client.peppol.list()
}
```

## Granica produktu

Rekordy dostawców są danymi referencyjnymi produktu. Cacheuj identyfikatory i
nazwy dostawców zgodnie z wymaganiami świeżości danych, a cache odświeżaj
niezależnie od uwierzytelnionych workerów faktur.

Łącz ten lookup z przepływami faktur tylko wtedy, gdy Twój produkt ma własny
krok PEPPOL, na przykład wybór identyfikatora dostawcy przez użytkownika przed
budową payloadu specyficznego dla integracji.

## Powiązane strony

- [Wyszukaj dostawców PEPPOL](../how-to-guides/query-peppol-providers.md): Pobierz jedną stronę albo przejdź przez wszystkich dostawców PEPPOL w kodzie SDK.
- [Przegląd SDK](overview.md): Zobacz PEPPOL wśród gałęzi klienta głównego.
- [Skonfiguruj klienta](../how-to-guides/client-setup.md): Utwórz klienta głównego używanego do publicznego lookupu dostawców.
