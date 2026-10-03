---
title: PEPPOL
description: Understand PEPPOL provider lookup and where it fits in the SDK.
---

PEPPOL provider lookup is a public root-client workflow. It does not require an
authenticated KSeF context and it does not participate in invoice session
processing by itself.

Use it as reference data: populate provider choices, validate provider ids, or
refresh a local provider cache. Keep it separate from sending invoices,
querying KSeF invoice metadata, exports, and UPO status.

:::note[Public lookup only]
PEPPOL lookup does not prove delivery, KSeF acceptance, or session processing
state. It only reads provider data registered in KSeF.
:::

## Where it sits in the SDK

PEPPOL is exposed on the root client next to other public branches:

```python
for provider in client.peppol.list():
    print(provider.id, provider.name)
```

`list()` returns a `Pager` over the paginated response: iterating it follows the
pages for you, `.pages()` yields one list per page and `.first_page()` makes a
single request.

```python
providers_by_id = {
    provider.id: provider.name
    for provider in client.peppol.list()
}
```

## Product boundary

Provider records are product reference data. Cache provider ids and names
according to your freshness requirements, and refresh that cache independently
from authenticated invoice workers.

Only connect this lookup to invoice workflows when your own product has a
PEPPOL-specific step, such as letting a user choose a provider id before
building an integration-specific payload.

## Related pages

- [Query PEPPOL providers](../how-to-guides/query-peppol-providers.md): Fetch one page or iterate through all PEPPOL providers from SDK code.
- [SDK Overview](overview.md): See PEPPOL among the root client branches.
- [Client setup](../how-to-guides/client-setup.md): Create the root client used for public provider lookup.
