---
title: Query PEPPOL Providers
description: Query PEPPOL service providers registered in KSeF.
---

Use `client.peppol` when you need the public list of PEPPOL service providers
registered in KSeF. This is a root-client branch and does not require
authentication.

## Query providers

### One page

```python
page = client.peppol.query()

# ListPeppolProvidersResponse
# {
#   "has_more": false,
#   "providers": [
#     {
#       "id": "PPL123456",
#       "name": "Example PEPPOL Provider",
#       "date_created": "2026-06-25T10:00:00Z"
#     }
#   ]
# }

for provider in page.providers:
    print(provider.id, provider.name)
```

### All providers

```python
for provider in client.peppol.all():
    print(provider.id, provider.name, provider.date_created)
```

## Cache provider choices

Provider records are reference data. Query them from KSeF, then cache the id and
display name for user selection or validation in your product.

```python
providers_by_id = {
    provider.id: provider.name
    for provider in client.peppol.all()
}
```

## Recommended flow

1. Query providers from the root client.

2. Store provider ids and names in your application's reference-data cache.

3. Use provider ids when validating user choices or PEPPOL-related data.

4. Refresh the cache according to your product's data freshness needs.

## Next workflows

- [Client setup](client-setup.md): Create the root client used for public PEPPOL provider queries.
- [PEPPOL](../concepts/peppol.md): Understand where PEPPOL provider data fits in the SDK surface.
