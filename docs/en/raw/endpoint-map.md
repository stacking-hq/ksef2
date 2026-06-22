---
title: Low-level endpoint map
description: Find the low-level ksef2 endpoint group for each KSeF area.
---

Low-level endpoint groups are thin facades over the SDK endpoint wrappers. They
are exposed through `client.raw` and `auth.raw`, use schema-native request and
response models, and share the same transport stack as the workflow clients.

## Before authentication

| Low-level branch | Use for |
| --- | --- |
| `client.raw.auth` | Challenge creation, token auth, XAdES auth, auth status, token redemption. |
| `client.raw.encryption` | Public KSeF encryption certificates. |
| `client.raw.peppol` | Public PEPPOL provider lookup. |
| `client.raw.testdata` | TEST-only subject, person, permission, attachment, and context fixtures. |

## After authentication

| Low-level branch | Use for |
| --- | --- |
| `auth.raw.auth` | Auth session listing and termination. |
| `auth.raw.certificates` | Certificate limits, enrollment, retrieval, query, and revocation. |
| `auth.raw.encryption` | Public KSeF encryption certificates. |
| `auth.raw.invoices` | Invoice metadata, export, download, online send, session invoice status, and UPO. |
| `auth.raw.limits` | Context, subject, and API rate-limit endpoints. |
| `auth.raw.peppol` | Public PEPPOL provider lookup. |
| `auth.raw.permissions.grant` | Permission grant endpoints. |
| `auth.raw.permissions.revoke` | Permission revocation endpoints. |
| `auth.raw.permissions.query` | Permission search and attachment status endpoints. |
| `auth.raw.permissions.status` | Permission operation status and entity role endpoints. |
| `auth.raw.session` | Online session open/terminate, batch session open/close, session UPO, session listing. |
| `auth.raw.testdata` | TEST-only fixture endpoints. |
| `auth.raw.tokens` | Token generation, listing, status, and revocation. |

## Imports

```python
from ksef2.raw import (
    encrypt_invoice,
    encrypt_symmetric_key,
    encrypt_token,
    generate_session_key,
    prepare_batch_package,
    sha256_b64,
    spec,
    supp,
)
from ksef2.raw.mappers import auth as auth_mapper
```

Low-level utility exports stay focused on KSeF mechanics such as encryption and
hashing. Request bodies stay explicit through `spec.*` models. Public mappers
such as `auth_mapper.from_spec(...)` are the explicit bridge from low-level
response models back to SDK domain models.
