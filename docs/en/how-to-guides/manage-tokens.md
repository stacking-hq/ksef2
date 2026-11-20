---
title: Manage Tokens
description: Generate, list, inspect, and revoke KSeF tokens through ksef2.
---

Use `auth.tokens` when an authenticated context needs to create or retire KSeF
tokens for automation. The examples assume you already have an authenticated
client named `auth`.

Pass at least one permission to `generate()`. Permission strings use
snake_case, such as `"invoice_read"`; `TokenPermissionEnum.INVOICE_READ` is also
accepted. An API value such as `"InvoiceRead"` raises `KSeFArgumentError` with
`did you mean "invoice_read"?`. Empty permission lists, empty token references
passed to `revoke()`, and empty `ksef_token` values passed to `with_token()` fail
locally with `KSeFArgumentError` before any HTTP request.

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
status = token.wait(timeout=60.0, poll_interval=1.0)
```

A timeout or transport error from `wait()` does not discard the credential you
already stored. Resume the status check later with
`auth.tokens.get_status(reference_number=...)`.

### Approve a pending token

If `get_status()` returns `awaiting_approval`, approve the token from an eligible
session authenticated with an accepted XAdES signature or the National Node.

```python
approval_auth.tokens.approve(reference_number=token.reference_number)
status = token.wait(timeout=60.0)
```

Set timezone-aware `valid_from` and `valid_to` when calling `generate()` to
schedule a validity period. A token with status `not_yet_active` becomes usable
when KSeF reports `active`. `get_status()` and list items expose `valid_from`,
`valid_to`, and any `failure`.

### Resume the handle after a restart

`token.resume_state()` returns a `GeneratedTokenResumeState`: the token's
reference number and nothing else. Persist it with `to_json()` and hand it to
`auth.tokens.generation()` when a queue worker or a restarted process picks the
job up again.

```python
saved_state = token.resume_state().to_json()

# Later, in the same or another process:
token = auth.tokens.generation(saved_state)
status = token.wait(timeout=60.0, poll_interval=1.0)
```

`generation()` takes the state object or its JSON string and returns a handle
that polls the same reference number. The one-time token is never part of the
state, in `to_json()`, `to_dict()`, `model_dump()` or `repr()`, so a resumed
handle has no `token` and no `response`: keep storing the secret yourself.

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
#   "reference_number": "20260625-EC-0123456789-ABCDEF0123-45",
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

### Resume from a cursor

`.page()` returns one `Page`: its `items` and `next_cursor`, the string naming
the page after it. Keep that string and pass it back to `.page()`, in this
process or a later one, to continue without re-reading the tokens you already
saw.

```python
first = auth.tokens.list().page()
cursor = first.next_cursor

# Later, after a restart.
if cursor is not None:
    second = auth.tokens.list().page(cursor)
```

Rebuild the pager with the same parameters: this cursor holds KSeF's
continuation state for the collection, not your filters. `.pages()` and plain
iteration follow the same cursor chain, and `next_cursor` is `None` only after
the last page. An empty page on its own does not end the walk. In async code the
same read is `second = await auth.tokens.list().page(cursor)`.

## Inspect or revoke one token

Use the token reference number for later lifecycle operations.

```python
status = auth.tokens.get_status(reference_number="20260625-EC-0123456789-ABCDEF0123-45")

# TokenStatusResponse
# {
#   "reference_number": "20260625-EC-0123456789-ABCDEF0123-45",
#   "status": "active"
# }
```

```python
auth.tokens.revoke(reference_number="20260625-EC-0123456789-ABCDEF0123-45")
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
