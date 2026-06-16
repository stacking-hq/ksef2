---
title: Tokeny
description: Generowanie, listowanie, sprawdzanie i unieważnianie tokenów KSeF.
---

Tokeny KSeF obsługujesz przez `auth.tokens`.

## Generowanie

```python
token = auth.tokens.generate(
    permissions=["invoice_read"],
    description="Reporting",
    timeout=60.0,
    poll_interval=1.0,
)
print(token.token)
```

`timeout` jest podawany w sekundach.

## Status

```python
status = auth.tokens.status(reference_number=token.reference_number)
print(status.status)
```

## Listowanie

```python
for page in auth.tokens.list_all():
    for token in page.tokens:
        print(token.reference_number, token.status)
```

## Unieważnienie

```python
auth.tokens.revoke(reference_number="token-reference")
```
