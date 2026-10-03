---
title: Use TEST Data
description: Create sandbox subjects, people, permissions, attachment flags, and blocked contexts in TEST.
---

Use `client.testdata` only with `Environment.TEST`. These helpers mutate KSeF
sandbox data so tests and demos can create known contexts.

## Create sandbox data manually

Use direct methods for shared fixtures that should survive multiple test runs.

### Subject

```python
client.testdata.create_subject(
    nip="5261040828",
    subject_type="vat_group",
    description="Sandbox company",
)

client.testdata.enable_attachments(nip="5261040828")
```

### Person

```python
client.testdata.create_person(
    nip="5261040828",
    pesel="90010112345",
    description="Sandbox person",
)
```

### Block context

```python
from ksef2.models import AuthContextIdentifier

context = AuthContextIdentifier(type="nip", value="5261040828")

client.testdata.block_context(context=context)
client.testdata.unblock_context(context=context)
```

Delete shared fixtures explicitly when they are no longer needed:

```python
client.testdata.delete_person(nip="5261040828")
client.testdata.delete_subject(nip="5261040828")
```

## Use temporal cleanup

`temporal()` records mutations and attempts best-effort cleanup when the block
exits.

### Subject and attachments

```python
with client.testdata.temporal() as data:
    data.create_subject(
        nip="5261040828",
        subject_type="vat_group",
        description="Integration test subject",
    )
    data.enable_attachments(nip="5261040828")
```

### Permissions

```python
from ksef2.models import Identifier, Permission

with client.testdata.temporal() as data:
    data.grant_permissions(
        permissions=[
            Permission(type="invoice_read", description="Read invoices"),
        ],
        grant_to=Identifier(type="nip", value="1111111111"),
        in_context_of=Identifier(type="nip", value="5261040828"),
    )
```

### Blocked context

```python
from ksef2.models import AuthContextIdentifier

context = AuthContextIdentifier(type="nip", value="5261040828")

with client.testdata.temporal() as data:
    data.block_context(context=context)
```

:::caution[TEST only]
The TEST data branch exists to prepare sandbox fixtures. Do not build product
workflows that depend on it in DEMO or PRODUCTION.
:::

## Generate identifiers

`ksef2.testdata` generates checksum-valid NIP and PESEL numbers so every test
run can use fresh sandbox subjects:

```python
from ksef2.testdata import generate_nip, generate_pesel

nip = generate_nip()
pesel = generate_pesel()
```

## Recommended flow

1. Create only the subjects, people, permissions, attachment flags, or blocked
   contexts required by the test.

2. Use `temporal()` for fixtures that should be cleaned up automatically.

3. Use direct create/delete methods for fixtures shared across many test runs.

4. Keep generated identifiers in test configuration, not production
   configuration.

## Next workflows

- [Client setup](client-setup.md): Create a TEST root client before using the testdata branch.
- [Authenticate](authenticate.md): Authenticate against TEST contexts created by testdata helpers.
- [Configure permissions](configure-permissions.md): Use production permission APIs after testing grant shapes in TEST.
