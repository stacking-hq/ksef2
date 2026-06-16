---
title: Authentication
description: Authenticate with TEST certificates, XAdES certificates, or KSeF tokens.
---

The SDK exposes authentication through `Client.authentication`.

Async applications use `AsyncClient.authentication` with the same method names;
await the methods that perform network calls.

## XAdES Authentication

TEST accepts SDK-generated self-signed certificates:

```python
from ksef2 import Client, Environment
from ksef2.core.tools import generate_nip

nip = generate_nip()
client = Client(Environment.TEST)

auth = client.authentication.with_test_certificate(nip=nip)

print(auth.access_token)
print(auth.auth_tokens.access_token.valid_until)
```

DEMO and PRODUCTION require an MCU-issued certificate:

```python
from ksef2 import Client, Environment
from ksef2.core.xades import load_certificate_from_pem, load_private_key_from_pem

cert = load_certificate_from_pem("1234567890.pem")
key = load_private_key_from_pem("1234567890.key")

auth = Client(Environment.DEMO).authentication.with_xades(
    nip="1234567890",
    cert=cert,
    private_key=key,
)
```

If you received a `.p12` / `.pfx` archive instead:

```python
from ksef2.core.xades import load_certificate_and_key_from_p12

cert, key = load_certificate_and_key_from_p12("cert.p12", password=b"secret")
```

Examples:
- [`scripts/examples/auth/auth_xades.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/auth/auth_xades.py)
- [`scripts/examples/auth/auth_xades_demo.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/auth/auth_xades_demo.py)

## KSeF Token Authentication

Use `with_token()` when you already have a KSeF token for the target context:

```python
from ksef2 import Client

client = Client()
auth = client.authentication.with_token(
    ksef_token="your-ksef-token",
    nip="5261040828",
)

print(auth.access_token)
print(auth.refresh_token)
```

Example:
- [`scripts/examples/auth/auth_token.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/auth/auth_token.py)

## Async Authentication

```python
from ksef2 import AsyncClient, Environment


async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
    print(auth.access_token)

    refreshed = await client.authentication.refresh(
        refresh_token=auth.refresh_token,
    )
    print(refreshed.access_token.token)
```

Token authentication follows the same shape:

```python
async with AsyncClient() as client:
    auth = await client.authentication.with_token(
        ksef_token="your-ksef-token",
        nip="5261040828",
    )
```

## Refreshing Access Tokens

Refreshing returns a `RefreshedToken`, not a new `AuthenticatedClient`:

```python
refreshed = client.authentication.refresh(refresh_token=auth.refresh_token)
print(refreshed.access_token.token)
print(refreshed.access_token.valid_until)
```

If you need a fresh authenticated context after expiry, authenticate again with XAdES or a KSeF token.

Example:
- [`scripts/examples/auth/auth_refresh.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/auth/auth_refresh.py)

## Active Authentication Sessions

Successful authentication also creates an auth session managed through `auth.sessions`.

```python
sessions = auth.sessions.query(page_size=10)
for item in sessions.items:
    print(item.reference_number, item.authentication_method, item.is_current)

for page in auth.sessions.all(page_size=10):
    print(len(page.items))

auth.sessions.terminate_current()

# Close a different auth session by reference number
# auth.sessions.close(reference_number="session-reference")
```

Example:
- [`scripts/examples/session/session_management.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/session/session_management.py)

## Flow

1. `client.authentication.with_xades(...)` or `client.authentication.with_token(...)`
2. Polling and token redemption happen inside the SDK
3. You receive an `AuthenticatedClient`
4. Use `auth.online_session()`, `auth.invoices`, `auth.tokens`, `auth.permissions`, and the other authenticated entry points

## Related

- [Sessions](sessions.md)
- [Async Client](async-client.md)
- [Tokens](tokens.md)
- [Test Data](testdata.md)
