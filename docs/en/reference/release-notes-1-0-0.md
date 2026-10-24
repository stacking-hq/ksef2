---
title: ksef2 1.0.0 Release Notes
description: Stability boundary and the documented public surface of the first stable ksef2 SDK release.
---

> Release preparation is in progress. The release date is not set.
> Compatibility aliases from [#171](https://github.com/stacking-hq/ksef2/issues/171)
> are included and covered by the legacy compatibility gate.

ksef2 1.0.0 is the first release that treats documented application-facing
imports as a compatibility contract for the 1.x line.
The SDK currently targets KSeF OpenAPI version `2.9.0`.

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
| Paging | Every `Pager` answers `.page(cursor)` with a `Page` (`items`, `next_cursor`), where the cursor is SDK-issued state you can store and replay after a restart, alongside `.pages()`, `.first_page()` and `.wait()`. |
| `ksef2.xades` | Certificate loading, TEST certificate generation, local XAdES signing helpers, and `LocalSigner`. |
| `ksef2.profiles` | Local `ksef2-cli` compatible profile config helpers. |
| `ksef2.fa3` | Public FA(3) invoice builder, draft snapshots, and public FA(3) domain models used by builder workflows. |
| `ksef2.renderers` | Optional local XSLT/PDF invoice rendering helpers when installed with the `pdf` extra. |

For the exact compatibility boundary, use the public API contract page.

`PreparedBatch.to_sensitive_dict()` and `to_sensitive_json()` persist the full
prepared batch as `{"version": "1", "payload": {...}}`, with encrypted parts as
URL-safe padded Base64. Restore it with `from_sensitive_dict()` or
`from_sensitive_json()` and the saved batch session state. These readers reject
missing or unsupported versions, unversioned development exports and unknown
fields with sanitized `ValueError` messages. Store this output as
credential material; generic dumps and repr exclude keys and payload bytes.
Readers in 1.x retain support for released persistence versions. Incompatible
formats require a new version and a documented migration. Session and operation resume states now write `format_version` as the string
`"1"`; readers also accept the integer `1` written by earlier releases.
Pagination cursors retain a separate integer version field.

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

Old import paths and method names remain functional through 1.x. Removal is
a 2.0 decision (#171), including APIs deprecated in 0.19.0. This supersedes
the earlier 1.10.0 removal plan. See the
[deprecated APIs](public-api.md#deprecated-apis) table.

## Errors

Every API error reads the same way, carries the raw KSeF code and trace ID, and
says what to do next. The response body is no longer dumped into the message; it
stays on `e.response`. Branch on the exception class or `ksef_code`, never on
message text.

Narrower classes cover the common cases: `KSeFNotFoundError`, `KSeFServerError`,
`KSeFResponseValidationError`, `KSeFProfileConfigError`, `KSeFSessionFailedError`
and `KSeFTokenActivationFailedError`. Every polling timeout derives from
`KSeFPollingTimeoutError`, which exposes `timeout`. Narrower error classes retain
their earlier bases except for the 403 change documented below. See the
[error reference](errors.md).

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

`download_upo()` fetches immediately and raises `KSeFNotReadyError` if the UPO
is not ready. Call `wait(timeout=..., poll_interval=...)` first on the submission
or closed session, then fetch the UPO (#169).

KSeF Problem Details is requested by default. Use
`TransportConfig(error_format="legacy")` for the older HTTP 400/429 format;
HTTP 401, 403 and 410 always use Problem Details (#169, #175).

## Breaking in 1.0

Public model validation and invoice-builder input failures now raise
`KSeFValidationError` (or `KSeFArgumentError`) with the original Pydantic error
as `__cause__`; these classes also inherit from `ValueError` or `TypeError` for
existing handlers. HTTP 403 now raises `KSeFPermissionDeniedError` instead of
`KSeFAuthError`. Applications that caught `KSeFAuthError` for 403 responses
must add a handler for `KSeFPermissionDeniedError` (or its `KSeFApiError` base).
Workflow `*FailedError` classes, including token activation failure, now share
`KSeFOperationFailedError` while keeping their existing API and session bases.

Transport failures are SDK errors. A public method no longer lets an `httpx`
exception escape: a request that produces no usable response raises
`KSeFTransportError` (`code = "TRANSPORT_ERROR"`) with `method`, `path` and
`outcome_ambiguous`, and the original `httpx` exception as `__cause__`. It covers
every `httpx.RequestError`: connection and timeout failures, a response the HTTP
client could not decode, and an abandoned redirect chain. It does not subclass
`httpx.HTTPError`, so handlers that caught `httpx.HTTPError` must name the SDK
class; `KSeFException` already covers every SDK failure. Retries, API error
classes and `KSeFAuthError` on a 401 are unchanged. HTTP 403 now raises
`KSeFPermissionDeniedError`; see the breaking change above.
`KSeFExternalTransferError`, `KSeFBatchUploadError` and
`KSeFAuthTokenRedemptionError` now derive from `KSeFTransportError` and keep their
own codes and recovery behaviour.
See the [migration guide](migration-1-0.md#transport-failures) and the
[error reference](errors.md#transport-failure-attributes).

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

The former paths `ksef2.core`, `ksef2.domain`, `ksef2.infra` and
`ksef2.services`, including their submodules, remain as deprecated aliases.
They emit `DeprecationWarning` once per package family, naming replacements. Existing method aliases
also remain available throughout 1.x, with removal no earlier than 2.0.0.
The private-module rename does not remove these legacy imports in 1.0.

See the [migration guide](migration-1-0.md) for imports, send/wait/UPO and search
examples. Python normally hides these warnings, so enable them in your tests.

## Related pages

- [Public API contract](public-api.md): Review stable imports and internal boundaries for application code.
- [Low-level API](low-level/overview.md): Understand the supported raw endpoint surface and its schema-following model contract.
- [Operations reference](operations.md): Review retries, timeouts, rate limits, logging boundaries, and resumable references.
