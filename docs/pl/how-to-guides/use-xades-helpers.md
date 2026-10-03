---
title: Podpisy XAdES
description: Ładowanie certyfikatów i kluczy, generowanie certyfikatów TEST i podpisywanie XML do uwierzytelniania KSeF.
---

Użyj pomocników XAdES, gdy uwierzytelniasz się materiałem certyfikatu albo
diagnozujesz podpisany XML uwierzytelniania. Większość aplikacji powinna nadal
wywoływać `client.authentication.with_xades()` zamiast podpisywać ręcznie.

## Załaduj materiał certyfikatu

### Z PEM

```python
import os

from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem

password = os.environ.get("KSEF2_KEY_PASSWORD")

cert = load_certificate_from_pem("company.pem")
private_key = load_private_key_from_pem(
    "company.key",
    password=password.encode() if password else None,
)
```

### Z PKCS#12

```python
import os

from ksef2.xades import load_certificate_and_key_from_p12

password = os.environ.get("KSEF2_P12_PASSWORD")

cert, private_key = load_certificate_and_key_from_p12(
    "company.p12",
    password=password.encode() if password else None,
)
```

## Uwierzytelnij przez XAdES

Przekaż załadowany certyfikat i klucz prywatny do gałęzi uwierzytelniania.

```python
auth = client.authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=private_key,
)
```

## Wygeneruj materiał certyfikatu TEST

Wygenerowanych certyfikatów używaj tylko w przepływach TEST.

### Firma

```python
from ksef2.xades import generate_test_certificate

cert, private_key = generate_test_certificate(nip="5261040828")
```

### Osoba

```python
from ksef2.xades import generate_personal_test_certificate

cert, private_key = generate_personal_test_certificate(
    pesel="90010112345",
    nip="5261040828",
)
```

## Podpisz XML bezpośrednio

Bezpośrednich helperów podpisu używaj do diagnostyki albo niższych testów
integracyjnych. Dla zwykłego uwierzytelniania preferuj `with_xades()`.

```python
from ksef2.xades import build_auth_token_request_xml, sign_xades

xml = build_auth_token_request_xml(
    challenge="challenge-from-ksef",
    nip="5261040828",
)

signed_xml = sign_xades(xml, cert, private_key)
```

:::caution[Chroń klucze prywatne]
Pliki kluczy prywatnych i hasła trzymaj poza kontrolą wersji. Ładuj hasła ze
zmiennych środowiskowych albo managera sekretów i przekazuj do SDK tylko
załadowany obiekt klucza.
:::

## Zalecany przepływ

1. Załaduj materiał certyfikatu z PEM albo PKCS#12.

2. Trzymaj hasła kluczy prywatnych w zmiennych środowiskowych albo managerze
   sekretów.

3. Uwierzytelniaj się przez `with_xades()`, gdy to możliwe.

4. Generuj samopodpisane certyfikaty tylko dla TEST.

5. Używaj bezpośrednich helperów podpisu tylko do diagnostyki albo
   niskopoziomowych testów integracyjnych.

## Następne przepływy

- [Uwierzytelnianie](authenticate.md): Użyj załadowanego materiału certyfikatu XAdES w uwierzytelnianiu SDK.
- [Zarządzaj certyfikatami](manage-certificates.md): Rejestruj, pobieraj i cofaj certyfikaty KSeF.
- [XAdES](../concepts/xades.md): Zrozum, gdzie XAdES pasuje do modelu uwierzytelniania KSeF.
