---
title: Authentication
description: Choose a KSeF2 authentication flow.
---

Every authenticated workflow starts at `Client.authentication` or
`AsyncClient.authentication`.

## TEST

Use the SDK-generated certificate helper in TEST:

```python
from ksef2 import Client, Environment

client = Client(Environment.TEST)
auth = client.authentication.with_test_certificate(nip="5261040828")
```

## DEMO and PRODUCTION

Use an MCU-issued certificate and private key:

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

## KSeF token

Use token authentication when you already have a KSeF token for the target
context:

```python
auth = Client().authentication.with_token(
    ksef_token="your-ksef-token",
    nip="5261040828",
    timeout=60.0,
)
```

## Async shape

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
    print(auth.access_token)
```

For the full authentication guide, see [Authentication](../guides/authentication.md).
