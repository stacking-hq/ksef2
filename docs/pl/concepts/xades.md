---
title: XAdES
description: Zrozum krok podpisu XML używany przez uwierzytelnianie KSeF oparte o certyfikat.
---

XAdES to format podpisu XML używany, gdy uwierzytelnianie KSeF opiera się o
certyfikat. W SDK XAdES należy do uwierzytelniania: podpisuje
`AuthTokenRequest` zbudowany z challenge KSeF i kontekstu logowania.

Nie jest schematem XML faktury, szyfrowaniem sesji ani formatem paczki eksportu.

## Co potwierdza XAdES

Podczas uwierzytelniania XAdES KSeF sprawdza podpisany dokument XML i certyfikat
osadzony w podpisie. Kontekstem logowania jest NIP przekazany do metody SDK.
Podmiot uwierzytelniający jest odczytywany z certyfikatu podpisującego, na
przykład:

- kwalifikowanego certyfikatu osoby fizycznej zawierającego PESEL albo NIP;
- kwalifikowanej pieczęci organizacji zawierającej NIP;
- certyfikatu KSeF do uwierzytelniania;
- certyfikatu rozpoznawanego przez uprawnienia na odcisk palca;
- materiału certyfikatu samopodpisanego tylko dla TEST.

Następnie KSeF sprawdza, czy ten podmiot może działać w żądanym kontekście.

## Warstwy SDK

Większość aplikacji powinna używać `with_xades()` albo profilu, który wybiera tę
metodę:

```python
auth = client.authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=private_key,
)
```

Helper obsługuje zwykłą sekwencję:

1. Pobierz challenge uwierzytelniania.
2. Zbuduj XML `AuthTokenRequest` dla kontekstu.
3. Podpisz XML przez XAdES.
4. Wyślij podpisany XML do KSeF.
5. Odpytuj operację uwierzytelniania.
6. Odbierz access i refresh tokeny.

Używaj `ksef2.xades` bezpośrednio, gdy musisz samodzielnie załadować materiał
certyfikatu, obejrzeć podpisany XML albo przetestować granicę low-level
integracji.

:::tip[Granica zewnętrznego podpisu]
Jeśli inny system podpisuje XML, a Python ma tylko wysłać wynik albo odebrać
tokeny, użyj low-level endpointów uwierzytelniania i powiąż pobrane tokeny
przez
`client.authentication.resume(AuthenticationResumeState.from_tokens(auth_tokens))`.
:::

## Certyfikaty TEST

SDK potrafi wygenerować materiał samopodpisanego certyfikatu tylko dla TEST
przez `with_test_certificate()` albo niskopoziomowe helpery w `ksef2.xades`. To
skrót developerski dla `Environment.TEST`; nie działa w DEMO ani PRODUKCJI.

## Powiązane strony

- [Metody uwierzytelniania](authentication-methods.md): Zobacz XAdES obok uwierzytelniania tokenem, certyfikatem TEST i profilem.
- [Użyj pomocników XAdES](../how-to-guides/use-xades-helpers.md): Załaduj materiał certyfikatu i podpisz XML uwierzytelniający w kodzie.
- [Certyfikaty](certificates.md): Zrozum tożsamość certyfikatu, rejestrację i typy wydanych certyfikatów.
- [Low-level uwierzytelnianie](../reference/low-level/authentication.md): Wykonaj uwierzytelnianie ręcznie, gdy podpis jest obsługiwany poza wysokopoziomowym helperem SDK.
