---
title: Manage Tokens
description: Generate, list, inspect, and revoke KSeF tokens through ksef2.
---

Use `auth.tokens` when an authenticated context needs to create or retire KSeF
tokens for automation. The examples assume you already have an authenticated
client named `auth`.

## Generate a token

Choose the smallest permission set required by the automation that will use the
token.

```python
token = auth.tokens.generate(
    permissions=["invoice_read"],
    description="nightly invoice export",
)

token_reference = token.reference_number
token_secret = token.token
```

`generate()` returns a `GeneratedToken` handle as soon as KSeF provides the
one-time credential. Its `token` value is the secret your automation will use
for token authentication later; the handle exposes every field of the generation
response.

Default `repr` and generic Pydantic dumps omit the secret. Read `.token` only
at the protected storage boundary, or use `to_sensitive_dict()` when an
explicit secret-bearing mapping is required.

:::caution[Token values are shown once]
Persist the returned token value immediately in a secret store. Later status
and list calls identify tokens by `reference_number`, but they do not recover
the secret token value.
:::

After persisting the credential, wait explicitly when the next operation needs
an active token:

```python
status = auth.tokens.generate(...).wait(timeout=60.0, poll_interval=1.0)
# or, on the handle you already hold:
status = token.wait(timeout=60.0, poll_interval=1.0)
```

A timeout or transport error from `wait()` does not discard the credential you
already stored. Resume the status check later with
`auth.tokens.get_status(reference_number=...)`.

## List tokens

`list()` returns a `Pager`: iterate it for every token, call `.pages()` for
page-sized lists, or `.first_page()` to make a single request. Nothing is
requested until you consume it.

### All tokens

```python
for item in auth.tokens.list():
    print(item.reference_number, item.status, item.description)

# TokenInfo
# {
#   "reference_number": "20260625-TOKEN-...",
#   "description": "nightly invoice export",
#   "requested_permissions": ["invoice_read"],
#   "status": "active"
# }
```

### One page

```python
first = auth.tokens.list().first_page()
```

### Page by page

```python
for page in auth.tokens.list().pages():
    print(len(page), "tokens on this page")
```

## Inspect or revoke one token

Use the token reference number for later lifecycle operations.

```python
status = auth.tokens.get_status(reference_number="20260625-TOKEN-...")

# TokenStatusResponse
# {
#   "reference_number": "20260625-TOKEN-...",
#   "status": "active"
# }
```

```python
auth.tokens.revoke(reference_number="20260625-TOKEN-...")
```

:::tip[Keep reference and secret separately]
Store the token secret in a secret manager. Store the `reference_number` in
operational metadata so you can inspect or revoke the token later without
exposing the secret.
:::

## Recommended flow

1. Choose the smallest permission set required by the automation.

2. Generate the token in the authenticated context that should own it.

3. Store the token value in a secret store and the reference number in metadata.

4. Wait for activation when the token must be usable immediately.

5. List or inspect token references during audits.

6. Revoke unused, expired, or compromised tokens.

## Next workflows

- [Authenticate](authenticate.md): Use a generated KSeF token as one of the SDK authentication methods.
- [Authentication methods](../concepts/authentication-methods.md): Understand KSeF token, XAdES, TEST certificate, and profile-based authentication.
- [Client setup](client-setup.md): Create sync or async clients before using authenticated branches.
