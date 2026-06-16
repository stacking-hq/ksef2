---
title: PEPPOL Providers
description: Query PEPPOL provider data through the public client.
---

`client.peppol` exposes the public PEPPOL provider registry published by KSeF.
These endpoints do not require authentication.

## Query One Page

```python
from ksef2 import Client
from ksef2.domain.models.pagination import OffsetPaginationParams

client = Client()

response = client.peppol.query(
    params=OffsetPaginationParams(page_offset=0, page_size=20),
)

for provider in response.providers:
    print(provider.id, provider.name, provider.date_created)
```

SDK endpoint: `GET /peppol/query`

## Iterate All Providers

```python
from ksef2 import Client

client = Client()

for provider in client.peppol.all():
    print(provider.id, provider.name)
```

## Example

- [`scripts/examples/peppol/query_providers.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/peppol/query_providers.py)

## Related

- [Authentication](authentication.md)
