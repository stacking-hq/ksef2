---
title: ksef2 1.0.0 Release Notes
description: Stability boundary and the documented public surface of the first stable ksef2 SDK release.
---

ksef2 1.0.0 is the first release that treats documented application-facing
imports as a compatibility contract for the 1.x line.
The SDK currently targets KSeF OpenAPI version `2.8.1`.

> **Unofficial SDK.** ksef2 is community-maintained. It is not published,
> endorsed, or supported by Poland's Ministry of Finance. The official KSeF
> documentation remains the source of truth for API behavior.

[Official KSeF API v2 documentation](https://api-test.ksef.mf.gov.pl/docs/v2/) — Use the Ministry of Finance documentation as the authority for API behavior.

## Stable in 1.0

The stable contract is the documented public SDK surface, not every importable
module in the repository.

| Surface | 1.0 contract |
| --- | --- |
| `ksef2` | Root clients, environments, transport config, `FormSchema`, `__version__`, and public exceptions. |
| `ksef2.clients` | Concrete sync and async client classes for type annotations and advanced construction. |
| `ksef2.models` | Public SDK request, response, filter, pagination, token, permission, session, batch, and invoice models. |
| High-level client branches | `client.authentication`, `client.encryption`, `client.peppol`, `client.testdata`, and authenticated branches such as `auth.invoices`, `auth.tokens`, `auth.permissions`, `auth.certificates`, `auth.collective_identifiers`, and `auth.limits`. |
| Collective identifier workflows | `auth.collective_identifiers` generates a collective identifier for supplied invoices, queries identifiers page by page, resolves the identifiers attached to one KSeF number, and lists the invoices inside selected collective identifiers. |
| Session helpers | Online and batch session workflows for sending, polling, UPO, and resumable KSeF references. |
| `ksef2.xades` | Certificate loading, TEST certificate generation, local XAdES signing helpers, and `LocalSigner`. |
| `ksef2.profiles` | Local `ksef2-cli` compatible profile config helpers. |
| `ksef2.fa3` | Public FA(3) invoice builder, draft snapshots, and public FA(3) domain models used by builder workflows. |
| `ksef2.renderers` | Optional local XSLT/PDF invoice rendering helpers when installed with the `pdf` extra. |

For the exact compatibility boundary, use the public API contract page.

## Invoice workflows in 1.0

Operations that start asynchronous KSeF work return a handle with `.wait()`,
and every collection returns one `Pager`. The old names remain as deprecated
aliases.

```python
# before (0.22.x)
sent = session.send_invoice(invoice_xml=xml)
status = session.wait_for_invoice_ready(invoice_reference_number=sent.reference_number)
for m in auth.invoices.all_metadata(filters=f): ...

# after (1.0)
submission = session.send_invoice(xml)
status = submission.wait(timeout=60)
upo = submission.download_upo()
for m in auth.invoices.search(f): ...
package = auth.invoices.export(f).wait()
package.save("out/")
```

Access tokens refresh automatically, and a session or export can be resumed
through the method that starts it: `auth.online_session(state=saved)`.

## Deprecation policy

A deprecated API is removed in a stated 1.x release. Every deprecation shipped
with 1.0.0 is removed in **ksef2 1.10.0**, including the seven deprecated in
0.19.0. See the [deprecated APIs](public-api.md#deprecated-apis) table.

## Errors

Every API error reads the same way, carries the raw KSeF code and trace ID, and
says what to do next. The response body is no longer dumped into the message; it
stays on `e.response`. Branch on the exception class or `ksef_code`, never on
message text.

```text
# before
API_ERROR/400: KSeF API error: 400
[UPO_NOT_FOUND:21178] Nie znaleziono UPO dla podanych kryteriów.
Response: { "exception": { "exceptionDetailList": [ ... ] } }

# after (KSeFNotReadyError)
KSeF rejected GET /sessions/online/S1/invoices/I1/upo (HTTP 400, KSeF code 21178): Nie znaleziono UPO dla podanych kryteriów.
Details: UPO o numerze referencyjnym 20260101-EE-ABC nie zostało znalezione.
Hint: KSeF has not issued the UPO yet. Wait for processing to finish and request it again.
```

`download_upo()` on a submission or session now waits for processing instead of
failing early.

## Public but lower level

`ksef2.raw` and `ksef2.raw.mappers` are public advanced APIs. Their import paths
are part of the 1.x contract, but their schema-native model shapes follow the
checked Ministry of Finance OpenAPI version.

Use `ksef2.raw` when you need endpoint-level control, exact OpenAPI-shaped
payloads, caller-owned encryption custody, or protocol debugging. Most
application code should use the high-level client branches.

## Not part of the 1.x contract

Do not build application code on these paths:

- any module path with an underscore-prefixed component, such as
  `ksef2._core` or `ksef2._clients.base` (a module path with no underscore is
  public; anything with an underscore is private);
- repository `scripts/*`;
- generated schema internals outside `ksef2.raw.spec` and `ksef2.raw.supp`.

The former internal packages (`ksef2.core`, `ksef2.domain`, `ksef2.infra`,
`ksef2.endpoints`, `ksef2.services`, the client implementation modules,
`ksef2.config` and `ksef2.logging`) are now underscore-prefixed, with no
compatibility aliases: importing the old paths raises `ImportError`. Private
modules can change without a 2.0 release.

## Related pages

- [Public API contract](public-api.md): Review stable imports and internal boundaries for application code.
- [Low-level API](low-level/overview.md): Understand the supported raw endpoint surface and its schema-following model contract.
- [Operations reference](operations.md): Review retries, timeouts, rate limits, logging boundaries, and resumable references.
