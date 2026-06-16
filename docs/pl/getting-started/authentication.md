---
title: Uwierzytelnianie
description: Wybór przepływu uwierzytelniania w KSeF2.
---

Każdy przepływ wymagający autoryzacji zaczyna się od `Client.authentication`
albo `AsyncClient.authentication`.

## TEST

W środowisku TEST użyj certyfikatu generowanego przez SDK:

```python
from ksef2 import Client, Environment

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip="5261040828")
```

## DEMO i PRODUKCJA

W środowiskach DEMO i PRODUKCJA użyj certyfikatu z MCU:

```python
from ksef2 import Client, Environment
from ksef2.core.xades import load_certificate_from_pem, load_private_key_from_pem

cert = load_certificate_from_pem("cert.pem")
key = load_private_key_from_pem("cert.key")

auth = Client(Environment.DEMO).authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=key,
    timeout=60.0,
)
```

## Token KSeF

Jeżeli masz już token KSeF dla kontekstu:

```python
auth = Client().authentication.with_token(
    ksef_token="your-ksef-token",
    nip="5261040828",
    timeout=60.0,
)
```

## Async

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
    print(auth.access_token)
```

Pełny opis znajduje się w przewodniku [Uwierzytelnianie](../guides/authentication.md).
