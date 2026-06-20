---
title: Admin Workflows
description: Manage KSeF tokens, permissions, certificates, limits, TEST data, and lookup helpers.
---

Most administrative KSeF workflows live on authenticated client branches. Keep
the handwritten docs focused on where each workflow starts; use the API
reference for every method and model field.

## Tokens

```python
token = auth.tokens.generate(
    permissions=["invoice_read"],
    description="nightly export",
)
print(token.token)

for page in auth.tokens.list_all():
    for item in page.tokens:
        print(item.reference_number, item.status)

auth.tokens.revoke(reference_number="token-reference")
```

## Permissions

```python
operation = auth.permissions.grant_person(
    subject_type="pesel",
    subject_value="90010112345",
    permissions=["invoice_read"],
    description="Read invoices",
    first_name="Jan",
    last_name="Kowalski",
)

status = auth.permissions.get_operation_status(
    reference_number=operation.reference_number,
)
print(status.status)

attachment_status = auth.permissions.get_attachment_permission_status()
print(attachment_status.can_use_attachments)
```

## Certificates

```python
limits = auth.certificates.get_limits()
print(limits.can_request)

for certificate in auth.certificates.all():
    print(certificate.serial_number, certificate.status)
```

## Limits and TEST data

```python
context_limits = auth.limits.get_context_limits()
print(context_limits.online_session.max_invoices)

client.testdata.create_subject(
    nip="5261040828",
    subject_type="vat_group",
    description="Quickstart company",
)
```

The `testdata` branch is available only in `Environment.TEST`.

## Public lookups

Some branches do not require an authenticated client.

```python
certificates = client.encryption.get_certificates()
providers = client.peppol.query()
```

## Reference

- [Tokens API](../reference/api/tokens.md)
- [Permissions API](../reference/api/permission-grants.md)
- [Certificates API](../reference/api/certificates.md)
- [Limits API](../reference/api/limits.md)
- [TEST data API](../reference/api/testdata.md)
- [PEPPOL API](../reference/api/peppol.md)
