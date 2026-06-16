---
title: Uwierzytelnianie
description: XAdES, token KSeF i odświeżanie tokenów.
---

SDK udostępnia uwierzytelnianie przez `Client.authentication` oraz
`AsyncClient.authentication`.

## XAdES

TEST akceptuje certyfikaty generowane przez SDK:

```python
from ksef2 import Client, Environment

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip="5261040828")
```

DEMO i PRODUKCJA wymagają certyfikatu z MCU:

```python
from ksef2 import Client, Environment
from ksef2.core.xades import load_certificate_from_pem, load_private_key_from_pem

cert = load_certificate_from_pem("1234567890.pem")
key = load_private_key_from_pem("1234567890.key")

auth = Client(Environment.DEMO).authentication.with_xades(
    nip="1234567890",
    cert=cert,
    private_key=key,
    timeout=60.0,
)
```

## Token KSeF

```python
from ksef2 import Client

auth = Client().authentication.with_token(
    ksef_token="your-ksef-token",
    nip="5261040828",
    timeout=60.0,
)
```

## Odświeżanie

```python
refreshed = client.authentication.refresh(refresh_token=auth.refresh_token)
print(refreshed.access_token.token)
```

`refresh()` zwraca `RefreshedToken`, a nie nowy `AuthenticatedClient`.

## Sesje uwierzytelniania

```python
for page in auth.sessions.all(page_size=10):
    print(len(page.items))

auth.sessions.terminate_current()
```

## Powiązane

- [Sesje](sessions.md)
- [Tokeny](tokens.md)
- [Dane TEST](testdata.md)
