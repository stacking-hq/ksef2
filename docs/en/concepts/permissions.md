---
title: Tokens and Permissions
description: Understand tokens, permission scopes, grants, revokes, and operation state in KSeF.
---

Authentication proves identity. Permissions determine what that identity can do.
Tokens package selected permissions into reusable credential material. A
credential can authenticate successfully and still lack permission for the next
operation.

Permissions determine what a subject, person, entity, EU entity, authorization,
or subunit can do in a KSeF context. Many permission changes are asynchronous
operations: the grant or revoke call returns an operation reference, then the
application checks the operation status.

Keep permission code explicit about the target identifier, permission scope, and
context. This makes later audits and failure recovery much easier.

## Tokens

`auth.tokens` creates, lists, checks, and revokes KSeF tokens. Token generation
returns the one-time token payload and a reference number immediately. Persist
the credential before explicitly calling `wait_for_activation()`. This keeps a
polling timeout or transport failure from discarding the only copy of the token.

A generated token has a fixed permission set. If the permissions should change,
generate a new token and revoke the old one after migration. Token generation is
available only in supported entity contexts, such as NIP or internal ID, and it
requires prior XAdES authentication before the reusable token credential exists.

Tokens should be treated as secrets. Store the token value outside source
control and prefer environment variables or a secret manager. Profiles can refer
to token environment variables so CLI and Python code share configuration
without committing the secret.

:::caution[Credential success is not authorization]
A token or certificate can authenticate correctly and still fail the next call
when the selected context, target identifier, or permission scope does not
match the operation.
:::

## Permissions

Permission APIs are intentionally specific because KSeF distinguishes target
types and scopes. The SDK exposes separate methods for person, entity,
authorization, indirect, subunit, and EU entity grants, plus matching query and
revoke flows.

The official permission model combines target identifiers, permission types, and
delegation rules:

| Concept | Design implication |
| --- | --- |
| Target identifier | Use the correct identifier kind, such as NIP, PESEL, certificate fingerprint, EU VAT NIP, or internal ID. |
| Permission type | Keep finite choices explicit, such as invoice read, invoice write, credential read, credential manage, subunit manage, enforcement operations, or introspection. |
| Direct and indirect permissions | Query and revoke through the branch that matches how the permission was granted. |
| Delegation | `can_delegate` is meaningful only where KSeF permits delegation for that permission path. |
| Operation status | Grant and revoke calls return operation references; poll status before assuming the permission changed. |

```python
from ksef2.models import EntityPermission

operation = auth.permissions.grant_entity(
    subject_value="1234567890",
    permissions=[EntityPermission(type="invoice_read", can_delegate=False)],
    description="Accounting office read access",
    entity_name="Accounting Sp. z o.o.",
)

status = auth.permissions.get_operation_status(
    reference_number=operation.reference_number,
)
print(status.status.code, status.status.description)
```

When an authorization failure happens, check:

- selected environment;
- authenticated taxpayer or context identifier;
- profile name and credential type;
- token permission set;
- target identifier and permission scope;
- whether the grant or revoke operation has completed.

## Related pages

- [Manage tokens](../how-to-guides/manage-tokens.md): Generate, list, inspect, and revoke KSeF tokens.
- [Configure permissions](../how-to-guides/configure-permissions.md): Grant, query, inspect, and revoke permissions for entities and people.
- [Operations](../reference/operations.md): Understand operation references, polling, retries, and status checks.
- [Authentication methods](authentication-methods.md): Separate authentication identity from the permissions checked during protected operations.
