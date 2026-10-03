---
title: Client Setup
description: Create ksef2 sync and async clients, configure transport behavior, and choose authenticated branches.
---

The root `Client` owns HTTP transport configuration and exposes unauthenticated
public branches. Authenticate once for a KSeF context, then pass the
authenticated client into workflow code.

## Choose sync or async

`Client` is the synchronous root client and `AsyncClient` is its async twin.
They expose the same API; with `AsyncClient` you use `async with` and `await`
the calls.

### Sync

```python
from ksef2 import Client, Environment

with Client(Environment.TEST) as client:
    auth = client.authentication.with_test_certificate(nip="5261040828")
```

### Async

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
```

Use `Environment.DEMO` or `Environment.PRODUCTION` outside local TEST
workflows.

## Manage lifecycle

The root client owns SDK-managed HTTP resources. Prefer a context manager for
scripts and jobs:

```python
from ksef2 import Client, Environment

with Client(Environment.TEST) as client:
    auth = client.authentication.with_test_certificate(nip="5261040828")
```

If a framework asks for a yielded dependency, put the `yield` inside the
dependency function and close the client in `finally`:

```python
from collections.abc import Iterator

from ksef2 import Client, Environment

def get_client() -> Iterator[Client]:
    client = Client(Environment.TEST)
    try:
        yield client
    finally:
        client.close()
```

Async applications use the same boundary with `async with`:

```python
from ksef2 import AsyncClient, Environment

async with AsyncClient(Environment.TEST) as client:
    auth = await client.authentication.with_test_certificate(nip="5261040828")
```

Online and batch sessions are lifecycle boundaries too. Use a session context
manager so the SDK closes the remote session when the block exits:

```python
from ksef2 import FormSchema

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice(invoice_xml).wait()
```

When credentials live in a CLI-compatible profile, create the root client for
the profile environment and authenticate through `with_profile()`:

```python
from ksef2 import Client, Environment

client = Client(Environment.PRODUCTION)
auth = client.authentication.with_profile("prod-token")
```

## Public root branches

The root client is useful before authentication:

```python
certificates = client.encryption.get_certificates()
providers = client.peppol.query()
```

The TEST-only branch is also on the root client:

```python
client.testdata.create_subject(
    nip="5261040828",
    subject_type="vat_group",
    description="Sandbox company",
)
```

## Authenticated branches

After authentication, use the branch that matches the task:

```python
invoices = auth.invoices
batch = auth.batch
tokens = auth.tokens
permissions = auth.permissions
certificates = auth.certificates
limits = auth.limits
sessions = auth.sessions
invoice_sessions = auth.invoice_sessions
```

:::note[Keep root and authenticated clients separate]
The root client chooses environment and transport. The authenticated client
owns bearer tokens and context-specific branches. Passing the authenticated
client into workflow code keeps auth state out of unrelated setup code.
:::

## Recommended flow

1. Read environment and transport settings in your application boundary.

2. Create one root client for the selected KSeF environment.

3. Use root branches only for public lookup or TEST data setup.

4. Authenticate once for the context that owns the operation.

5. Pass the authenticated client to invoice, token, permission, certificate,
   limits, and session workflows.

## Reference

- [Authentication guide](authenticate.md): Authenticate with a token, XAdES certificate, TEST certificate, or profile.
- [Operations](../reference/operations.md): Map common workflows to high-level SDK entry points.
- [Configure a certificate store](configure-certificate-store.md): Configure certificate cache refresh or provide a custom certificate store.
- [Encryption certificates](inspect-encryption-certificates.md): Inspect KSeF public encryption certificates before encrypted workflows.
- [PEPPOL providers](query-peppol-providers.md): Query public PEPPOL provider data from the root client.
- [TEST data](use-test-data.md): Create and manage TEST subjects and permissions.
- [Client lifecycle](../reference/client-lifecycle.md): Review root client lifecycle, authenticated clients, and close behavior.
