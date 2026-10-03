---
title: Use XAdES Helpers
description: Load certificates and private keys, generate TEST certificates, and sign XML for KSeF authentication.
---

Use XAdES helpers when you authenticate with certificate material or need to
diagnose the signed authentication XML. Most applications should still call
`client.authentication.with_xades()` instead of signing manually.

## Load certificate material

### With PEM

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

### With PKCS#12

```python
import os

from ksef2.xades import load_certificate_and_key_from_p12

password = os.environ.get("KSEF2_P12_PASSWORD")

cert, private_key = load_certificate_and_key_from_p12(
    "company.p12",
    password=password.encode() if password else None,
)
```

## Authenticate with XAdES

Pass the loaded certificate and private key to the authentication branch.

```python
auth = client.authentication.with_xades(
    nip="5261040828",
    cert=cert,
    private_key=private_key,
)
```

## Generate TEST certificate material

Use generated certificates only in TEST workflows.

### Company

```python
from ksef2.xades import generate_test_certificate

cert, private_key = generate_test_certificate(nip="5261040828")
```

### Person

```python
from ksef2.xades import generate_personal_test_certificate

cert, private_key = generate_personal_test_certificate(
    pesel="90010112345",
    nip="5261040828",
)
```

## Sign XML directly

Use direct signing helpers for diagnostics or lower-level tests. For normal
authentication, prefer `with_xades()`.

```python
from ksef2.xades import build_auth_token_request_xml, sign_xades

xml = build_auth_token_request_xml(
    challenge="challenge-from-ksef",
    nip="5261040828",
)

signed_xml = sign_xades(xml, cert, private_key)
```

:::caution[Protect private keys]
Keep private-key files and passwords outside source control. Load passwords
from environment variables or a secret manager, and pass only the loaded key
object to SDK authentication.
:::

## Recommended flow

1. Load certificate material from PEM or PKCS#12.

2. Keep private-key passwords in environment variables or a secret manager.

3. Authenticate through `with_xades()` when possible.

4. Generate self-signed certificates only for TEST.

5. Use direct signing helpers only for diagnostics or low-level integration
   tests.

## Next workflows

- [Authenticate](authenticate.md): Use loaded XAdES certificate material in SDK authentication.
- [Manage certificates](manage-certificates.md): Enroll, retrieve, and revoke KSeF certificates.
- [XAdES](../concepts/xades.md): Understand where XAdES fits in the KSeF authentication methods.
