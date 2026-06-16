---
title: Szyfrowanie
description: Certyfikaty publiczne i szyfrowanie używane przez SDK.
---

SDK pobiera publiczne certyfikaty KSeF i używa ich do szyfrowania tokenów oraz
kluczy sesji.

```python
certificates = client.encryption.get_certificates()
for cert in certificates:
    print(cert.public_key_id, cert.usage)
```

Authenticated client ładuje materiały szyfrujące automatycznie, gdy otwierasz
sesję online albo batch.

```python
key, iv, encrypted_key = auth.get_encryption_key()
```

Zwykle nie musisz wywoływać niskopoziomowych funkcji szyfrujących bezpośrednio.
