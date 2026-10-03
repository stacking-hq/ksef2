---
title: Configure a Certificate Store
description: Configure the SDK certificate cache used by token authentication, sessions, and invoice exports.
---

The SDK stores KSeF public encryption certificates on the root client. Token
authentication, online and batch sessions, and invoice exports reuse that store
when they need to encrypt key material for KSeF.

Use the default in-memory store for scripts and workers that can refresh
certificates from KSeF. Provide a custom store when certificates must be shared
across processes or persisted in application storage.

## Use the default store

`Client` and `AsyncClient` create `CertificateStore` automatically. The default
store refreshes valid cached certificates after 24 hours and refreshes
immediately when the required certificate usage is missing.

Configure a different refresh interval at root-client construction:

```python
from datetime import timedelta

from ksef2 import CertificateStore, Client, Environment

store = CertificateStore(refresh_after=timedelta(hours=6))

with Client(Environment.PRODUCTION, certificate_store=store) as client:
    auth = client.authentication.with_profile("prod-token")
```

`AsyncClient` accepts the same `certificate_store` argument. Use
`async with AsyncClient(...)` and `await` the authentication call; nothing else
changes.

Use `refresh_after=None` only for short-lived clients where fetch-once behavior
is intentional:

```python
from ksef2 import CertificateStore

store = CertificateStore(refresh_after=None)
```

:::note[Missing usage still refreshes]
`refresh_after=None` does not suppress refreshes when the store lacks the
certificate usage required by the workflow. The SDK checks KSeF again before
raising `NoCertificateAvailableError`.
:::

## Provide a custom store

Custom stores implement `CertificateStoreProtocol`. The SDK owns remote
fetching; the store owns persistence, valid-certificate selection, and freshness
decisions.

```python
from collections.abc import Iterable
from datetime import datetime

from ksef2 import CertificateStoreProtocol, Client, Environment
from ksef2.models import CertUsage, CertUsageEnum, PublicKeyCertificate

class DatabaseCertificateStore:
    def load(self, certs: Iterable[PublicKeyCertificate]) -> None:
        """Replace stored public certificates after the SDK fetches them."""
        ...

    def get_valid(
        self,
        usage: CertUsage | CertUsageEnum | str,
    ) -> PublicKeyCertificate:
        """Return a currently valid certificate for the requested usage."""
        ...

    def needs_refresh(
        self,
        usage: CertUsage | CertUsageEnum | str,
        *,
        at: datetime | None = None,
    ) -> bool:
        """Return True when the SDK should fetch certificates from KSeF."""
        ...

store: CertificateStoreProtocol = DatabaseCertificateStore()
client = Client(Environment.PRODUCTION, certificate_store=store)
```

## Recommended flow

1. Start with the default `CertificateStore`.

2. Set `refresh_after` when your application has a stricter certificate rotation
   or startup policy.

3. Implement `CertificateStoreProtocol` only when certificates must survive
   process restarts or be shared by multiple workers.

4. Keep remote KSeF fetching in the SDK client and keep persistence in the
   store.

## Related pages

- [Inspect encryption certificates](inspect-encryption-certificates.md): Read and inspect public KSeF encryption certificates directly.
- [Client setup](client-setup.md): Configure root clients, transport, lifecycle, and authenticated branches.
- [Encryption](../concepts/encryption.md): Understand how public certificates protect token, session, and export key material.
