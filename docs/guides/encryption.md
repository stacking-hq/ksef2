---
title: Encryption Certificates
description: Retrieve and use public KSeF encryption certificates.
---

`client.encryption` exposes the public KSeF certificates used to encrypt KSeF tokens
and session symmetric keys.

## List Public Certificates

```python
from ksef2 import Client

client = Client()

certificates = client.encryption.get_certificates()

for cert in certificates:
    print(cert.valid_from, cert.valid_to, cert.usage)
```

SDK endpoint: `GET /security/public-key-certificates`

## Filter by Usage

```python
from ksef2 import Client

client = Client()

token_certs = client.encryption.get_certificates(
    usage=["ksef_token_encryption"],
)

session_certs = client.encryption.get_certificates(
    usage=["symmetric_key_encryption"],
)

print(len(token_certs), len(session_certs))
```

Common usage values:

- `ksef_token_encryption`
- `symmetric_key_encryption`

## Notes

Most applications do not need to call `client.encryption` directly.
The SDK uses these certificates internally for:

- `client.authentication.with_token()`
- `auth.online_session()`
- `auth.batch_session()`
- `auth.invoices.schedule_export()`

## Related

- [Authentication](authentication.md)
- [Invoices](invoices.md)
