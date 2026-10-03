---
title: Inspect Encryption Certificates
description: Read public KSeF encryption certificates used by encrypted invoice and export workflows.
---

Use `client.encryption` when you need a startup check, diagnostics, or a custom
certificate cache. Most invoice workflows load public encryption certificates
automatically.

## Fetch certificates

`client.encryption` is a root-client branch, so it does not require an
authenticated client.

### All usages

```python
certificates = client.encryption.get_certificates()

# PublicKeyCertificate
# {
#   "public_key_id": "12345",
#   "certificate_id": "abcde",
#   "valid_from": "2026-06-01T00:00:00Z",
#   "valid_to": "2026-12-01T00:00:00Z",
#   "usage": ["ksef_token_encryption", "symmetric_key_encryption"]
# }

for certificate in certificates:
    print(certificate.public_key_id, certificate.usage, certificate.valid_to)
```

### Session/export keys

```python
certificates = client.encryption.get_certificates(
    usage=["symmetric_key_encryption"],
)

for certificate in certificates:
    print(certificate.public_key_id, certificate.valid_to)
```

### Token auth

```python
certificates = client.encryption.get_certificates(
    usage=["ksef_token_encryption"],
)

for certificate in certificates:
    print(certificate.public_key_id, certificate.valid_to)
```

## Preload before encrypted workflows

High-level online, batch, token-authentication, and export helpers use these
public certificates when they encrypt local key material for KSeF. Preloading is
useful when you want startup diagnostics before a worker accepts jobs.

```python
required_usage = "symmetric_key_encryption"
certificates = client.encryption.get_certificates(usage=[required_usage])

if not certificates:
    raise RuntimeError(f"No KSeF certificate supports {required_usage}.")
```

:::tip[Do not pin certificate contents in code]
Fetch current KSeF certificates and cache them according to your operational
needs. Hard-coded certificate data will eventually expire.
:::

## Recommended flow

1. Let high-level invoice workflows load certificates lazily by default.

2. Add a startup check only when certificate availability should fail fast.

3. Check the usage your workflow needs: token encryption or symmetric-key
   encryption.

4. Alert and retry later if no valid certificate is available.

## Next workflows

- [Encryption](../concepts/encryption.md): Understand where KSeF public certificates appear in SDK workflows.
- [Configure a certificate store](configure-certificate-store.md): Control certificate cache refresh or plug in application storage.
- [Send invoices](send-invoices.md): Use encryption certificates through high-level online and batch sessions.
- [Download invoices](download-invoices.md): Use export helpers that encrypt and decrypt package material for you.
