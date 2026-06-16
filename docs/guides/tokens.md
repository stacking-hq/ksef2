---
title: Tokens
description: Create, query, and revoke KSeF authentication tokens.
---

KSeF tokens are generated and managed through `auth.tokens`.
They are different from access tokens and refresh tokens.

## Generate a KSeF Token

```python
result = auth.tokens.generate(
    permissions=["invoice_read", "invoice_write"],
    description="Example API token",
)

print(result.reference_number)
print(result.token)
```

SDK endpoint: `POST /tokens`

## List Tokens

The token client exposes `list_page()` for one page and `list_all()` for iteration across all pages.

```python
from ksef2.domain.models.pagination import TokenListParams

page = auth.tokens.list_page(
    params=TokenListParams(
        status=["active"],
        description="API token",
        page_size=20,
    )
)
for token in page.tokens:
    print(token.reference_number, token.status, token.description)

for page in auth.tokens.list_all(
    params=TokenListParams(status=["active"])
):
    print(len(page.tokens))
```

SDK endpoint: `GET /tokens`

## Check Token Status

```python
status = auth.tokens.status(reference_number=result.reference_number)
print(status.status)
```

SDK endpoint: `GET /tokens/{referenceNumber}`

## Revoke a Token

```python
auth.tokens.revoke(reference_number=result.reference_number)
```

SDK endpoint: `DELETE /tokens/{referenceNumber}`

## Common Status Values

- `pending`
- `active`
- `revoking`
- `revoked`
- `failed`

## Example

- [`scripts/examples/auth/token_management.py`](https://github.com/stacking-hq/ksef2/blob/main/scripts/examples/auth/token_management.py)

## Related

- [Authentication](authentication.md)
