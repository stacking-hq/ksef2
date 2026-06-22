---
title: Low-level API
description: Use schema-native endpoint calls when a KSeF integration needs lower-level control.
---

The low-level API is the SDK's advanced seam for callers who need endpoint-level
control without leaving the SDK transport. It is exposed through the `raw`
client branch. Use it when you need custom signing, custom encryption custody,
exact OpenAPI-shaped payloads, or a debugging path that shows what KSeF
receives.

Most application code should still start with the workflow clients. Low-level
calls are intentionally explicit: request and response objects use KSeF/OpenAPI
field names such as `referenceNumber`, `publicKeyId`, and
`authenticationToken`.

## Three levels

```python
# Workflow level: SDK owns the whole task.
status = session.send_invoice_and_wait(invoice_xml=invoice_xml)

# Step level: SDK owns protocol details, caller owns ordering.
result = session.send_invoice(invoice_xml=invoice_xml)
status = session.wait_for_invoice_ready(
    invoice_reference_number=result.reference_number,
)

# Low-level API: caller owns endpoint order and schema-native payloads.
sent = auth.raw.invoices.send(reference_number, send_request)
```

The low-level API is still higher than `httpx`: it keeps SDK retry handling,
lifecycle checks, bearer-token middleware, response parsing, and KSeF exception
mapping.

## Import models

Import schema-native models from `ksef2.raw`, not from the internal `infra`
package.

```python
from ksef2.raw import spec

request = spec.GenerateTokenRequest(...)
response = auth.raw.tokens.generate_token(request)
```

Some low-level endpoint methods use supplemental SDK schema models where the
generated OpenAPI model is not Python-friendly. Those models are re-exported
from `ksef2.raw.spec` for the common path, and `ksef2.raw.supp` is available
when you need the supplemental package directly.

## Mix low-level and workflow calls

You can move between levels. A common pattern is manual low-level
authentication, then normal workflow calls:

```python
from ksef2.raw.mappers import auth as auth_mapper

raw_tokens = client.raw.auth.redeem_token(auth_token)
auth = client.authenticated(auth_mapper.from_spec(raw_tokens))

with auth.online_session(form_code=FormSchema.FA3) as session:
    status = session.send_invoice_and_wait(invoice_xml=invoice_xml)
```

The main rule is session ownership. If low-level code opens a session, low-level
code should usually close and poll that session. If high-level code opens a
session, use the session client returned by the SDK.

## Low-level API section

- [Manual authentication](authentication.md)
- [Sessions and invoices](sessions-invoices.md)
- [Endpoint map](endpoint-map.md)
