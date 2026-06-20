---
title: Klient
description: Utwórz klienta ksef2, uwierzytelnij się i wybierz sync albo async.
---

Klient główny wybiera środowisko i udostępnia publiczne wejścia SDK. Najpierw
tworzysz klienta, potem uwierzytelniasz się, a następnie korzystasz z gałęzi
`auth`.

## Utwórz klienta

```python
from ksef2 import Client, Environment

client = Client(Environment.TEST)
```

Poza TEST użyj `Environment.DEMO` albo `Environment.PRODUCTION`.

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    ...
```

## Uwierzytelnij się

W TEST możesz użyć certyfikatu generowanego przez SDK.

```python
auth = client.authentication.with_test_certificate(nip="5261040828")
```

DEMO i PRODUCTION wymagają prawdziwego certyfikatu albo istniejącego tokenu
KSeF.

```python
from ksef2.core.xades import load_certificate_from_pem, load_private_key_from_pem

cert = load_certificate_from_pem("company.pem")
key = load_private_key_from_pem("company.key")

auth = Client(Environment.DEMO).authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=key,
)
```

```python
auth = client.authentication.with_token(
    ksef_token="your-ksef-token",
    nip="5261040828",
)
```

## Użyj gałęzi po uwierzytelnieniu

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    ...

invoices = auth.invoices
tokens = auth.tokens
permissions = auth.permissions
certificates = auth.certificates
```

## Błędy

Łap błędy sklasyfikowane przez SDK przez `KSeFException`. Błędy transportu HTTP
łap osobno.

```python
import httpx

from ksef2 import KSeFException

try:
    auth = client.authentication.with_test_certificate(nip="5261040828")
except KSeFException as exc:
    print(exc)
except httpx.HTTPError as exc:
    print(f"Transport failed: {exc}")
```

## Referencja

- [Przepływ uwierzytelniania](../workflows/authentication.mdx)
- [Access API](../reference/api/access.md)
- [Active sessions API](../reference/api/active-sessions.md)
- [Errors reference](../reference/api/errors.md)
