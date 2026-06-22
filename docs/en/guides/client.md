---
title: Client
description: Create a ksef2 client, authenticate, and choose sync or async usage.
---

The root client owns transport configuration and exposes the public SDK entry
points. Create one client for the target KSeF environment, authenticate, then
use the authenticated branches for invoices, sessions, tokens, permissions, and
certificates.

## Create a client

```python
from ksef2 import Client, Environment

client = Client(Environment.TEST)
```

Use `Environment.DEMO` or `Environment.PRODUCTION` outside local TEST workflows.

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    ...
```

## Authenticate

TEST can use an SDK-generated certificate.

```python
auth = client.authentication.with_test_certificate(nip="5261040828")
```

DEMO and PRODUCTION require a real certificate or an existing KSeF token.

```python
from ksef2.xades import load_certificate_from_pem, load_private_key_from_pem

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

## Use authenticated branches

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    ...

invoices = auth.invoices
tokens = auth.tokens
permissions = auth.permissions
certificates = auth.certificates
```

Async code uses the same names and awaits network calls.

```python
async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
    async with auth.online_session(form_code=FormSchema.FA3) as session:
        ...
```

## Handle errors

Catch SDK-classified failures with `KSeFException`. Catch `httpx.HTTPError`
separately for transport failures before KSeF returns a response.

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

Common specialized SDK exceptions include `KSeFAuthError`,
`KSeFRateLimitError`, `KSeFValidationError`, and `KSeFClientClosedError`.

## Reference

- [Authentication workflow](../workflows/authentication.mdx)
- [Public API contract](public-api.md)
- [Error handling](errors.md)
- [Low-level API](../raw/overview.md)
- [Access API](../reference/api/access.md)
- [Active sessions API](../reference/api/active-sessions.md)
- [Errors reference](../reference/api/errors.md)
