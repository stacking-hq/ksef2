---
title: Test Data
description: Use TEST-environment helper endpoints for integration workflows.
---

`client.testdata` is available only on `Environment.TEST`.
It helps create disposable subjects, people, permissions, attachment state, and blocked auth contexts.

## Create Subjects and People

```python
from ksef2 import Client, Environment

client = Client(Environment.TEST)

client.testdata.create_subject(
    nip="1234567890",
    subject_type="enforcement_authority",
    description="Test organization",
)

client.testdata.create_person(
    nip="1234567890",
    pesel="12345678901",
    description="Test person",
)
```

SDK endpoints:
- `POST /testdata/subject`
- `POST /testdata/person`

## Grant and Revoke Permissions

```python
from ksef2.domain.models.testdata import Identifier, Permission

client.testdata.grant_permissions(
    permissions=[
        Permission(type="invoice_read", description="Read invoices"),
        Permission(type="invoice_write", description="Send invoices"),
    ],
    grant_to=Identifier(type="nip", value="0987654321"),
    in_context_of=Identifier(type="nip", value="1234567890"),
)

client.testdata.revoke_permissions(
    revoke_from=Identifier(type="nip", value="0987654321"),
    in_context_of=Identifier(type="nip", value="1234567890"),
)
```

SDK endpoints:
- `POST /testdata/permissions`
- `POST /testdata/permissions/revoke`

## Attachment Permissions

```python
from datetime import date, timedelta

client.testdata.enable_attachments(nip="1234567890")
client.testdata.revoke_attachments(nip="1234567890")
client.testdata.revoke_attachments(
    nip="1234567890",
    expected_end_date=date.today() + timedelta(days=30),
)
```

SDK endpoints:
- `POST /testdata/attachment`
- `POST /testdata/attachment/revoke`

## Block and Unblock Auth Contexts

```python
from ksef2.domain.models.testdata import AuthContextIdentifier

context = AuthContextIdentifier(type="nip", value="1234567890")
client.testdata.block_context(context=context)
client.testdata.unblock_context(context=context)
```

SDK endpoints:
- `POST /testdata/context/block`
- `POST /testdata/context/unblock`

## Automatic Cleanup with `temporal()`

Use `temporal()` whenever possible so cleanup happens automatically:

```python
from ksef2.core.tools import generate_nip, generate_pesel
from ksef2.domain.models.testdata import Identifier, Permission

org_nip = generate_nip()
person_nip = generate_nip()
person_pesel = generate_pesel()

with client.testdata.temporal() as temp:
    temp.create_subject(
        nip=org_nip,
        subject_type="enforcement_authority",
        description="Example organization",
    )
    temp.create_person(
        nip=person_nip,
        pesel=person_pesel,
        description="Example person",
    )
    temp.grant_permissions(
        permissions=[
            Permission(type="invoice_read", description="Read invoices"),
            Permission(type="invoice_write", description="Send invoices"),
        ],
        grant_to=Identifier(type="nip", value=person_nip),
        in_context_of=Identifier(type="nip", value=org_nip),
    )

    # tests or demos go here
```

Example:
- [`scripts/examples/testdata/setup_test_data.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/testdata/setup_test_data.py)

## Related

- [Authentication](authentication.md)
- [Limits](limits.md)
