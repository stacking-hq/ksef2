---
title: Przepływy administracyjne
description: Tokeny, uprawnienia, certyfikaty, limity, dane TEST i pomocnicze wyszukiwarki.
---

Większość administracyjnych przepływów KSeF jest dostępna po uwierzytelnieniu
przez gałęzie klienta `auth`.

## Tokeny

```python
token = auth.tokens.generate(
    permissions=["invoice_read"],
    description="nightly export",
)
print(token.token)
```

## Uprawnienia

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
```

## Certyfikaty, limity i TEST

```python
limits = auth.certificates.get_limits()
print(limits.can_request)

context_limits = auth.limits.get_context_limits()
print(context_limits.online_session.max_invoices)

client.testdata.create_subject(
    nip="5261040828",
    subject_type="vat_group",
    description="Quickstart company",
)
```

Gałąź `testdata` działa tylko w `Environment.TEST`.

## Publiczne wyszukiwarki

```python
certificates = client.encryption.get_certificates()
providers = client.peppol.query()
```

## Referencja

- [Tokens API](../reference/api/tokens.md)
- [Permissions API](../reference/api/permission-grants.md)
- [Certificates API](../reference/api/certificates.md)
- [Limits API](../reference/api/limits.md)
- [TEST data API](../reference/api/testdata.md)
- [PEPPOL API](../reference/api/peppol.md)
